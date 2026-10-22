"""
env.py: load a local `.env` file into the process environment (stdlib only).

Rules: one `KEY=VALUE` per line; blank lines and `#` comments are skipped; an `export ` prefix and
matching quotes around the value are accepted; a variable that is already set in the real environment
is never overwritten. `RAG_ENV_FILE` points at a different file; `RAG_NO_DOTENV=1` turns loading off
(tests set it so a developer's real key can never reach a test). Values are never logged.
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("rag_template.env")

_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


def parse_dotenv(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = _LINE.match(raw)
        if not m:
            continue
        key, value = m.groups()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        elif " #" in value:  # trailing comment on an unquoted value
            value = value.split(" #", 1)[0].rstrip()
        out[key] = value
    return out


def find_dotenv() -> Optional[Path]:
    """RAG_ENV_FILE if set, else the first `.env` in the working directory or above."""
    explicit = os.environ.get("RAG_ENV_FILE")
    if explicit:
        return Path(explicit)
    cwd = Path.cwd()
    for folder in (cwd, *cwd.parents):
        candidate = folder / ".env"
        if candidate.is_file():
            return candidate
    return None


def load_dotenv(path: Optional[Path] = None) -> List[str]:
    """Set every variable from the file that is not already set. Returns the names that were set."""
    if os.environ.get("RAG_NO_DOTENV", "").strip().lower() in ("1", "true", "yes"):
        return []
    path = Path(path) if path else find_dotenv()
    if path is None or not path.is_file():
        return []
    loaded = []
    for key, value in parse_dotenv(path.read_text()).items():
        if key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
    if loaded:
        logger.info("Loaded %s from %s", ", ".join(sorted(loaded)), path)
    return loaded


_OFF, _ON = ("0", "false", "no", "off"), ("1", "true", "yes", "on")


def flag(name: str, default: bool = True) -> bool:
    """A boolean environment variable: off/0/false/no -> False, on/1/true/yes -> True, unset or anything else -> `default`."""
    value = os.environ.get(name, "").strip().lower()
    return False if value in _OFF else True if value in _ON else default
