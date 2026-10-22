from rag_template.evals.split import bucket, is_dev, select


def test_the_same_question_always_lands_on_the_same_side_whatever_its_spacing_or_case():
    assert is_dev("What is  the Limit?") == is_dev("what is the limit?  ")
    assert bucket("What is the limit?") == bucket(" what is the LIMIT? ")


def test_dev_and_test_partition_the_questions_and_dev_is_about_sixty_percent():
    qs = [f"question number {i} about topic {i % 17}" for i in range(2000)]
    dev, test = select(qs, str, "dev"), select(qs, str, "test")
    assert sorted(dev + test) == sorted(qs) and select(qs, str, "all") == qs
    assert 0.55 < len(dev) / len(qs) < 0.65
