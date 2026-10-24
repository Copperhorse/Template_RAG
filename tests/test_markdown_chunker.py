import pytest
import textwrap

from rag_template.chunking import ChunkConfig, MarkdownChunker, chunk_markdown
from rag_template.tokens import count_tokens

DOC = textwrap.dedent("""
    # Guide

    Intro paragraph that explains what the guide covers and why it exists in the first place.

    ## Setup

    Install the package, then run the tool.

    ```python
    # not a heading
    def hello():
        return 1
    ```

    ### Config

    Set the options in the file.

    $$E = mc^2$$

    | name | value |
    |------|-------|
    | a    | 1     |
    | b    | 2     |
""").lstrip()


def test_header_hierarchy_and_protected_blocks():
    cs = chunk_markdown(DOC, max_chunk_tokens=300)
    by_type = {}
    for c in cs:
        by_type.setdefault(c["metadata"]["content_type"], []).append(c)
    code = by_type["code"][0]
    assert code["content"].startswith("```python") and "# not a heading" in code["content"]
    assert code["metadata"]["section_header"] == "Setup"  # the # inside the fence is not a heading
    assert by_type["math"][0]["content"] == "$$E = mc^2$$"
    assert by_type["table"][0]["content"].startswith("| name")
    config = next(c for c in cs if c["metadata"]["section_header"] == "Config")
    assert config["metadata"]["parent_section"] == "Setup"
    assert config["metadata"]["top_header"] == "Guide"
    assert config["metadata"]["breadcrumb"] == "Guide > Setup > Config"


def test_prose_respects_the_token_budget():
    """Regression: the original passed chunk_size = max_tokens * 4 to a token-length splitter, so
    prose chunks could be four times over budget."""
    para = " ".join(f"Sentence number {i} says something specific about topic {i}." for i in range(300))
    cs = chunk_markdown(f"# T\n\n{para}\n", max_chunk_tokens=100)
    assert len(cs) > 5
    assert max(c["estimated_tokens"] for c in cs) <= 100
    assert all(c["content"].rstrip().endswith(".") for c in cs)  # sentence punctuation survives the split


def test_large_table_is_split_by_rows_with_the_header_repeated():
    rows = "\n".join(f"| item_{i} | {i * 7} | description of item {i} |" for i in range(120))
    table = f"| name | qty | note |\n|------|-----|------|\n{rows}"
    cs = chunk_markdown(f"# Data\n\n{table}\n", max_chunk_tokens=120)
    tables = [c for c in cs if c["metadata"]["content_type"] == "table"]
    assert len(tables) > 3
    assert all(c["content"].startswith("| name | qty | note |\n|------|-----|------|") for c in tables)
    assert all(c["estimated_tokens"] <= 140 for c in tables)
    assert sum(c["content"].count("| item_") for c in tables) == 120


def test_oversized_python_fence_is_split_with_the_ast_not_mid_function():
    funcs = "\n\n".join(f"def func_{i}(x):\n    return x + {i}  # adds {i}\n" for i in range(40))
    cs = chunk_markdown(f"# API\n\n```python\n{funcs}\n```\n", max_chunk_tokens=120)
    code = [c for c in cs if c["metadata"]["content_type"] == "code"]
    assert len(code) > 2
    for c in code:
        assert c["content"].startswith("```python\n") and c["content"].rstrip().endswith("```")
        assert c["content"].count("def func_") == c["content"].count("return x +")  # no function cut in half
        assert c["metadata"]["language"] == "python"
    assert sum(c["content"].count("def func_") for c in code) == 40


def test_other_languages_in_a_fence_are_cut_at_blank_lines_and_refenced():
    block = "\n\n".join(f"echo step_{i}\nsleep {i}" for i in range(80))
    cs = chunk_markdown(f"# Ops\n\n```bash\n{block}\n```\n", max_chunk_tokens=80)
    code = [c for c in cs if c["metadata"]["content_type"] == "code"]
    assert len(code) > 2 and all(c["content"].startswith("```bash") and c["content"].endswith("```") for c in code)


