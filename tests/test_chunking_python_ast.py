import ast
import textwrap

from rag_template.chunking import ChunkConfig, PythonASTChunker, chunk_file
from rag_template.tokens import count_tokens
from conftest import SAMPLE_PY


def chunks_of(src, **cfg):
    return PythonASTChunker(ChunkConfig(**cfg)).process(src, source="m.py")


def by_name(chunks):
    out = {}
    for c in chunks:
        for s in c["metadata"]["symbols"]:
            out[s] = c
    return out


def test_every_definition_becomes_a_chunk_with_its_metadata():
    cs = chunks_of(SAMPLE_PY, max_chunk_tokens=400, min_chunk_tokens=10)
    names = by_name(cs)
    retry = names["retry"]
    assert retry["metadata"]["kind"] == "function"
    assert retry["metadata"]["signature"] == "def retry(fn, attempts=DEFAULT_ATTEMPTS, delay=0.5)"
    assert retry["metadata"]["docstring"].startswith("Call fn until it succeeds")
    assert "raise RuntimeError" in retry["content"]
    assert retry["metadata"]["top_header"] == "m.py"
    assert retry["metadata"]["breadcrumb"] == "m.py > retry"
    assert retry["metadata"]["content_type"] == "code" and retry["metadata"]["language"] == "python"
    assert names["Cache"]["metadata"]["kind"] == "class"  # small enough to stay whole
    assert "def put" in names["Cache"]["content"]


def test_nothing_is_lost_or_duplicated():
    """Every non-blank source line lands in exactly one chunk."""
    for budget in (400, 80, 40):
        cs = chunks_of(SAMPLE_PY, max_chunk_tokens=budget, min_chunk_tokens=10)
        body = "\n".join(c["content"] for c in cs)
        for line in (ln.strip() for ln in SAMPLE_PY.splitlines() if ln.strip()):
            assert line in body, f"lost at budget {budget}: {line!r}"
        spans = sorted((c["metadata"]["start_line"], c["metadata"]["end_line"]) for c in cs if "part" not in c["metadata"])
        for (_, e1), (s2, _) in zip(spans, spans[1:]):
            assert s2 > e1, f"chunks overlap at budget {budget}: ends {e1}, next starts {s2}"
        assert all(a <= b for a, b in spans)


def test_oversized_class_is_cut_into_header_plus_methods():
    cs = chunks_of(SAMPLE_PY, max_chunk_tokens=70, min_chunk_tokens=5)
    names = by_name(cs)
    assert "Cache.get" in names and "Cache.put" in names and "Cache.__init__" in names
    assert names["Cache.get"]["metadata"]["kind"] == "method"
    assert names["Cache.get"]["metadata"]["parent_section"] == "Cache"
    assert names["Cache.get"]["metadata"]["qualname"] == "Cache.get"
    assert names["Cache.get"]["metadata"]["breadcrumb"] == "m.py > Cache.get"
    head = [c for c in cs if c["metadata"]["kind"] == "class" and c["metadata"]["qualname"] == "Cache"]
    assert head and "A tiny time-to-live cache" in head[0]["content"]
    assert "def get" not in head[0]["content"]
    assert max(c["estimated_tokens"] for c in cs) <= 70


def test_oversized_function_is_cut_between_statements_and_labelled():
    body = "\n".join(f"    value_{i} = compute_something({i}) + other_function_call({i}, {i * 2})" for i in range(60))
    src = f'def big(x):\n    """Doc."""\n{body}\n    return value_59\n'
    cs = chunks_of(src, max_chunk_tokens=150, min_chunk_tokens=5)
    assert len(cs) > 3
    assert all(c["estimated_tokens"] <= 150 for c in cs)
    assert cs[0]["content"].startswith("def big(x):")
    assert all(c["metadata"]["qualname"] == "big" for c in cs)
    assert [c["metadata"]["part"] for c in cs][0] == f"1/{len(cs)}"
    for c in cs[1:]:
        assert c["content"].startswith("# ... continued: def big(x)")
    joined = "\n".join(c["content"] for c in cs)
    assert "value_0 =" in joined and "return value_59" in joined
    # no statement is cut in half: every part compiles once re-indented under the def
    for c in cs:
        text = "\n".join(ln for ln in c["content"].splitlines() if not ln.startswith(("#", "def ", '    """')))
        ast.parse(textwrap.dedent(text) or "pass")


def test_decorators_and_leading_comments_travel_with_the_function():
    src = textwrap.dedent('''
        import functools

        # Cache results for the lifetime of the process.
        # Keyed on the arguments.
        @functools.lru_cache(maxsize=None)
        def slow(n):
            return sum(range(n))


        def other():
            return 1
    ''').lstrip()
    cs = chunks_of(src, max_chunk_tokens=400, min_chunk_tokens=1)
    slow = by_name(cs)["slow"]
    assert slow["content"].startswith("# Cache results")
    assert "@functools.lru_cache" in slow["content"]
    assert slow["metadata"]["decorators"] == ["functools.lru_cache(maxsize=None)"]
    assert "import functools" not in slow["content"]


