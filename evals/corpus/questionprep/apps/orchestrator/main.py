"""
main.py — QuestionPrep FastAPI Backend (Orchestrator)
uv run uvicorn apps.orchestrator.main:app --reload

ds"""

import asyncio
import hashlib
import json
import logging
import mimetypes
import os
import re
import secrets
import shlex
import shutil
import subprocess
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Dict, List, Optional, Set, Tuple

from fastapi.responses import FileResponse

# Ensure .mjs files are served with correct MIME type
mimetypes.add_type("application/javascript", ".mjs")
mimetypes.add_type("application/wasm", ".wasm")


import httpx
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

# At top of main.py, with other fastapi imports:
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.responses import Response as PlainResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator

# ---------------- INTERNAL IMPORTS ----------------
from qp_core import models
from qp_core.auth import create_token, load_secret, verify_token
from qp_core.DBManager import DBManager
from qp_core.device import get_device
from qp_core.IDGenerator import IDGenerator
from qp_core.SimHashHandler import SimHashHandler
from qp_pipeline.ChunkEvaluator import ChunkEvaluator
from qp_pipeline.Embedder import VectorIndexer
from qp_pipeline.Enricher import EnrichmentManager, LLMUnavailable
from qp_pipeline.game_loop import InterviewSession
from qp_pipeline.ingester import ingest
from qp_pipeline.MarkdownChunker import ChunkConfig, MarkdownChunker
from qp_voice.speech_to_text import SpeechToText
from qp_voice.text_to_speech import TextToSpeech

# B25: Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Settings may live in a git-ignored .env at the repository root (see .env.example); real environment variables win.
from qp_core.env import load_dotenv  # noqa: E402

load_dotenv()

# ---------------- LOGGING SETUP ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator")

# ---------------- PATH SETUP ----------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]
# QP_DATA_DIR lets tests (and other deployments) keep the DB, secret and logs elsewhere.
DATA_DIR = Path(os.environ.get("QP_DATA_DIR") or PROJECT_ROOT / "data")
DB_PATH = DATA_DIR / "rag_staging.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------- LLAMA SERVER CONFIG ----------------
# Same command everywhere: `llama serve -m <model> ...`
LLAMA_CMD = shlex.split(os.environ.get("LLAMA_CMD", "llama serve"))
LLAMA_MODEL = Path(
    os.environ.get("LLAMA_MODEL", "/home/copper/models/Sharp-MiniCPM5-2B-Q8_K_M.gguf")
)
LLAMA_HOST = os.environ.get("LLAMA_HOST", "localhost")
LLAMA_PORT = int(os.environ.get("LLAMA_PORT", "8080"))
LLAMA_HEALTH_URL = f"http://{LLAMA_HOST}:{LLAMA_PORT}/v1/models"
LLAMA_LOG = DATA_DIR / "server_log.txt"
# Offload as many layers as fit on the GPU. llama.cpp ignores this on CPU-only
# builds / machines without a GPU, so it is safe to leave on.
LLAMA_NGL = os.environ.get("LLAMA_NGL", "99")
# Max thinking tokens per request (-1 = unlimited, 0 = no thinking).
LLAMA_REASONING_BUDGET = int(os.environ.get("LLAMA_REASONING_BUDGET", "4096"))
LLAMA_EXTRA_ARGS = shlex.split(os.environ.get("LLAMA_EXTRA_ARGS", ""))

HEALTH_RETRIES = 60
HEALTH_INTERVAL = 3  # seconds

# ---------------- UPLOAD LIMITS ----------------
MAX_UPLOAD_BYTES = int(float(os.environ.get("QP_MAX_UPLOAD_MB", "50")) * 1024 * 1024)
UPLOAD_CHUNK_BYTES = 1024 * 1024

# ---------------- VECTOR INDEX ----------------
# Nothing on the web path reads Chroma yet (D4); indexing is kept for planned semantic
# search / retrieval-grounded feedback. Set QP_INDEX_EMBEDDINGS=0 to skip it.
def _env_flag(name: str, default: bool = True) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw not in ("0", "false", "no", "off")


INDEX_EMBEDDINGS = _env_flag("QP_INDEX_EMBEDDINGS")

# ---------------- SESSION CONFIG ----------------
SESSION_TTL_SECONDS = 1800  # 30 minutes

# ---------------- AUTH CONFIG ----------------
JWT_SECRET = load_secret(DATA_DIR)

# ---------------- GLOBAL STATE ----------------
db = DBManager(db_path=str(DB_PATH))
active_sessions: Dict[str, InterviewSession] = {}
_session_last_active: Dict[str, float] = {}
_session_locks: Dict[str, asyncio.Lock] = {}

_stt: Optional[SpeechToText] = None
_tts: Optional[TextToSpeech] = None
_llm_process: Optional[subprocess.Popen] = None
_llama_lock = threading.Lock()  # one start/stop at a time
_enriching_files: Set[str] = set()
_ingesting: Set[Tuple[str, str]] = set()  # (user_id, sha256) uploads still being processed

_tts_lock = threading.Lock()
_stt_lock = threading.Lock()

