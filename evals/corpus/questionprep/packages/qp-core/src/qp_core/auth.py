"""
auth.py — signed bearer tokens for QuestionPrep (no extra dependencies).

Put next to DBManager.py (qp_core/auth.py).

Tokens are standard HS256 JWTs: base64url(header).base64url(payload).signature,
so they can later be swapped for PyJWT without changing the wire format.

Secret handling:
  * QP_JWT_SECRET env var if set (recommended for any shared deployment), else
  * a random secret generated once and stored in <data_dir>/.jwt_secret (0600),
    so tokens survive restarts but the secret never lives in source control.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from typing import Optional

TOKEN_TTL_SECONDS = int(os.environ.get("QP_TOKEN_TTL_SECONDS", str(7 * 24 * 3600)))
_HEADER = {"alg": "HS256", "typ": "JWT"}


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def load_secret(data_dir: Path) -> bytes:
    env = os.environ.get("QP_JWT_SECRET", "").strip()
    if env:
        return env.encode("utf-8")

    secret_file = Path(data_dir) / ".jwt_secret"
    if secret_file.exists():
        existing = secret_file.read_text().strip()
        if existing:
            return existing.encode("utf-8")

    generated = secrets.token_urlsafe(48)
    fd = os.open(str(secret_file), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(generated)
    return generated.encode("utf-8")


def create_token(user_id: str, secret: bytes, ttl: int = TOKEN_TTL_SECONDS) -> str:
    now = int(time.time())
    payload = {"sub": user_id, "iat": now, "exp": now + ttl}
    signing_input = (
        _b64e(json.dumps(_HEADER, separators=(",", ":")).encode())
        + "."
        + _b64e(json.dumps(payload, separators=(",", ":")).encode())
    )
    sig = hmac.new(secret, signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64e(sig)}"


def verify_token(token: str, secret: bytes) -> Optional[str]:
    """Return the user_id if the token is valid and unexpired, else None."""
    try:
        head_b64, payload_b64, sig_b64 = token.split(".")
        header = json.loads(_b64d(head_b64))
        if header.get("alg") != "HS256":  # never trust the token's own alg claim
            return None

        expected = hmac.new(
            secret, f"{head_b64}.{payload_b64}".encode("ascii"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(expected, _b64d(sig_b64)):
            return None

        payload = json.loads(_b64d(payload_b64))
        if int(payload.get("exp", 0)) < time.time():
            return None
        sub = payload.get("sub")
        return sub if isinstance(sub, str) and sub else None
    except Exception:
        return None
