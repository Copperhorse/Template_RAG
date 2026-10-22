"""A tiny OpenAI-compatible server for testing against real HTTP behaviour (hangs, 5xx, garbage,
reasoning fields) without a model. In `good` mode its replies are built from the chunk text in the
prompt, so the gates see realistic, verifiable input:

  metadata   tags = identifiers found in the chunk
  questions  one question whose source_quote is a real line/sentence of the chunk
  answer     restates the quote (prose) or names an identifier from it in backticks (code)
  ask        answers from the first numbered source and cites it as [S1] (sources are labelled S1, S2, ...)
"""

import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def _kind(body: dict) -> str:
    system = body["messages"][0]["content"]
    user = body["messages"][-1]["content"]
    if "Knowledge Graph" in system:
        return "metadata"
    if system.startswith("You answer questions using ONLY the SOURCES"):
        return "ask"
    if "judge" in system.lower() or "reviewer" in system.lower():
        return "judge"
    if "qa_pairs" in user:
        return "questions"
    return "answer"


def _chunk_of(user: str) -> str:
    m = re.search(r"### (?:TEXT CHUNK|TARGET CHUNK)[^\n]*\n(.*?)\n\n### ", user, re.S)
    return m.group(1) if m else user


def _passage_of(user: str) -> str:
    m = re.search(r"### (?:KEY PASSAGE|SOURCE TEXT)\n(.*?)\n\n### QUESTION", user, re.S)
    return m.group(1) if m else user


def _identifiers(text: str):
    return [w for w in dict.fromkeys(re.findall(r"[A-Za-z_][A-Za-z0-9_]{4,}", text)) if not w.startswith("__")]


def _quote(chunk: str) -> str:
    """A verbatim line (code) or sentence (prose) of at least 40 characters."""
    for line in chunk.splitlines():
        if len(line.strip()) >= 40 and not line.strip().startswith(("#", "```")):
            return line.strip()
    for sent in re.split(r"(?<=[.!?])\s+", chunk):
        if len(sent) >= 40:
            return sent.strip()
    return chunk.strip()[:80]


class StubLLM:
    """mode: good | hang | garbage | 500 | 503 | 400 | 429 | reasoning | inline_think | truncated_think | length
    chat_modes maps a call kind to its own mode; models_mode controls GET /v1/models."""

    def __init__(self, mode="good", chat_modes=None, models_mode="ok", hang_seconds=3.0, answer_override=None):
        self.mode, self.chat_modes, self.models_mode = mode, chat_modes or {}, models_mode
        self.hang_seconds = hang_seconds
        self.answer_override = answer_override  # fixed text for "answer" calls (to test gates)
        self.requests: list[dict] = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, status, payload):
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                try:
                    self.wfile.write(data)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def do_GET(self):
                if stub.models_mode == "hang":
                    time.sleep(stub.hang_seconds)
                if stub.models_mode in ("500", "503"):
                    return self._send(int(stub.models_mode), {"error": {"message": "loading model"}})
                self._send(200, {"object": "list", "data": [{"id": "stub", "object": "model"}]})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                stub.requests.append(body)
                kind = _kind(body)
                mode = stub.chat_modes.get(kind, stub.mode)
                if mode == "hang":
                    time.sleep(stub.hang_seconds)
                    return self._send(200, stub._completion("{}"))
                if mode in ("500", "503", "400", "429"):
                    return self._send(int(mode), {"error": {"message": f"stub {mode}", "type": "stub"}})
                self._send(200, stub._respond(kind, mode, body))

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/v1"
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @staticmethod
    def _completion(content, reasoning=None, finish="stop"):
        message = {"role": "assistant", "content": content}
        if reasoning is not None:
            message["reasoning_content"] = reasoning
        return {
            "id": "x", "object": "chat.completion", "created": 0, "model": "stub",
            "choices": [{"index": 0, "message": message, "finish_reason": finish}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }

    def _good(self, kind, body):
        user = body["messages"][-1]["content"]
        if kind == "metadata":
            chunk = _chunk_of(user)
            ids = _identifiers(chunk)[:3]
            return json.dumps({
                "summary": "Handles one concern of the module. It is used by the surrounding code paths.",
                "tags": ids,
                "triplets": [{"subject": ids[0], "predicate": "uses", "object": ids[1]}] if len(ids) > 1 else [],
            })
        if kind == "questions":
            chunk = _chunk_of(user)
            q = _quote(chunk)
            ident = next(iter(_identifiers(q)), "this")
            level = re.search(r"Write up to \d+ '(\w+)'", user)
            level = level.group(1) if level else "Easy"
            return json.dumps({"qa_pairs": [{"question": f"What does {ident} do when {level.lower()} cases occur?" if level != "Easy" else f"What does {ident} do?",
                                              "source_quote": q, "difficulty": level}]})
        if kind == "answer":
            if self.answer_override is not None:
                return self.answer_override
            passage = _passage_of(user)
            if "backticks" in user:  # code rules
                ident = next(iter(_identifiers(passage)), "value")
                return f"It uses `{ident}` as written in the code."
            return passage.strip()
        if kind == "ask":
            first = re.search(r"\[S1\][^\n]*\n(.*?)(?:\n\n\[S2\]|\n\nQUESTION:)", user, re.S)
            text = first.group(1) if first else ""
            line = _quote(re.sub(r"^```\w*\n|\n```$", "", text.strip()))
            if "```" in text:  # code source: name an identifier that is on the quoted line
                ident = next(iter(_identifiers(line)), "")
                answer = f"The relevant part defines `{ident}` [S1]." if ident else "See the source [S1]."
            else:  # prose source: a faithful restatement of the quoted sentence
                answer = f"{line.rstrip('.')} [S1]."
            return json.dumps({"answer": answer, "quotes": [{"source": 1, "quote": line}]})
        if kind == "judge":
            return json.dumps({"supported": True, "answers_question": True})
        raise ValueError(kind)

    def _respond(self, kind, mode, body):
        if mode == "good":
            return self._completion(self._good(kind, body))
        good = self._good(kind, body)
        if mode == "garbage":
            return self._completion("Sorry, I can't help with that. Here is some prose without any structure.")
        if mode == "reasoning":
            return self._completion("", reasoning=good)
        if mode == "inline_think":
            return self._completion(f"<think>let me think about this carefully</think>\n{good}")
        if mode == "truncated_think":
            return self._completion("<think>still thinking and the budget ran out", finish="length")
        if mode == "length":
            return self._completion("", reasoning="thinking...", finish="length")
        raise ValueError(mode)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()

    def chat_requests(self, kind=None):
        return [r for r in self.requests if kind in (None, _kind(r))]