# One queue per open /api/events stream, tagged with the user it belongs to.
_sse_clients: Dict[asyncio.Queue, str] = {}
# Single-use, short-lived tickets: EventSource cannot send an Authorization header.
SSE_TICKET_TTL_S = 30
SSE_MAX_TICKETS_PER_USER = 20
_sse_tickets: Dict[str, Tuple[str, float]] = {}  # ticket -> (user_id, expires_at)
_sse_ticket_lock = threading.Lock()
_active_enrichments: int = 0
_enrichment_lock = threading.Lock()
_main_loop: Optional[asyncio.AbstractEventLoop] = None


async def broadcast(message: str, user_id: Optional[str] = None) -> None:
    """
    Send a status line to open event streams.
    user_id=None  -> system line: every authenticated stream. It must not contain file names,
                     paths, ids or anything else that belongs to one user.
    user_id="..." -> only that user's streams (ingest / enrichment / session / voice lines).
    """
    dead = []
    for q, owner in list(_sse_clients.items()):
        if user_id is not None and owner != user_id:
            continue
        try:
            q.put_nowait(message)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _sse_clients.pop(q, None)


def emit(message: str, user_id: Optional[str] = None) -> None:
    if _main_loop and _main_loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast(message, user_id), _main_loop)
    else:
        logger.info(f"[emit-fallback] {message}")


def _issue_sse_ticket(user_id: str) -> str:
    now = time.time()
    with _sse_ticket_lock:
        for t, (_, expires) in list(_sse_tickets.items()):
            if expires <= now:
                del _sse_tickets[t]
        mine = sorted((exp, t) for t, (u, exp) in _sse_tickets.items() if u == user_id)
        for _, t in mine[: max(0, len(mine) - SSE_MAX_TICKETS_PER_USER + 1)]:
            del _sse_tickets[t]  # keep memory bounded if a client hammers the endpoint
        ticket = secrets.token_urlsafe(32)
        _sse_tickets[ticket] = (user_id, now + SSE_TICKET_TTL_S)
    return ticket


def _redeem_sse_ticket(ticket: str) -> Optional[str]:
    """Return the ticket's user and burn it (single use), or None if unknown / expired."""
    with _sse_ticket_lock:
        entry = _sse_tickets.pop(ticket, None)
    if entry is None or entry[1] <= time.time():
        return None
    return entry[0]


def _inc_enrichments() -> None:
    global _active_enrichments
    with _enrichment_lock:
        _active_enrichments += 1


def _dec_enrichments() -> None:
    global _active_enrichments
    with _enrichment_lock:
        _active_enrichments = max(0, _active_enrichments - 1)


def get_stt() -> SpeechToText:
    global _stt
    if _stt is None:
        with _stt_lock:
            if _stt is None:
                emit("[INFO] asr: ▶ Loading Qwen3-ASR-0.6B model into memory…")
                _stt = SpeechToText()
                emit("[INFO] asr: ✓ Qwen3 ASR model loaded and ready")
    return _stt


def get_tts() -> TextToSpeech:
    global _tts
    if _tts is None:
        with _tts_lock:
            if _tts is None:
                emit("[INFO] tts: ▶ Loading pocket-tts model…")
                _tts = TextToSpeech()
                emit("[INFO] tts: ✓ TextToSpeech ready")
    return _tts


# ==========================================
# B22: BACKGROUND SESSION PRUNING
# ==========================================