def test_tiny_neighbours_are_merged_but_large_ones_are_not():
    src = "def a():\n    return 1\n\n\ndef b():\n    return 2\n\n\ndef c():\n    return 3\n"
    merged = chunks_of(src, max_chunk_tokens=400, min_chunk_tokens=50)
    assert len(merged) == 1 and merged[0]["metadata"]["symbols"] == ["a", "b", "c"]
    assert merged[0]["metadata"]["section_header"] == "a, b, c"
    assert merged[0]["metadata"]["signature"] == ""  # not one function any more
    separate = chunks_of(src, max_chunk_tokens=400, min_chunk_tokens=1)
    assert [c["metadata"]["qualname"] for c in separate] == ["a", "b", "c"]
    off = chunks_of(src, max_chunk_tokens=400, min_chunk_tokens=50, merge_short_chunks=False)
    assert len(off) == 3


def test_async_nested_and_module_level_code():
    src = textwrap.dedent('''
        """Module doc."""
        import asyncio

        async def fetch(url, *, timeout=5) -> bytes:
            async def inner():
                return b""
            return await inner()

        class Outer:
            class Inner:
                def method(self):
                    return 1

        if __name__ == "__main__":
            asyncio.run(fetch("x"))
    ''').lstrip()
    cs = chunks_of(src, max_chunk_tokens=400, min_chunk_tokens=1)
    names = by_name(cs)
    assert names["fetch"]["metadata"]["signature"] == "async def fetch(url, *, timeout=5) -> bytes"
    assert "async def inner" in names["fetch"]["content"]  # nested defs stay with their parent
    assert "class Inner" in names["Outer"]["content"]
    module = [c for c in cs if c["metadata"]["kind"] == "module"]
    assert module[0]["metadata"]["docstring"] == "Module doc."
    assert any('__name__ == "__main__"' in c["content"] for c in module)


def test_syntax_errors_fall_back_to_line_chunks_instead_of_failing():
    cs = chunks_of("def broken(:\n    pass\n\ndef fine():\n    return 1\n")
    assert cs and all("parse_error" in c["metadata"] for c in cs)
    assert "SyntaxError" in cs[0]["metadata"]["parse_error"]
    assert "def fine" in "".join(c["content"] for c in cs)


def test_empty_source_yields_no_chunks_and_ids_are_linked():
    assert chunks_of("   \n\n") == []
    cs = chunks_of(SAMPLE_PY, max_chunk_tokens=70, min_chunk_tokens=5)
    assert cs[0]["prev_chunk_id"] is None and cs[-1]["next_chunk_id"] is None
    for a, b in zip(cs, cs[1:]):
        assert a["next_chunk_id"] == b["chunk_id"] and b["prev_chunk_id"] == a["chunk_id"]
    assert [c["chunk_index"] for c in cs] == list(range(len(cs)))


def test_one_giant_constant_is_still_bounded():
    src = "TABLE = {\n" + "\n".join(f"    'key_{i}': {i}," for i in range(400)) + "\n}\n"
    cs = chunks_of(src, max_chunk_tokens=100)
    assert len(cs) > 1 and all(count_tokens(c["content"]) <= 120 for c in cs)


def test_router_sends_python_to_ast_and_other_languages_to_the_line_chunker():
    py = chunk_file("pkg/a.py", SAMPLE_PY, ChunkConfig(max_chunk_tokens=400, min_chunk_tokens=1))
    assert py[0]["metadata"]["language"] == "python" and "qualname" in py[0]["metadata"]
    ts = chunk_file("web/app.ts", "export function greet(name: string) {\n  return `hi ${name}`;\n}\n\nexport class Box {\n  size = 1;\n}\n",
                    ChunkConfig(max_chunk_tokens=400, min_chunk_tokens=1, merge_short_chunks=False), source="web/app.ts")
    assert [c["metadata"]["symbols"] for c in ts] == [["greet"], ["Box"]]
    assert ts[0]["metadata"]["language"] == "typescript" and ts[0]["metadata"]["kind"] == "block"
    md = chunk_file("README.md", "# T\n\nSome prose that is long enough to be a chunk of its own here.\n")
    assert md[0]["metadata"]["content_type"] == "prose"


def test_a_small_function_header_is_never_left_as_an_orphan_chunk():
    """Regression (found by the corpus eval): a long function whose first statement is huge used to yield a
    chunk holding only `def main():` and a comment."""
    body = "\n".join(f"        step_{i} = compute_something({i}) + other_function_call({i}, {i * 2})" for i in range(80))
    src = f"def main():\n    # terminal setup\n    for item in items:\n{body}\n    return 1\n"
    cs = chunks_of(src, max_chunk_tokens=120, min_chunk_tokens=40)
    assert len(cs) > 2
    assert not any(c["content"].strip().splitlines()[-1].strip() in ("def main():", "# terminal setup") for c in cs)  # no chunk ends at the header
    assert cs[0]["content"].startswith("def main():") and "for item in items" in cs[0]["content"] and "step_0 =" in cs[0]["content"]
    assert all(c["estimated_tokens"] <= 120 for c in cs)