def test_short_adjacent_prose_in_one_section_is_merged_and_ids_are_linked():
    cs = chunk_markdown(
        "# T\n\nFirst short paragraph here.\n\nSecond short paragraph here.\n\n## U\n\nOther section text.\n"
    )
    assert len(cs) == 2 and "First" in cs[0]["content"] and "Second" in cs[0]["content"]
    assert cs[0]["next_chunk_id"] == cs[1]["chunk_id"] and cs[1]["prev_chunk_id"] == cs[0]["chunk_id"]
    off = chunk_markdown(
        "# T\n\nFirst short paragraph here.\n\nSecond short paragraph here.\n", merge_short_chunks=False
    )
    assert len(off) == 1  # one paragraph block per split; merging only matters across splitter pieces


def test_text_without_headings_gets_a_root_header_and_empty_input_is_empty():
    cs = chunk_markdown("Just some text without any heading at all, long enough to matter.")
    assert cs[0]["metadata"]["section_header"] == "Root"
    assert MarkdownChunker(ChunkConfig()).process("") == []


def test_a_pathological_table_does_not_hang():
    big = "\n".join("| " + " | ".join("x" * 5 for _ in range(10)) + " |" for _ in range(3000))
    assert count_tokens(big) > 1000
    assert chunk_markdown(big, max_chunk_tokens=200)


def test_text_with_no_separators_is_still_bounded():
    """A base64 blob or minified line has no whitespace to split on: fall back to characters."""
    cs = chunk_markdown(f"# T\n\n{'A1b2' * 3000}\n", max_chunk_tokens=100)
    assert len(cs) > 3 and max(c["estimated_tokens"] for c in cs) <= 130
    assert sum(len(c["content"]) for c in cs) == 12000


# ---- a table's caption travels with the table ---------------------------------------------------------------------

TABLE = "|Method|Acc|\n|---|---|\n|A|55.0|\n|B|87.4|"


def _chunks(md):
    from rag_template.chunking import chunk_file

    return chunk_file("doc.md", md)


def test_caption_above_a_table_is_attached_to_it():
    md = (
        "# Results\n\nSome intro text about the experiments that is long enough to be a paragraph of its own.\n\n_Table 1._ Ablation of the model on Sudoku comparing accuracy.\n\n"
        + TABLE
        + "\n\nAfter the table."
    )
    tables = [c for c in _chunks(md) if c["metadata"]["content_type"] == "table"]
    assert (
        len(tables) == 1 and tables[0]["content"].startswith("_Table 1._ Ablation") and "87.4" in tables[0]["content"]
    )
    assert not any(
        "Ablation of the model" in c["content"] for c in _chunks(md) if c["metadata"]["content_type"] != "table"
    )


def test_caption_below_a_table_is_attached_when_there_is_none_above():
    md = "# Results\n\nIntro paragraph.\n\n" + TABLE + "\n\nTable 2: Accuracy by method.\n\nNext paragraph."
    t = next(c for c in _chunks(md) if c["metadata"]["content_type"] == "table")
    assert t["content"].endswith("Table 2: Accuracy by method.") and "Next paragraph" not in t["content"]


def test_a_paragraph_that_only_mentions_a_table_is_not_a_caption():
    md = "# Results\n\nResults are shown in Table 3, which compares the methods.\n\n" + TABLE
    t = next(c for c in _chunks(md) if c["metadata"]["content_type"] == "table")
    assert "Results are shown" not in t["content"]