async def _prune_expired_sessions() -> int:
    now = time.time()
    expired = [
        sid
        for sid, last in list(_session_last_active.items())
        if now - last > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        session = active_sessions.pop(sid, None)
        if session is not None:
            await run_in_threadpool(_persist_session, session)  # keep the results
        _session_last_active.pop(sid, None)
        _session_locks.pop(sid, None)
        logger.info(f"Pruned expired session {sid[:8]}")
        if session is not None:
            await broadcast(
                f"[WARNING] sessions: ■ Session {sid[:8]} pruned (TTL expired)",
                session.user_id,
            )
    if expired:
        logger.info(f"Pruned {len(expired)} expired session(s).")
    return len(expired)


async def _session_pruner():
    while True:
        await asyncio.sleep(300)  # check every 5 minutes
        await _prune_expired_sessions()


# ==========================================
# LLAMA SERVER LIFECYCLE
# ==========================================


def _llama_is_healthy() -> bool:
    try:
        r = httpx.get(LLAMA_HEALTH_URL, timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _stop_own_llama() -> None:
    """
    Stop the llama server *this process* started, if it is alive but unhealthy.
    (The old code ran `pkill -f llama-server`, which also killed unrelated llama
    servers on the machine, e.g. benchmark runs.)
    """
    global _llm_process
    if _llm_process and _llm_process.poll() is None:
        logger.warning("Stopping our unhealthy llama server before restart.")
        emit("[WARNING] llm: ■ Stopping unhealthy llama server")
        _llm_process.terminate()
        try:
            _llm_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _llm_process.kill()
    _llm_process = None


def _build_llama_cmd() -> List[str]:
    cmd = [
        *LLAMA_CMD,
        "-m",
        str(LLAMA_MODEL),
        "--host",
        LLAMA_HOST,
        "--port",
        str(LLAMA_PORT),
        "-ngl",
        LLAMA_NGL,
        "--reasoning-budget",
        str(LLAMA_REASONING_BUDGET),
    ]
    return cmd + LLAMA_EXTRA_ARGS


def _ensure_llama_running() -> bool:
    # Two "Generate" clicks used to race here and kill each other's server.
    with _llama_lock:
        return _ensure_llama_running_locked()


def _ensure_llama_running_locked() -> bool:
    global _llm_process

    if _llama_is_healthy():
        logger.info("LLM server already running and healthy.")
        emit("[INFO] llm: ✓ LLM server already running and healthy")
        return True

    if shutil.which(LLAMA_CMD[0]) is None:
        logger.error(f"llama command not found on PATH: {LLAMA_CMD[0]}")
        emit("[ERROR] llm: ✗ llama command not found on PATH (details in the server log)")
        return False
    if not LLAMA_MODEL.exists():
        logger.error(f"LLM model not found: {LLAMA_MODEL}")
        emit("[ERROR] llm: ✗ LLM model file not found (details in the server log)")
        return False

    _stop_own_llama()

    cmd = _build_llama_cmd()
    logger.info(f"Starting llama server: {' '.join(cmd)}")
    emit("[INFO] llm: ▶ Starting llama serve…")
    with open(LLAMA_LOG, "w") as log_fh:
        _llm_process = subprocess.Popen(cmd, stdout=log_fh, stderr=log_fh)

    logger.info(f"llama server started (PID {_llm_process.pid}). Waiting for model…")
    emit("[INFO] llm: waiting for the model to load…")

    time.sleep(10)
    if _llm_process.poll() is not None:
        logger.error("llama server died immediately. Check data/server_log.txt")
        emit("[ERROR] llm: ✗ llama server exited immediately — check the server log")
        _llm_process = None
        return False

    for attempt in range(1, HEALTH_RETRIES + 1):
        time.sleep(HEALTH_INTERVAL)
        if _llama_is_healthy():
            elapsed = attempt * HEALTH_INTERVAL
            logger.info(f"LLM server ready after {elapsed}s.")
            emit(f"[INFO] llm: ✓ LLM server ready after {elapsed}s")
            return True
        if _llm_process.poll() is not None:
            logger.error("llama server died while waiting. Check data/server_log.txt")
            emit("[ERROR] llm: ✗ llama server died during startup — check the server log")
            _llm_process = None
            return False
        emit(f"[DEBUG] llm: health check {attempt}/{HEALTH_RETRIES}…")

    logger.error("Timeout waiting for LLM server to become healthy.")
    emit("[ERROR] llm: ✗ Timeout waiting for LLM server — aborting")
    _llm_process.terminate()
    _llm_process = None
    return False


def _stop_llama_server():
    global _llm_process
    if _llm_process and _llm_process.poll() is None:
        _llm_process.terminate()
        try:
            _llm_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _llm_process.kill()
        logger.info("LLM server stopped.")
        emit("[INFO] llm: ■ LLM server stopped")
    _llm_process = None


# ==========================================
# LIFESPAN
# ==========================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _main_loop
    _main_loop = asyncio.get_running_loop()
    logger.info(f"Torch models will run on: {get_device()}")
    if models.preload_enabled():
        models.preload_in_background()  # QP_PRELOAD=1: warm bge / NLI / Docling off the request path
    asyncio.create_task(_session_pruner())
    await run_in_threadpool(_retry_pending_deletions)
    await broadcast("[INFO] orchestrator: ✓ QuestionPrep API started")
    logger.info("QuestionPrep API started.")
    yield
    await broadcast("[INFO] orchestrator: ■ QuestionPrep API shutting down")
    _stop_llama_server()
    logger.info("QuestionPrep API shut down.")


# ==========================================
# APP & TEMPLATES
# ==========================================

app = FastAPI(title="QuestionPrep API", lifespan=lifespan)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _asset_version() -> str:
    """Changes whenever a static file changes; appended to script / style URLs so browsers and the
    service worker never keep serving an old app.js against newer HTML."""
    newest = max(
        (p.stat().st_mtime_ns for p in (BASE_DIR / "static").rglob("*") if p.is_file()),
        default=0,
    )
    return format(newest // 1_000_000, "x")


templates.env.globals["asset_v"] = _asset_version()


# ==========================================
# PYDANTIC MODELS
# ==========================================


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean_email(value: str) -> str:
    email = DBManager.normalize_email(value)
    if len(email) > 254 or not _EMAIL_RE.match(email):
        raise ValueError("Enter a valid email address")
    return email


class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

    _valid_email = field_validator("email")(_clean_email)


class LoginRequest(BaseModel):
    """Sign in with the account's email address and password."""

    email: str
    password: str




class EvaluateRequest(BaseModel):
    session_id: str
    user_answer: str = Field(..., max_length=5000)


class GenerateRequest(BaseModel):
    file_id: str


class StartInterviewRequest(BaseModel):
    # The user comes from the auth token. A legacy `user_id` in the body is ignored.
    file_id: Optional[str] = None


class TTSRequest(BaseModel):
    text: str = Field(..., max_length=2000)


class EmailUpdateRequest(BaseModel):
    new_email: str

    _valid_email = field_validator("new_email")(_clean_email)


# ==========================================
# AUTH DEPENDENCY
# ==========================================


def get_current_user(request: Request) -> str:
    """Resolve the caller from `Authorization: Bearer <token>`; returns user_id."""
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    challenge = {"WWW-Authenticate": "Bearer"}
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(401, "Not authenticated", headers=challenge)
    user_id = verify_token(token.strip(), JWT_SECRET)
    # Checking the DB also invalidates tokens of deleted accounts.
    if not user_id or not db.get_user_by_id(user_id):
        raise HTTPException(401, "Invalid or expired token", headers=challenge)
    return user_id


CurrentUser = Annotated[str, Depends(get_current_user)]


def _require_self(path_user_id: str, current_user: str) -> None:
    if path_user_id != current_user:
        raise HTTPException(403, "You can only modify your own account")


def _require_file_owner(user_id: str, file_id: str) -> Dict:
    """Return the file row if it belongs to the user, else 404 (no existence leak)."""
    for f in db.get_files_for_user(user_id):
        if f.get("file_id") == file_id:
            return f
    raise HTTPException(404, "File not found")


def _get_owned_session(session_id: str, user_id: str) -> InterviewSession:
    session = active_sessions.get(session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(404, "Session not found or expired")
    return session


# ==========================================
# INTERVIEW RESULT PERSISTENCE
# ==========================================

HISTORY_FORMAT_VERSION = 1


def _session_record(session: InterviewSession) -> Dict:
    """Everything worth keeping about a session, in the shape session_results stores."""
    history = session.ctx.history
    average = sum(r.similarity for r in history) / len(history) if history else 0.0
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "start_time": session.start_time,
        "end_time": datetime.now(timezone.utc).isoformat(),
        "questions_attempted": len(history),
        "average_score": average,
        "final_difficulty": session.ctx.difficulty_label,
        "history_json": json.dumps(
            {
                "v": HISTORY_FORMAT_VERSION,
                "file_id": session.file_id,
                "questions": [
                    {
                        "question_id": r.question_id,
                        "question_text": r.question_text,
                        "user_answer": r.user_text,
                        "reference_answer": r.reference_answer,
                        "similarity": r.similarity,
                        "confidence": r.confidence,
                        "feedback": r.feedback,
                        "timestamp": r.timestamp,
                    }
                    for r in history
                ],
            }
        ),
    }


def _persist_session(session: InterviewSession) -> bool:
    """Upsert the session's results. Sessions with no answers are not worth storing."""
    if not session.ctx.history:
        return False
    try:
        return db.save_session_result(**_session_record(session))
    except Exception as e:
        logger.warning(f"Could not save session {session.session_id[:8]}: {e}")
        return False


def _summary_from_record(record: Dict) -> Dict:
    """The /summary response, built from a stored (or freshly built) session record."""
    if "history" in record:  # as returned by DBManager.get_session_result
        payload = record["history"]
    else:
        payload = json.loads(record["history_json"]) if record.get("history_json") else {}
    if isinstance(payload, list):  # tolerate rows written without the v1 header
        payload = {"questions": payload}
    payload = payload or {}
    return {
        "session_id": record["session_id"],
        "start_time": record.get("start_time"),
        "end_time": record.get("end_time"),
        "questions_attempted": record.get("questions_attempted", 0),
        "average_similarity": round(record.get("average_score") or 0.0, 3),
        "final_difficulty": record.get("final_difficulty"),
        "detailed_history": payload.get("questions", []),
    }


# ==========================================
# DELETION (Chroma first, then SQLite)
# ==========================================


def _delete_file_everywhere(file_id: str, indexer=None) -> Optional[str]:
    """
    Remove a file's embeddings, then its SQLite rows. Chroma goes first so a failure leaves the
    DB rows in place (and the file recorded in `pending_deletions`) instead of orphan embeddings
    that still hold the user's text. Returns None on success, else the error text.
    """
    try:
        (indexer or VectorIndexer()).delete_embeddings_for_file(file_id)
    except Exception as e:
        attempts = db.record_pending_deletion(file_id, str(e))
        logger.warning(
            f"Chroma cleanup failed for {file_id[:8]} (attempt {attempts}); "
            f"keeping DB rows for a retry: {e}"
        )
        return str(e)
    if not db.delete_file(file_id) and db.get_file_name(file_id) is not None:
        db.record_pending_deletion(file_id, "database delete failed")
        return "database delete failed"
    return None  # delete_file also cleared any pending_deletions row


def _retry_pending_deletions() -> int:
    """Retry files whose earlier Chroma cleanup failed. Never raises. Returns how many finished."""
    try:
        pending = db.list_pending_deletions()
        if not pending:
            return 0
        indexer = VectorIndexer()
    except Exception as e:
        logger.warning(f"Could not retry pending deletions: {e}")
        return 0
    done = 0
    for row in pending:
        if _delete_file_everywhere(row["file_id"], indexer) is None:
            done += 1
            logger.info(f"Pending deletion completed for {row['file_id'][:8]}")
    return done


def _partial_delete_response(message: str, deleted: List[str], failed: List[str]):
    return JSONResponse(
        {"status": "partial", "detail": message, "deleted": deleted, "failed": failed},
        status_code=207,
    )


# ==========================================
# BACKGROUND TASKS
# ==========================================


def run_ingestion_task(temp_path: Path, user_id: str, sha256: Optional[str] = None):
    fname = temp_path.name.split("_", 1)[-1]
    emit(f"[INFO] ingest: ▶ Ingesting {fname}…", user_id)
    try:
        converter = models.get_docling_converter()  # shared; built on first upload only
        chunker = MarkdownChunker(ChunkConfig(max_chunk_tokens=1000))
        evaluator = ChunkEvaluator()
        id_gen = IDGenerator()
        simhash = SimHashHandler()

        # Duplicates are judged against this user's own files only.
        simhash.load_index_from_data(db.get_simhashes_for_user(user_id))

        result = ingest(
            temp_path,
            db,
            converter,
            chunker,
            evaluator,
            id_gen,
            simhash,
            on_duplicate="skip",
            sha256=sha256,
        )

        if result.ok:
            db.assign_file_to_user(user_id, result.file_id)
            logger.info(f"Ingested file {result.file_id} for user {user_id}")
            emit(f"[INFO] ingest: ✓ {fname} ingested — file_id {result.file_id[:8]}", user_id)
        elif result.status == "duplicate":
            original = db.get_file_name(result.duplicate_of) or result.duplicate_of[:8]
            emit(
                f"[WARNING] ingest: ■ {fname} not added — near-duplicate of "
                f"your existing file {original}",
                user_id,
            )
        else:
            emit(f"[ERROR] ingest: ✗ {fname} failed — {result.message}", user_id)

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        emit(f"[ERROR] ingest: ✗ Ingestion failed for {fname}: {e}", user_id)
    finally:
        if sha256:
            _ingesting.discard((user_id, sha256))
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def run_enrichment_task(file_id: str, user_id: str):
    _inc_enrichments()
    emit(f"[INFO] enricher: ▶ Starting enrichment for file {file_id[:8]}…", user_id)
    try:
        if not _ensure_llama_running():
            logger.error(
                f"Enrichment aborted for {file_id[:8]} — LLM server could not start. "
                "Is the USB stick mounted? Check data/server_log.txt for details."
            )
            emit(
                f"[ERROR] enricher: ✗ Enrichment aborted for {file_id[:8]} — LLM server failed to start",
                user_id,
            )
            return

        logger.info(f"Running enrichment for file {file_id[:8]}…")
        emit(f"[INFO] enricher: Running LLM enrichment for {file_id[:8]}…", user_id)
        EnrichmentManager().enrich_single_file(file_id)

        if INDEX_EMBEDDINGS:
            logger.info(f"Running vector indexing for file {file_id[:8]}…")
            emit(f"[INFO] enricher: Running vector indexing for {file_id[:8]}…", user_id)
            VectorIndexer().index_file(file_id)
        else:
            logger.info("Vector indexing disabled (QP_INDEX_EMBEDDINGS=0).")

        logger.info(f"Enrichment + indexing complete for file {file_id[:8]}.")
        emit(f"[INFO] enricher: ✓ Enrichment + indexing complete for {file_id[:8]}", user_id)

    except LLMUnavailable as e:
        # Not the file's fault: nothing was rejected and the file stays pending for a re-run.
        logger.error(f"Enrichment aborted for {file_id[:8]}: {e}")
        emit(
            f"[ERROR] enricher: ✗ LLM server unavailable — enrichment of {file_id[:8]} stopped "
            f"and the file was left unprocessed. Press Generate again once the server is back. ({e})",
            user_id,
        )
    except Exception as e:
        logger.error(f"Enrichment task failed for {file_id}: {e}")
        emit(f"[ERROR] enricher: ✗ Enrichment failed for {file_id[:8]}: {e}", user_id)
    finally:
        _dec_enrichments()
        _enriching_files.discard(file_id)


# ==========================================
# PAGE ROUTES (HTML)
# ==========================================
@app.get("/companion", response_class=HTMLResponse)
async def get_companion_page(request: Request):
    return templates.TemplateResponse("companion.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/sw.js")
async def service_worker():
    return FileResponse(
        BASE_DIR / "sw.js",
        media_type="application/javascript",
    )


@app.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})


@app.get("/profile", response_class=HTMLResponse)
async def get_profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})


