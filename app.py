"""Pathora web entrypoint.

One FastAPI app that exposes both agents under a single origin:

    /api/career/*       career_guidance_agent/backend_api.py
    /api/evaluation/*   ques_ans_agent/backend/app_eval.py

The website lives in public/ and is served as static files.

Both agents keep state between requests (JSON files in outputs/ for the
career agent, an in-memory session dict for the evaluation agent). A
serverless host gives no guarantee that two requests reach the same
machine, so this module gives every visitor a private working directory
and, when a Redis REST database is configured, saves that state there
after each request.
"""

import asyncio
import base64
import copyreg
import importlib
import importlib.util
import json
import os
import pickle
import re
import shutil
import sys
import tempfile
import threading
import traceback
import uuid
from contextvars import ContextVar
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.concurrency import run_in_threadpool

ROOT = Path(__file__).resolve().parent
CAREER_DIR = ROOT / "career_guidance_agent"
EVAL_DIR = ROOT / "ques_ans_agent"
WORK_DIR = Path(tempfile.gettempdir()) / "pathora"

SESSION_COOKIE = "pathora_session"
SESSION_ID = re.compile(r"[0-9a-f]{32}")
SESSION_TTL = 7 * 24 * 60 * 60

load_dotenv(ROOT / ".env")
WORK_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Shared state store (optional)
# ---------------------------------------------------------------------------
class RedisStore:
    """Small client for the Upstash Redis REST API."""

    def __init__(self, url: str, token: str):
        self._http = httpx.Client(
            base_url=url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )

    def _run(self, *command):
        response = self._http.post("/", json=list(command))
        response.raise_for_status()
        return response.json().get("result")

    def get(self, key: str):
        return self._run("GET", key)

    def set(self, key: str, value: str):
        self._run("SET", key, value, "EX", SESSION_TTL)


_store_url = os.getenv("KV_REST_API_URL") or os.getenv("UPSTASH_REDIS_REST_URL")
_store_token = os.getenv("KV_REST_API_TOKEN") or os.getenv("UPSTASH_REDIS_REST_TOKEN")
store = RedisStore(_store_url, _store_token) if _store_url and _store_token else None


# ---------------------------------------------------------------------------
# Load the two agents
# ---------------------------------------------------------------------------
def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sys.path[:0] = [str(CAREER_DIR), str(EVAL_DIR)]

career_api = importlib.import_module("backend_api")
# Both agents have a top-level "backend" folder, so this one is loaded by path.
eval_api = _load_module("app_eval", EVAL_DIR / "backend" / "app_eval.py")

from core.session_manager import SessionManager  # noqa: E402
from llm.llm_client import LLMClient  # noqa: E402


# ---------------------------------------------------------------------------
# Career guidance agent
# ---------------------------------------------------------------------------
# The agent reads data/ and writes outputs/ relative to the current directory.
# Each visitor gets a directory of their own and requests run one at a time,
# on a worker thread so the long pipeline calls do not block other routes.
_career_lock = threading.Lock()


def _career_workspace(session_id: str) -> Path:
    work = WORK_DIR / "career" / session_id
    (work / "outputs").mkdir(parents=True, exist_ok=True)
    data = work / "data"
    if not data.exists():
        try:
            data.symlink_to(CAREER_DIR / "data", target_is_directory=True)
        except OSError:
            shutil.copytree(CAREER_DIR / "data", data)
    return work


def _read_outputs(work: Path) -> dict:
    return {f.name: f.read_text(encoding="utf-8") for f in (work / "outputs").glob("*.json")}


def _restore_outputs(session_id: str, work: Path) -> dict:
    if store is None:
        return {}
    try:
        saved = json.loads(store.get(f"pathora:career:{session_id}") or "{}")
    except Exception:
        traceback.print_exc()
        return _read_outputs(work)
    for stale in (work / "outputs").glob("*.json"):
        stale.unlink()
    for name, text in saved.items():
        (work / "outputs" / Path(name).name).write_text(text, encoding="utf-8")
    return saved


