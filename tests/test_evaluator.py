import pytest

from rag_template.chunking import ChunkConfig, chunk_file
from rag_template.evaluator import ChunkEvaluator
from conftest import SAMPLE_PY

ev = ChunkEvaluator()
PROSE = "Gradient descent updates parameters in the direction of the negative gradient. The learning rate controls the step size, and too large a value makes training diverge."


def judge(text, **meta):
    return ev.evaluate_chunk(text, meta)


def test_good_prose_is_accepted_with_a_score():
    r = judge(PROSE, section_header="Optimization", content_type="prose")
    assert r["should_use"] and r["content_type"] == "main_content" and r["quality_score"] >= 60


@pytest.mark.parametrize(
    "text, meta, reason",
    [
        ("tiny", {}, "Too short"),
        (PROSE, {"section_header": "References"}, "Header filter"),
        (PROSE, {"section_header": "Table of Contents"}, "Header filter"),
        ("[removed: corrupted latex content] \\frac{a}{b} more text follows here to be long.", {}, "Forbidden prefix"),
        ("See https://example.com/some/page for the full details of this thing.", {}, "Citation/Link"),
        ("Copyright 2024 Example Corp. All rights reserved. Do not copy this document at all.", {}, "Metadata keyword"),
        (
            "1 Introduction ........ 3\n2 Methods ........ 9\n3 Results ........ 14\n4 Discussion ........ 20\n5 Notes ........ 25",
            {},
            "Table of Contents",
        ),
        ("12 34 56 78 90 12 34 56 78 90 12 34 56 78 90 12 34 56", {}, "Low alpha"),
    ],
)
def test_prose_gates_reject(text, meta, reason):
    r = judge(text, **meta)
    assert not r["should_use"] and reason in r["reason"]


def test_real_data_table_is_kept_but_a_toc_table_is_not():
    rows = "\n".join(f"| {i} | {i * 3} | {i * 5} |" for i in range(12))
    table = f"| a | b | c |\n|---|---|---|\n{rows}"
    assert judge(table, section_header="Results")["content_type"] == "table"
    assert not judge(table, section_header="Table of Contents")["should_use"]


def test_prose_that_contains_code_is_classified_as_code():
    r = judge(
        "Use it like this:\n\ndef main():\n    run()\n\nThen call main from your script when needed.",
        section_header="Usage",
    )
    assert r["should_use"] and r["content_type"] == "code"
    # the old pattern fired on any "import <word>" in prose
    assert (
        judge(
            "We decided to import data from the legacy system, which took a long time overall.",
            section_header="Migration",
        )["content_type"]
        == "main_content"
    )


# ----------------------------------------------------------------------------------- code


def code_meta(**kw):
    return {"content_type": "code", "language": "python", "kind": "function", **kw}


def test_code_chunks_skip_the_heading_filters():
    """A function called get_index (or a class called Author) is code, not back matter."""
    fn = "def get_index(items, key):\n    for i, item in enumerate(items):\n        if item == key:\n            return i\n    return -1"
    r = judge(fn, **code_meta(section_header="get_index", symbol="get_index", docstring=""))
    assert r["should_use"] and r["content_type"] == "code"
    r2 = judge(fn, **code_meta(section_header="references", symbol="x"))
    assert r2["should_use"]


@pytest.mark.parametrize(
    "text, reason",
    [
        ("# Copyright 2024 Example Corp\n# Licensed under the Apache License\n# All rights reserved", "Comment-only"),
        ("import os\nimport sys\nfrom pathlib import Path\n__all__ = ['x']", "Imports only"),
        ("# This file is auto-generated. DO NOT EDIT.\nVALUE = compute_the_value_from_inputs(1, 2, 3)", "Generated"),
        ("x=1", "Too short"),
    ],
)
def test_code_gates_reject(text, reason):
    r = judge(text, **code_meta(kind="module", section_header="<module>"))
    assert not r["should_use"] and reason in r["reason"]


def test_a_documented_function_outscores_a_bare_one():
    body = "def f(a, b):\n    total = a + b\n    return total * 2  # double the sum before returning it\n" * 3
    bare = judge(body, **code_meta(symbol="f"))
    doc = judge(body, **code_meta(symbol="f", docstring="Add and double."))
    assert doc["quality_score"] > bare["quality_score"] >= 55


def test_licence_header_module_chunk_is_dropped_but_the_functions_below_it_are_kept():
    src = "# Copyright 2024 Example. All rights reserved.\n# Licensed under MIT.\n\n\n" + SAMPLE_PY
    stats = ev.evaluate_chunks(
        chunk_file("a.py", src, ChunkConfig(max_chunk_tokens=400, min_chunk_tokens=1), source="a.py")
    )
    kept = {s for c in stats["evaluated_chunks"] if c["evaluation"]["should_use"] for s in c["metadata"]["symbols"]}
    assert {"retry", "Cache"} <= kept


def test_fenced_code_blocks_from_markdown_are_judged_as_code():
    r = judge(
        "```bash\npip install rag-template && rag ingest ./docs\n```",
        content_type="code",
        language="bash",
        section_header="Install",
    )
    assert r["should_use"] and r["content_type"] == "code"