@app.get("/interview", response_class=HTMLResponse)
async def get_interview_page(request: Request):
    return templates.TemplateResponse("interview.html", {"request": request})


# ==========================================
# AUTH API ROUTES
# ==========================================


@app.post("/api/auth/signup")
@limiter.limit("5/minute")
def signup(request: Request, user: SignupRequest):
    # Plain `def`: FastAPI runs it in a worker thread, so the ~150 ms PBKDF2 hash
    # no longer blocks the event loop.
    user_id = db.create_user(
        username=user.username,
        email=user.email,
        password=user.password,
    )
    if not user_id:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    return {"message": "User created successfully", "user_id": user_id}


@app.post("/api/auth/login")
@limiter.limit("10/minute")
def login(request: Request, creds: LoginRequest):
    db_user = db.get_user_by_email(creds.email)
    if not db_user or not db.verify_password(creds.email, creds.password):
        if not db_user:
            # Burn the same hashing time so response time doesn't reveal
            # whether the email is registered.
            DBManager._hash_password(creds.password)
        # One message for "no such account" and "wrong password".
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"token": create_token(db_user["user_id"], JWT_SECRET), "user": db_user}


@app.get("/session", response_class=HTMLResponse)
async def get_session_page(request: Request):
    return templates.TemplateResponse("session.html", {"request": request})