def test_every_part_of_an_oversize_table_repeats_the_header_and_carries_the_caption():
    rows = "\n".join(f"|row {i}|{i * 1000 + 7}|" for i in range(400))
    md = "# R\n\n_Table 9._ A very long table of values.\n\n|Name|Value|\n|---|---|\n" + rows
    chunks = _chunks(md)
    tables = [c for c in chunks if c["metadata"]["content_type"] == "table"]
    assert len(tables) > 1
    assert all(
        c["content"].startswith("_Table 9._ A very long table of values.") and "|Name|Value|" in c["content"]
        for c in tables
    )
    assert not any("A very long table" in c["content"] for c in chunks if c["metadata"]["content_type"] != "table")
    assert sum(c["content"].count("|row ") for c in tables) == 400  # no row lost or duplicated


def test_a_continuation_row_inherits_the_label_of_the_row_it_continues():
    from rag_template.tables import inherit_row_labels as _inherit_row_labels

    rows = [
        "| Qwen3-30B-Thinking | 66.1 | 41.5 |",
        "| + SSD | 68.2 | 46.7 |",
        "| Llama-3.1-8B | 12.7 | 0.0 |",
        "| w/ ACT | 86.1 | 5 |",
        "| + SSD (ours) | 1 | 2 |",
    ]
    out = _inherit_row_labels(rows)
    assert out[0] == rows[0] and out[2] == rows[2]
    assert out[1] == "| Qwen3-30B-Thinking / + SSD | 68.2 | 46.7 |"
    assert (
        out[3] == "| Llama-3.1-8B / w/ ACT | 86.1 | 5 |" and out[4] == "| Llama-3.1-8B / + SSD (ours) | 1 | 2 |"
    )  # the parent stays the last ordinary label


def test_split_table_rows_name_their_parent_in_the_chunk_that_holds_them():
    wide = " | ".join(f"Column heading number {i} with a long descriptive name here" for i in range(40))
    md = (
        f"# R\n\n_Table 2._ Per-model results.\n\n| Model | {wide} |\n|---|{'---|' * 40}\n| Qwen3-30B-Thinking | "
        + " | ".join(["1.0"] * 40)
        + " |\n| + SSD | "
        + " | ".join(["2.0"] * 40)
        + " |\n"
    )
    tables = [c for c in _chunks(md) if c["metadata"]["content_type"] == "table"]
    holder = next(c for c in tables if "2.0" in c["content"])
    assert "Qwen3-30B-Thinking / + SSD" in holder["content"] and holder["content"].startswith(
        "_Table 2._ Per-model results."
    )


def test_ordinary_row_labels_are_never_rewritten():
    from rag_template.tables import inherit_row_labels as _inherit_row_labels

    rows = ["| alpha | 1 |", "| beta | 2 |", "| gamma | 3 |", "|  | 4 |"]
    assert _inherit_row_labels(rows) == rows


@pytest.mark.parametrize(
    "line,is_caption",
    [
        ("Table 3 Generation-time and evaluation-time decoding settings.", True),
        ("Table 1: Ablation of the model.", True),
        ("_Table 2._ Per-model results.", True),
        ("**Table IV.** Results", True),
        ("Table 3 shows that the method works.", False),
        ("Table 3, which compares the methods, is below.", False),
        ("Table of contents", False),
    ],
)
def test_what_counts_as_a_table_caption(line, is_caption):
    from rag_template.chunking.markdown import _TABLE_CAPTION

    assert bool(_TABLE_CAPTION.match(line)) is is_caption


def test_a_caption_between_two_tables_goes_to_the_second_one():
    t1 = "| a | b |\n|---|---|\n| 1 | 2 |"
    t2 = "| c | d |\n|---|---|\n| 3 | 4 |"
    chunks = chunk_markdown(
        f"# S\n\n{t1}\n\nTable 2. Second thing\n\n{t2}\n", min_chunk_tokens=1, merge_short_chunks=False
    )
    tables = [c["content"] for c in chunks if c["metadata"]["content_type"] == "table"]
    assert len(tables) == 2 and "Second thing" not in tables[0] and "Second thing" in tables[1]
