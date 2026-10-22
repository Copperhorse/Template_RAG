"""tablecheck: a number the answer states must come from a table cell whose row and column fit the answer."""
import pytest

from rag_template.tablecheck import check_table_numbers, normalise_number, numbers, parse_tables

HEADER = "| Model | V6 pass@1 EASY | V6 pass@1 HARD | V6 pass@5 EASY | V6 pass@5 HARD |\n|---|---|---|---|---|\n"
TABLE = HEADER + (
    "| Qwen3-30B-Thinking | 99.8 | 41.5 | 100.0 | 59.7 |\n"
    "| + SSD | 100.0 +0.2 | 46.7 +5.2 | 100.0 | 65.8 +6.1 |\n"
    "| Llama-3.1-8B | 46.8 | 0.0 | 71.0 | 12.4 |\n"
    "| + SSD | 52.6 +5.8 | 1.6 +1.6 | 77.7 | 14.0 |\n"
)
CAPTION = "Table 2 Per-model results on the benchmark.\n\n"
Q = "What is Qwen3-30B-Thinking's V6 hard pass@1 before and after SSD?"


def ok(answer, question=Q, evidence=(CAPTION + TABLE,)):
    return check_table_numbers(answer, list(evidence), question)[0]


def test_numbers_are_read_as_a_reader_sees_them():
    assert numbers("went from 42.4% to 55.3%, +12.9pp, 1,000 runs; Qwen3-30B, v6, pass@5") == ["42.4", "55.3", "12.9", "1000"]
    assert numbers("ARC-AGI-1 and ARC-AGI-2 scores of 44.6 and a range 3-5") == ["44.6", "3", "-5"[1:]]  # a digit joined to a name by a hyphen is part of the name; a range is two numbers
    assert normalise_number("+5.2") == "5.2" and normalise_number("30%") == "30"


def test_a_table_is_read_with_row_labels_column_headers_and_inherited_parents():
    cells = {(c.number, c.row_label) for c in parse_tables(TABLE)[0]}
    assert ("46.7", "Qwen3-30B-Thinking / + SSD") in cells and ("1.6", "Llama-3.1-8B / + SSD") in cells and ("41.5", "Qwen3-30B-Thinking") in cells
    assert next(c for c in parse_tables(TABLE)[0] if c.number == "46.7").column == "V6 pass@1 HARD"


def test_the_right_cells_pass():
    assert ok("Qwen3-30B-Thinking's V6 hard pass@1 was 41.5 before SSD and 46.7 after.")
    assert ok("It goes from 41.5 to 46.7.")  # the entity comes from the question


def test_a_number_from_the_wrong_column_is_flagged():
    good, why = check_table_numbers("Qwen3-30B-Thinking's V6 hard pass@1 before SSD was 41.5 and after SSD it is 59.7.", [CAPTION + TABLE], Q)
    assert not good and "59.7" in why and "pass@5" in why  # 59.7 is the baseline's pass@5, not an SSD pass@1
    assert not ok("After SSD the V6 hard pass@1 is 65.8.")  # an SSD pass@5 value


def test_a_number_from_the_wrong_row_is_flagged_even_if_one_label_word_matches():
    assert not ok("Llama-3.1-8B reaches 46.7 after SSD.", "What does Llama-3.1-8B reach after SSD?")
    assert ok("Llama-3.1-8B reaches 1.6 after SSD on hard pass@1.", "What does Llama-3.1-8B reach after SSD?")


def test_pass_at_five_values_are_accepted_when_the_answer_says_pass_at_five():
    assert ok("The V6 hard pass@5 of Qwen3-30B-Thinking is 59.7 before SSD.", "What is the V6 hard pass@5 of Qwen3-30B-Thinking before SSD?")


def test_deltas_in_a_cell_are_numbers_too():
    assert ok("SSD adds 5.2 points on V6 hard pass@1 for Qwen3-30B-Thinking.")


def test_a_number_the_prose_also_states_is_not_held_to_the_table():
    prose = "The experiments use 52.6 samples in total.\n\n" + TABLE
    assert ok("Llama-3.1-8B-Instruct uses 52.6 samples.", "How many samples?", evidence=[prose])


def test_numbers_that_are_in_no_table_are_left_to_the_other_checks():
    assert ok("Training took 3 days on 8 GPUs.") and check_table_numbers("anything 12.5", ["no table here at all"], "q") == (True, "")