@app.get("/api/auth/profile")
def get_profile(current_user: CurrentUser):
    user = db.get_user_by_id(current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"profile": user}


@app.delete("/api/users/{user_id}")
def delete_user_account(user_id: str, current_user: CurrentUser):
    _require_self(user_id, current_user)

    # Remove the user's files (and embeddings) unless another account shares them.
    deleted: List[str] = []
    failed: List[str] = []
    try:
        indexer = VectorIndexer()
    except Exception as e:
        logger.warning(f"Chroma unavailable during account deletion: {e}")
        indexer = None
    for f in db.get_files_for_user(user_id):
        fid = f.get("file_id")
        if fid and len(db.get_users_for_file(fid)) <= 1:
            err = _delete_file_everywhere(fid, indexer)
            (failed if err else deleted).append(fid)

    if failed:
        # Keep the account so nothing is orphaned and the user can simply retry.
        return _partial_delete_response(
            "Some files could not be fully removed (vector store unavailable). "
            "Your account was NOT deleted; try again shortly.",
            deleted,
            failed,
        )

    if not db.delete_user(user_id):
        raise HTTPException(status_code=500, detail="Failed to delete account.")
    _retry_pending_deletions()
    return {"status": "success", "message": "Account deleted successfully."}


@app.put("/api/users/{user_id}/email")
def update_user_email(user_id: str, payload: EmailUpdateRequest, current_user: CurrentUser):
    _require_self(user_id, current_user)
    # db.update_user_email returns False (it doesn't raise) on a duplicate email,
    # and the old handler reported success anyway.
    if not db.update_user_email(user_id, payload.new_email):
        raise HTTPException(status_code=409, detail="That email is already in use.")
    return {"status": "success", "message": "Email updated successfully."}