def test_batch_report_and_filter():
    chunks = [
        {"content": PROSE, "metadata": {"section_header": "Optimization"}},
        {"content": PROSE, "metadata": {"section_header": "References"}},
        {"content": "x", "metadata": {}},
    ]
    stats = ev.evaluate_chunks(chunks)
    assert (stats["total_chunks"], stats["accepted_chunks"], stats["rejected_chunks"]) == (3, 1, 2)
    assert round(stats["acceptance_rate"]) == 33
    assert sum(stats["rejection_reasons"].values()) == 2
    assert "evaluation" in stats["evaluated_chunks"][0] and "evaluation" not in chunks[0]  # input not mutated
    assert len(ev.filter_chunks(chunks)) == 1


def test_the_word_copyright_in_a_sentence_is_content_but_a_notice_is_boilerplate():
    readme_row = "| Module | Purpose |\n|---|---|\n| `ChunkEvaluator.py` | Flags unusable chunks (TOC, references, copyright, links, low text ratio) and scores quality. |\n| `ingester.py` | Runs the whole ingest pipeline for one file and reports the outcome. |"
    assert judge(readme_row, section_header="Modules")["should_use"]
    for notice in (
        "Copyright (c) 2024 Example Corp. Licensed under the MIT licence for any purpose.",
        "Intro text here that is long enough.\n© 2024 Example Corp, some other words follow here.",
        "Published by Example Press. All rights reserved. No part of this book may be copied.",
    ):
        assert not judge(notice, section_header="Front matter")["should_use"], notice


def test_decorative_banner_comments_are_dropped_as_code():
    banner = "# " + "=" * 70 + "\n# ENTRY POINT\n# " + "=" * 70
    r = judge(banner, **code_meta(kind="module", section_header="<module>"))
    assert not r["should_use"] and "banner" in r["reason"]


def test_figure_captions_are_kept_as_captions_not_discarded():
    r = judge(
        "Figure 3: The architecture of the ingestion pipeline, from upload to indexed chunks.",
        section_header="Architecture",
    )
    assert r["should_use"] and r["content_type"] == "caption" and r["reason"] == "Figure caption"
    assert (
        judge(
            "Fig. 1: A high level research landscape of data collection for machine learning.", section_header="Intro"
        )["content_type"]
        == "caption"
    )
    assert not judge("Fig. 2", section_header="Intro")["should_use"]  # a bare label says nothing


# ---- documents that are not papers or code: statutes, forms, contracts -------------------------------

CLAUSES = "(c) in order to secure the proper management of the company; or\n(d) in the interests of the system as a whole, the regulator may prepare a scheme for reconstruction."


def test_list_clause_c_is_not_a_copyright_notice():
    assert judge(CLAUSES, content_type="prose")["should_use"]


def test_a_real_copyright_notice_is_still_rejected():
    assert not judge("(c) 2024 Example Corp. " + PROSE, content_type="prose")["should_use"]
    assert not judge("Copyright 2024 Example Corp. " + PROSE, content_type="prose")["should_use"]


FORM = (
    "| Name of the company to which the advance was made          | Nature of interest in the company             | Date of advance |\n"
    "|------------------------------------------------------------|-----------------------------------------------|-----------------|\n"
    "|                                                            |                                               |                 |\n"
    "| 1                                                          | 2                                             | 3               |\n"
)


def test_a_table_of_words_is_kept_not_rejected_for_its_pipes():
    assert ev._alpha_ratio(FORM) < 0.30  # the raw ratio would have rejected it
    r = judge(FORM, content_type="table")
    assert r["should_use"] and r["content_type"] == "table"


def test_a_table_of_numbers_is_still_rejected_when_it_is_not_useful():
    numbers = "| 1 | 22 | 333 |\n|---|----|-----|\n| 4 | 55 | 666 |\n"
    assert not judge(numbers, content_type="table")["should_use"]


def test_contents_table_with_a_pages_column_is_rejected():
    rows = "\n".join(f"| {i}. | Some section title number {i} | {i + 3} |" for i in range(1, 9))
    r = judge(rows, section_header="Sections: Pages", content_type="table")
    assert not r["should_use"] and r["content_type"] == "toc"


def test_contents_without_the_word_pages_is_caught_by_rising_page_numbers():
    rows = "\n".join(f"| {40 + i}A. | Power of the authority to act {i} | {10 + i} |" for i in range(8))
    assert not judge(rows, content_type="table")["should_use"]


def test_numbered_data_table_with_random_last_column_is_not_taken_for_contents():
    rows = "\n".join(f"| {i}. | Branch office number {i} | {v} |" for i, v in enumerate([9, 3, 7, 1, 8, 2, 6, 4], 1))
    assert judge(rows, content_type="table")["should_use"]


def test_form_blanks_do_not_reject_a_form():
    form = "Name of the applicant \\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\nAddress of the applicant \\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\nSignature of the applicant \\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_\\_"
    assert judge(form, content_type="prose")["should_use"]


# ---- header filters match whole words ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "header", ["EXTRAORDINARY PUBLISHED BY AUTHORITY", "Authority of the regulator", "Indexed columns", "Preferences"]
)
def test_a_header_that_merely_contains_a_filter_word_is_kept(header):
    assert judge(PROSE, section_header=header, content_type="prose")["should_use"]


@pytest.mark.parametrize("header", ["Author", "Authors", "Index", "References", "Table of Contents", "Appendix A"])
def test_a_header_that_is_a_filter_word_is_still_rejected(header):
    assert not judge(PROSE, section_header=header, content_type="prose")["should_use"]