def _save_outputs(session_id: str, work: Path, before: dict) -> None:
    if store is None:
        return
    current = _read_outputs(work)
    if current == before:
        return
    try:
        store.set(f"pathora:career:{session_id}", json.dumps(current))
    except Exception:
        traceback.print_exc()


def _run_career_request(scope, body: bytes, session_id: str) -> list:
    messages = []
    delivered = False

    async def receive():
        nonlocal delivered
        if delivered:
            return {"type": "http.disconnect"}
        delivered = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        messages.append(message)

    with _career_lock:
        work = _career_workspace(session_id)
        before = _restore_outputs(session_id, work)
        os.chdir(work)
        try:
            asyncio.run(career_api.app(scope, receive, send))
        except Exception:
            traceback.print_exc()
        finally:
            os.chdir(WORK_DIR)
        _save_outputs(session_id, work, before)

    if not messages:
        payload = json.dumps({"error": "Internal server error"}).encode()
        messages = [
            {
                "type": "http.response.start",
                "status": 500,
                "headers": [(b"content-type", b"application/json")],
            },
            {"type": "http.response.body", "body": payload},
        ]
    return messages


async def career_endpoint(scope, receive, send):
    if scope["type"] != "http":
        return
    request = Request(scope, receive)
    body = await request.body()

    session_id = request.cookies.get(SESSION_COOKIE, "")
    is_new = not SESSION_ID.fullmatch(session_id)
    if is_new:
        session_id = uuid.uuid4().hex

    messages = await run_in_threadpool(_run_career_request, scope, body, session_id)

    for message in messages:
        if is_new and message["type"] == "http.response.start":
            cookie = f"{SESSION_COOKIE}={session_id}; Path=/api/career; Max-Age={SESSION_TTL}; HttpOnly; SameSite=Lax"
            if os.getenv("VERCEL"):
                cookie += "; Secure"
            headers = list(message.get("headers", [])) + [(b"set-cookie", cookie.encode())]
            message = {**message, "headers": headers}
        await send(message)


# ---------------------------------------------------------------------------
# Adaptive evaluation agent
# ---------------------------------------------------------------------------
_save_session_file = SessionManager.save_to_json


def _save_evaluation(self, session, output_dir: str = str(WORK_DIR / "evaluations")) -> str:
    # The result file is a local record only; the report is returned in the response.
    try:
        return _save_session_file(self, session, output_dir)
    except OSError:
        return ""


SessionManager.save_to_json = _save_evaluation

# An evaluation session holds API clients, which cannot be serialised.
# They are rebuilt from provider and model name when a session is loaded.
copyreg.pickle(LLMClient, lambda client: (LLMClient, (client.provider, client.model)))

_open_sessions: ContextVar[dict] = ContextVar("open_sessions")


class StoredSessions:
    """Replacement for the in-memory SESSIONS dict, backed by the shared store."""

    def _load(self, session_id):
        opened = _open_sessions.get()
        if session_id not in opened:
            if not isinstance(session_id, str) or not SESSION_ID.fullmatch(session_id):
                return None
            raw = store.get(f"pathora:evaluation:{session_id}")
            if raw is None:
                return None
            opened[session_id] = pickle.loads(base64.b64decode(raw))
        return opened[session_id]

    def __contains__(self, session_id):
        return self._load(session_id) is not None

    def __getitem__(self, session_id):
        session = self._load(session_id)
        if session is None:
            raise KeyError(session_id)
        return session

    def __setitem__(self, session_id, session):
        _open_sessions.get()[session_id] = session


if store is not None:
    eval_api.SESSIONS = StoredSessions()

    @eval_api.app.middleware("http")
    async def keep_sessions(request: Request, call_next):
        opened = {}
        token = _open_sessions.set(opened)
        try:
            response = await call_next(request)
            for session_id, session in opened.items():
                data = base64.b64encode(pickle.dumps(session)).decode()
                await run_in_threadpool(store.set, f"pathora:evaluation:{session_id}", data)
            return response
        finally:
            _open_sessions.reset(token)


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(title="Pathora", docs_url=None, redoc_url=None, openapi_url=None)

app.mount("/api/career", career_endpoint)
app.mount("/api/evaluation", eval_api.app)


@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse("/index.html")