# ==========================================
# PIPELINE API ROUTES
# ==========================================


@app.middleware("http")
async def reject_oversized_uploads(request: Request, call_next):
    """Refuse a declared-too-large upload before Starlette spools the body to disk."""
    if request.method == "POST" and request.url.path == "/api/files/ingest":
        declared = request.headers.get("content-length", "")
        # + 1 MiB for the multipart envelope
        if declared.isdigit() and int(declared) > MAX_UPLOAD_BYTES + 1024 * 1024:
            return JSONResponse(
                {"detail": f"File too large (limit {MAX_UPLOAD_BYTES // (1024 * 1024)} MB)."},
                status_code=413,
            )
    return await call_next(request)


@app.post("/api/files/ingest")
@limiter.limit("5/minute")
async def ingest_file(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    file: UploadFile = File(...),
):
    # .name strips any directory components the client put in the filename.
    safe_name = Path(file.filename or "upload.pdf").name

    head = await file.read(5)
    if head != b"%PDF-":
        raise HTTPException(400, "Only PDF files are accepted.")

    temp_path = DATA_DIR / f"{uuid.uuid4()}_{safe_name}"
    digest = hashlib.sha256(head)
    size = len(head)
    try:
        with open(temp_path, "wb") as f:
            f.write(head)
            while chunk := await file.read(UPLOAD_CHUNK_BYTES):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        413,
                        f"File too large (limit {MAX_UPLOAD_BYTES // (1024 * 1024)} MB).",
                    )
                digest.update(chunk)
                await run_in_threadpool(f.write, chunk)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise
    sha256 = digest.hexdigest()

    # Exact re-upload by the same user: answer immediately, before any Docling work.
    existing = await run_in_threadpool(db.get_file_by_sha256_for_user, current_user, sha256)
    if existing or (current_user, sha256) in _ingesting:
        temp_path.unlink(missing_ok=True)
        if existing:
            return JSONResponse(
                {
                    "detail": f"You already uploaded this file as “{existing['file_name']}”.",
                    "file_id": existing["file_id"],
                    "file_name": existing["file_name"],
                },
                status_code=409,
            )
        return JSONResponse(
            {"detail": "This file is already being processed."}, status_code=409
        )

    _ingesting.add((current_user, sha256))
    background_tasks.add_task(run_ingestion_task, temp_path, current_user, sha256)
    return {
        "status": "processing",
        "message": "File uploaded. Ingestion running in background.",
        "filename": safe_name,
    }


@app.post("/api/questions/generate")
@limiter.limit("10/minute")
def generate_questions(
    request: Request,
    req: GenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
):
    _require_file_owner(current_user, req.file_id)

    existing = db.get_questions_for_file(req.file_id)
    if existing:
        return {
            "message": (
                f"File {req.file_id[:8]} already has {len(existing)} question(s). "
                "Delete them first to re-enrich."
            ),
            "skipped": True,
        }
    if req.file_id in _enriching_files:
        return {
            "message": f"Enrichment for {req.file_id[:8]} is already running.",
            "skipped": True,
        }
    _enriching_files.add(req.file_id)
    background_tasks.add_task(run_enrichment_task, req.file_id, current_user)
    return {"message": f"Enrichment and indexing started for file {req.file_id}"}