def test_rows_without_a_label_cannot_be_judged_by_row_so_only_the_column_counts():
    unlabeled = HEADER + "|  | 1.5 | 2.5 | 3.5 | 4.5 |\n"
    assert ok("The pass@1 hard value is 2.5.", "q", evidence=[unlabeled])
    assert not ok("The pass@1 hard value is 4.5.", "q", evidence=[unlabeled])


@pytest.mark.parametrize("ragged", ["| a | b |\n|---|---|\n| x | 1.5 | 2.5 |"])
def test_a_row_longer_than_its_header_has_no_column_to_contradict(ragged):
    assert ok("x has 2.5", "x?", evidence=[ragged])


def test_a_subject_named_before_a_semicolon_or_in_the_previous_sentence_still_counts():
    table = "| Endpoint | Auth | Note |\n|---|---|---|\n| `DELETE /api/user/{user_id}` | yes | delete file, embedding, result; 207 (account kept) if one could not be removed |\n"
    assert ok("delete file, embedding, result; 207 (account kept) if one could not be removed", "q", evidence=[table])
    assert ok("The DELETE endpoint removes the user. It returns 207 if one embedding could not be removed.", "q", evidence=[table])


def test_inflected_words_match_the_row_label():
    table = "| Method | Notes |\n|---|---|\n| `DELETE /api/users/{user_id}` | deletes files, embeddings, results; `207` (account kept) if some could not be removed |\n"
    assert ok("It deletes files, embeddings and results; 207 if some embeddings could not be removed.", "What status when an account is deleted?", evidence=[table])


def test_the_row_context_reaches_one_sentence_back_but_no_further():
    one_back = "Qwen3-30B-Thinking improves. It reaches 46.7 after SSD on V6 hard pass@1."
    two_back = "Qwen3-30B-Thinking improves. Nothing else changes. It reaches 46.7 after SSD on V6 hard pass@1."
    assert ok(one_back, "What changes?") and not ok(two_back, "What changes?")


ABLATION = ("| Method | Acc(%) | Depth |\n|---|---|---|\n| HRM | 55.0 | 24 |\n| TRM (_T_ =3,_n_=6) | 87.4 | 42 |\n| w/ ACT | 86.1 | 42 |\n"
            "| w/_T_ =2,_n_=2 | 73.7 | 12 |\n| w/ 1-step gradient | 56.5 | 42 |\n")


def test_ablation_rows_are_labelled_by_the_base_row_they_vary_even_when_one_is_written_w_slash_T():
    labels = {c.number: c.row_label for c in parse_tables(ABLATION)[0]}
    assert labels["73.7"] == "TRM (_T_ =3,_n_=6) / w/_T_ =2,_n_=2" and labels["56.5"] == "TRM (_T_ =3,_n_=6) / w/ 1-step gradient"


def test_the_trm_ablation_answer_that_was_wrongly_flagged_now_passes_and_a_wrong_row_still_fails():
    q = "How much does using the 1-step gradient approximation hurt TRM on Sudoku-Extreme?"
    assert ok("Using the 1-step gradient approximation results in an accuracy of 56.5% for TRM on Sudoku-Extreme.", q, evidence=[ABLATION])
    assert not ok("Using the 1-step gradient approximation results in an accuracy of 73.7% for TRM on Sudoku-Extreme.", q, evidence=[ABLATION])


NO_EMA = ("| Method | Acc(%) |\n|---|---|\n| TRM (T=3, n=6) | 87.4 |\n| no EMA | 79.9 |\n| w/ 1-step gradient | 56.5 |\n"
          "| HRM | 55.0 |\n| no EMA | 70.0 |\n")


def test_a_row_whose_own_label_is_unique_does_not_need_the_label_of_the_row_before_it():
    q = "What accuracy does TRM reach with the 1-step gradient approximation?"
    assert ok("The 1-step gradient approximation gives 56.5% for TRM.", q, evidence=[NO_EMA])



def test_only_real_continuation_labels_inherit_the_row_above():
    from rag_template.tables import inherit_row_labels

    rows = inherit_row_labels(["| Base | 1 |", "| + SSD | 2 |", "| (ours) | 3 |", "| -0.5 | 4 |", "| (a) Setup | 5 |"])
    labels = [r.split("|")[1].strip() for r in rows]
    # "-0.5" and "(a) Setup" are ordinary labels: they keep their own text (and become the parent of what follows)
    assert labels == ["Base", "Base / + SSD", "Base / (ours)", "-0.5", "(a) Setup"]
