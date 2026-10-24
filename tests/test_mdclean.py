"""Generic repairs to converter Markdown: each rule, and the cases that must be left alone."""

from rag_template.mdclean import clean_markdown


def test_br_inside_a_table_row_becomes_a_space_so_words_stay_separate():
    out = clean_markdown("|a|b|\n|---|---|\n|constant<br>compute per token|x<br/>y|")
    assert "constant compute per token" in out and "x y" in out and "<br" not in out


def test_presentation_tags_are_removed_and_their_text_kept():
    assert clean_markdown("Thursday<sup>2</sup> of <u>each</u> week") == "Thursday^2 of each week\n"


def test_superscripts_keep_their_link_as_a_caret():
    out = clean_markdown("an authorized dealer[, money changer]<sup>3</sup> in Pakistan and x<sup>2</sup> + 1")
    assert "]^3 in Pakistan" in out and "x^2 + 1" in out


def test_bold_markers_come_off_but_a_lone_asterisk_survives():
    out = clean_markdown("**1. Short title.—** (1) This *Ordinance* costs 2 * 3")
    assert out == "1. Short title.— (1) This *Ordinance* costs 2 * 3\n"


def test_heading_text_is_cleaned():
    assert clean_markdown("### **`04`** The shape of an application\n\ntext here.").startswith(
        "### 04 The shape of an application"
    )


def test_heading_fragments_are_demoted_to_text():
    out = clean_markdown("# **engage.—**\n\nBody text.\n\n## Real Heading\n\nMore text.\n\n## 17\n\nx.")
    assert "# engage" not in out and "engage.—" in out
    assert "## Real Heading" in out and "## 17" not in out


def test_a_sentence_broken_by_a_blank_line_is_joined():
    assert (
        clean_markdown("(1) This Ordinance\n\nmay be called the Banking Companies Ordinance.")
        == "(1) This Ordinance may be called the Banking Companies Ordinance.\n"
    )


def test_paragraphs_that_end_properly_or_start_new_blocks_are_not_joined():
    md = "First sentence ends here.\n\nsecond starts lower case.\n\nA heading follows\n\n- list item\n\n| a | b |"
    out = clean_markdown(md)
    assert "First sentence ends here.\n\nsecond" in out
    assert "A heading follows\n\n- list item" in out and "\n\n| a | b |" in out


def test_fenced_code_is_never_touched():
    code = "```\nx = '<br>'   # **bold**\n\nif a:\n    <sup>\n```"
    assert clean_markdown("Intro text.\n\n" + code + "\n\nAfter.") == "Intro text.\n\n" + code + "\n\nAfter.\n"


def test_image_placeholders_are_dropped():
    assert clean_markdown("Before.\n\n<!-- image -->\n\nAfter.") == "Before.\n\nAfter.\n"


def test_a_padded_table_separator_is_normalised_to_the_column_count():
    md = "|Name       |Value |\n|-----------|:----:|\n|a|1|"
    out = clean_markdown(md)
    assert out.splitlines()[1] == "|---|---|" and out.splitlines()[0] == "|Name |Value |"
    assert (
        clean_markdown("some text -- with dashes\n\n--- \n").count("---") == 1
    )  # a horizontal rule is not a table separator


def test_a_sentence_split_at_a_page_break_is_rejoined_and_the_page_marker_survives():
    from rag_template.pages import mark_pages, split_pages

    text, marks = split_pages(clean_markdown(mark_pages([(1, "The banking companies"), (2, "may be called upon.")])))
    assert text == "The banking companies\nmay be called upon.\n"
    assert [m[1] for m in marks] == [1, 2] and marks[1][0] == len(
        "thebankingcompanies"
    )  # page 2 starts after page 1's letters


def test_dunder_names_and_snake_case_are_text_not_bold_markup():
    assert (
        clean_markdown("see `__init__` and __main__ and a__b here, **bold** goes")
        == "see `__init__` and __main__ and a__b here, bold goes\n"
    )


def test_blank_lines_inside_fenced_code_are_kept():
    code = "```\na = 1\n\n\n\nb = 2\n```"
    assert code in clean_markdown("Intro.\n\n" + code + "\n\nAfter.")