@app.get("/api/files")
def list_user_files(current_user: CurrentUser):
    return {"files": db.get_files_for_user(current_user)}


@app.delete("/api/files/{file_id}")
def delete_file(file_id: str, current_user: CurrentUser):
    _require_file_owner(current_user, file_id)

    err = _delete_file_everywhere(file_id)
    if err:
        return JSONResponse(
            {
                "detail": "Could not remove this file's embeddings, so the file was kept. "
                "It will be retried automatically; you can also try again.",
                "failed": [file_id],
            },
            status_code=502,
        )
    _retry_pending_deletions()
    return {"message": "File and embeddings deleted successfully"}


@app.delete("/api/files/all/{user_id}")
def delete_all_user_files(user_id: str, current_user: CurrentUser):
    _require_self(user_id, current_user)
    try:
        indexer = VectorIndexer()
    except Exception as e:
        logger.warning(f"Chroma unavailable during bulk delete: {e}")
        indexer = None

    deleted: List[str] = []
    failed: List[str] = []
    for f in db.get_files_for_user(user_id):
        fid = f.get("file_id") or f.get("id")
        if fid:
            err = _delete_file_everywhere(fid, indexer)
            (failed if err else deleted).append(fid)

    if failed:
        return _partial_delete_response(
            f"{len(failed)} file(s) could not be fully removed and were kept; "
            "they will be retried automatically.",
            deleted,
            failed,
        )
    _retry_pending_deletions()
    return {"status": "success", "message": "All files deleted."}


@app.get("/api/files/{file_id}/audit")
def get_file_audit(file_id: str, current_user: CurrentUser):
    # Ownership check doubles as the metadata lookup (the old code called
    # get_files_for_user(None), which always returned an empty list).
    metadata = _require_file_owner(current_user, file_id)

    try:
        questions = db.get_questions_for_file(file_id) or []
    except Exception:
        questions = []

    safe_questions = [
        {
            "question_id": q.get("question_id"),
            "question_text": q.get("question_text"),
            "difficulty": q.get("difficulty"),
            "question_type": q.get("question_type"),
        }
        for q in questions
    ]

    try:
        rejected = db.get_rejections_for_file(file_id) or []
    except AttributeError:
        rejected = []

    return {
        "metadata": metadata,
        "total_questions": len(safe_questions),
        "questions": safe_questions,
        "rejected": rejected,
    }


# ==========================================
# INTERVIEW API ROUTES
# ==========================================


@app.post("/api/interview/start")
async def start_interview(req: StartInterviewRequest, current_user: CurrentUser):
    if req.file_id:
        await run_in_threadpool(_require_file_owner, current_user, req.file_id)

    session_id = str(uuid.uuid4())
    session = await run_in_threadpool(
        InterviewSession,
        session_id=session_id,
        user_id=current_user,
        db_path=str(DB_PATH),
        file_id=req.file_id,
    )
    first_question = await run_in_threadpool(session.start_interview)

    if not first_question:
        raise HTTPException(
            status_code=404, detail="No questions available. Enriched files required."
        )

    active_sessions[session_id] = session
    _session_last_active[session_id] = time.time()
    await broadcast(f"[INFO] sessions: ✓ New session {session_id[:8]} started", current_user)
    return {"session_id": session_id, "first_question": first_question}


@app.post("/api/interview/evaluate")
async def evaluate_answer(req: EvaluateRequest, current_user: CurrentUser):
    session = _get_owned_session(req.session_id, current_user)
    _session_last_active[req.session_id] = time.time()

    # Scoring runs the bi-encoder + NLI cross-encoder (blocking, GPU/CPU heavy).
    # Calling it directly inside `async def` froze the whole server — SSE, status
    # polling and every other request — until it finished. Run it in a worker
    # thread, one evaluation at a time per session.
    lock = _session_locks.setdefault(req.session_id, asyncio.Lock())
    async with lock:
        result = await run_in_threadpool(session.evaluate_turn, req.user_answer)
        # Saved after every answer (not only at the end) so results survive a restart and
        # the "End session" button, which navigates away without calling DELETE.
        await run_in_threadpool(_persist_session, session)
    _session_last_active[req.session_id] = time.time()
    return result


@app.get("/api/interview/{session_id}/status")
async def get_session_status(session_id: str, current_user: CurrentUser):
    session = _get_owned_session(session_id, current_user)
    current_q = session.ctx.current_question
    return {
        "alive": True,
        "state": session.state.name,
        "current_question": current_q.text if current_q else None,
        "questions_answered": len(session.ctx.history),
    }


@app.get("/api/interview/history")
async def get_interview_history(current_user: CurrentUser):
    """The caller's past sessions, newest first."""
    rows = await run_in_threadpool(db.list_session_summaries, current_user)
    return {
        "sessions": [
            {
                "session_id": r["session_id"],
                "start_time": r["start_time"],
                "end_time": r["end_time"],
                "questions_attempted": r["questions_attempted"],
                "average_similarity": round(r["average_score"] or 0.0, 3),
                "final_difficulty": r["final_difficulty"],
            }
            for r in rows
        ]
    }


