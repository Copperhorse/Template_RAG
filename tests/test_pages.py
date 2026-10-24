from rag_template.pages import assign_pages, mark_pages, page_label, split_pages


def chunk(content):
    return {"content": content, "metadata": {}}


PAGES = [
    (1, "# Title\n\nFirst page has the abstract of the paper."),
    (2, "Second page explains the method in detail.\n\nIt continues here."),
    (3, "Third page holds the results table and the conclusion."),
]


def test_markers_are_removed_and_pages_are_found_for_each_chunk():
    text, marks = split_pages(mark_pages(PAGES))
    assert "<!--" not in text and [m[1] for m in marks] == [1, 2, 3]
    chunks = [
        chunk("First page has the abstract of the paper."),
        chunk("Second page explains the method in detail."),
        chunk("Third page holds the results table and the conclusion."),
    ]
    assert assign_pages(chunks, text, marks) == 3
    assert [c["metadata"]["page"] for c in chunks] == [1, 2, 3] and not any("page_end" in c["metadata"] for c in chunks)


def test_a_chunk_across_a_page_break_gets_both_pages_and_one_that_cannot_be_found_gets_none():
    text, marks = split_pages(mark_pages(PAGES))
    across = chunk(
        "It continues here. Third page holds the results table and the conclusion."
    )  # the break is invisible once the markers are gone
    lost = chunk("Text a caption moved away from the page it was found in, nowhere in the document.")
    assign_pages([across, lost], text, marks)
    assert (across["metadata"]["page"], across["metadata"]["page_end"]) == (2, 3) and "page" not in lost["metadata"]


def test_a_repeated_sentence_is_located_after_the_previous_chunk_not_at_its_first_occurrence():
    pages = [
        (1, "Intro.\n\nThe same sentence appears twice in this paper."),
        (5, "The same sentence appears twice in this paper."),
    ]
    text, marks = split_pages(mark_pages(pages))
    first, second = (
        chunk("Intro. The same sentence appears twice in this paper."),
        chunk("The same sentence appears twice in this paper."),
    )
    assign_pages([first, second], text, marks)
    assert first["metadata"]["page"] == 1 and second["metadata"]["page"] == 5


def test_page_labels():
    assert (
        page_label({"page": 5}) == "p. 5"
        and page_label({"page": 5, "page_end": 6}) == "pp. 5-6"
        and page_label({}) == ""
    )
