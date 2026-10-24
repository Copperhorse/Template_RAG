from rag_template.retrieve import Answerer, Hit
from test_answerer import FakeLLM, reply
from test_retrieval import build

DOC = """# Training

## Recipe

The method adds the following improvements: Dynamic Sampling filters prompts whose answers are all right or all wrong.

| Strategy | Step time |
|---|---|
| Vanilla | 488 |
| Chunk-8k | 286 |

Clip-Higher raises the upper clipping threshold. Token-level loss averages over tokens. Overlong filtering drops cut-off samples.

## Other

An unrelated section that talks about the weather in some detail for a while, to keep sections apart.
"""


def retriever(make_rag, tmp_path):
    rag = build(make_rag, tmp_path, {"recipe.md": DOC})
    return rag, rag.retriever


def test_the_tail_of_a_list_cut_by_a_table_is_found_in_the_same_section(make_rag, tmp_path):
    rag, r = retriever(make_rag, tmp_path)
    first = [h for h in r.search("Dynamic Sampling filters prompts", k=1, rerank=False)]
    assert first and "Dynamic Sampling" in first[0].content
    extra = r.section_neighbors(first, limit=3)
    text = " ".join(h.content for h in extra)
    assert extra and all(h.breadcrumb == first[0].breadcrumb and h.section_of == first[0].chunk_id for h in extra)
    assert "Clip-Higher" in text or "Clip-Higher" in first[0].content
    assert all("weather" not in h.content for h in extra)  # another section is never pulled in
    assert all(h.chunk_id != first[0].chunk_id for h in extra) and r.section_neighbors(first, limit=0) == []


def test_expansion_is_off_by_default_and_appends_after_the_retrieved_sources(make_rag, tmp_path):
    rag, r = retriever(make_rag, tmp_path)
    q = "What improvements does the method add?"
    llm_off, llm_on = (
        FakeLLM(reply("x [S1].", ("S1", "Dynamic Sampling"))),
        FakeLLM(reply("x [S1].", ("S1", "Dynamic Sampling"))),
    )
    Answerer(r, llm_off).ask(q, k=1, rerank=False)
    Answerer(r, llm_on, expand_section=3).ask(q, k=1, rerank=False)
    assert llm_on.prompts[0].count("[S") > llm_off.prompts[0].count("[S") and "[S1]" in llm_on.prompts[0]
    assert llm_on.prompts[0].index("[S1]") < llm_on.prompts[0].index("[S2]")