@app.get("/api/interview/{session_id}/summary")
async def get_summary(session_id: str, current_user: CurrentUser):
    session = active_sessions.get(session_id)
    if session is not None:
        session = _get_owned_session(session_id, current_user)
        return _summary_from_record(_session_record(session))

    # Not in memory (expired, ended, or the server restarted): use the stored copy.
    stored = await run_in_threadpool(db.get_session_result, session_id)
    if not stored or stored.get("user_id") != current_user:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    return _summary_from_record(stored)


@app.delete("/api/interview/{session_id}")
async def end_session(session_id: str, current_user: CurrentUser):
    global _stt
    session = active_sessions.get(session_id)
    if session is not None and session.user_id != current_user:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    if session is not None:
        await run_in_threadpool(_persist_session, session)

    active_sessions.pop(session_id, None)
    _session_last_active.pop(session_id, None)
    _session_locks.pop(session_id, None)

    if not active_sessions and _stt is not None:
        with _stt_lock:
            if not active_sessions and _stt is not None:
                _stt = None
                logger.info("Qwen3 ASR model unloaded — no active sessions.")
                await broadcast(
                    "[INFO] asr: ■ Qwen3 ASR model unloaded — no active sessions remain"
                )

    if session is not None:
        await broadcast(f"[INFO] sessions: ■ Session {session_id[:8]} ended", current_user)
    return {"message": "Session ended"}


# ==========================================
# VOICE API ROUTES
# ==========================================


@app.post("/api/analyze-speech")
async def analyze_speech(current_user: CurrentUser, audio: UploadFile = File(...)):
    try:
        audio_bytes = await audio.read()
        loop = asyncio.get_running_loop()
        stt = await loop.run_in_executor(None, get_stt)

        result = await loop.run_in_executor(
            None, stt.transcribe_and_analyze, audio_bytes
        )
        words = len((result.get("transcript") or "").split())
        await broadcast(
            f"[INFO] asr: ✓ Transcribed {words} words — "
            f"stutter={'yes' if result.get('stutter_flag') else 'no'}  "
            f"rate={result.get('disfluency_rate', 0):.2%}",
            current_user,
        )
        return result

    except FileNotFoundError as e:
        msg = "ffmpeg not found. Install it: sudo apt install ffmpeg (Linux) or brew install ffmpeg (Mac)."
        logger.error(msg)
        raise HTTPException(status_code=500, detail=msg) from e
    except RuntimeError as e:
        if "ffmpeg" in str(e).lower():
            msg = f"ffmpeg decode failed: {e}. Check the audio format sent by the browser."
        else:
            msg = str(e)
        logger.exception(f"STT runtime error: {e}")
        raise HTTPException(status_code=500, detail=msg) from e
    except Exception as e:
        logger.exception(f"Speech analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/tts")
async def text_to_speech(req: TTSRequest, current_user: CurrentUser):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    try:
        loop = asyncio.get_running_loop()
        tts = await loop.run_in_executor(None, get_tts)
        wav_bytes = await loop.run_in_executor(None, tts.generate_wav_bytes, req.text)

        audio_data = wav_bytes.read()
        await broadcast(
            f"[INFO] tts: ✓ Generated {len(audio_data) // 1024} KB of audio", current_user
        )
        return PlainResponse(content=audio_data, media_type="audio/wav")
    except Exception as e:
        logger.exception(f"TTS failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ==========================================
# SSE STATUS ENDPOINTS
# ==========================================


@app.post("/api/events/ticket")
@limiter.limit("60/minute")
async def create_event_ticket(request: Request, current_user: CurrentUser):
    """A one-shot ticket for EventSource, which cannot send an Authorization header."""
    return {"ticket": _issue_sse_ticket(current_user), "expires_in": SSE_TICKET_TTL_S}


@app.get("/api/events")
async def sse_events(request: Request, ticket: Optional[str] = None):
    """Status stream. Needs a ticket from POST /api/events/ticket (or a normal bearer token)."""
    user_id = _redeem_sse_ticket(ticket) if ticket else None
    if user_id and not await run_in_threadpool(db.get_user_by_id, user_id):
        user_id = None
    if not user_id:
        user_id = get_current_user(request)  # 401 for anonymous callers

    queue: asyncio.Queue = asyncio.Queue(maxsize=200)
    _sse_clients[queue] = user_id

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {msg}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            _sse_clients.pop(queue, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/status")
async def get_system_status(request: Request):
    """Anonymous callers get only whether the LLM server is up; signed-in users get the rest."""
    body = {"llm_server_running": await run_in_threadpool(_llama_is_healthy)}
    try:
        get_current_user(request)
    except HTTPException:
        return body
    body.update(
        {
            "active_enrichments": _active_enrichments,
            "sessions_with_asr": 1 if _stt is not None else 0,
            "active_sessions": len(active_sessions),
            "models": {"device": get_device(), "loaded": models.loaded_models()},
        }
    )
    return body


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "apps.orchestrator.main:app",
        host=os.environ.get("QP_HOST", "127.0.0.1"),
        port=int(os.environ.get("QP_PORT", "8000")),
        reload=True,
    )
