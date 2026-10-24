import pytest

from rag_template.enrichment import verify as v

CHUNK = (
    "Mitosis is the process of cell division. It proceeds through four phases: prophase, metaphase, "
    "anaphase and telophase. The result is two genetically identical daughter cells."
)
CFG = v.VerifyConfig()


# --------------------------------------------------------------------------- provenance


def test_exact_quote_is_snapped_to_whole_sentences():
    span = v.locate_quote("proceeds through four phases", CHUNK)
    assert span == "It proceeds through four phases: prophase, metaphase, anaphase and telophase."


def test_quote_survives_dropped_punctuation_and_case():
    span = v.locate_quote("the result is two genetically identical daughter cells", CHUNK)
    assert span == "The result is two genetically identical daughter cells."


def test_fuzzy_quote_is_accepted_but_an_invented_one_is_not():
    assert v.locate_quote("Mitosis is the process of cells division.", CHUNK) is not None
    assert v.locate_quote("Meiosis halves the chromosome number in gametes during reproduction.", CHUNK) is None
    assert v.locate_quote("too short", CHUNK) is None


def test_long_quote_keeps_its_exact_span_instead_of_snapping_wider():
    text = "One sentence here. Two sentence here. Three sentence here. Four sentence here. Five sentence here."
    span = v.locate_quote("two sentence here three sentence here four sentence here five sentence here", text)
    assert span.startswith("Two sentence") and span.endswith(
        "Five sentence here"
    )  # exact span, trimmed to alphanumerics


def test_code_quote_is_snapped_to_whole_lines():
    code = "def f(x):\n    y = x * 2\n    return y + 1\n"
    assert v.locate_code_quote("return y + 1", code) == "    return y + 1"
    assert v.locate_code_quote("y=x*2", code) is None  # fewer than 12 alphanumerics
    assert v.locate_code_quote("y = x * 2 return y + 1", code) == "    y = x * 2\n    return y + 1"


# ----------------------------------------------------------------------------- support


def ok(answer, question="What is mitosis?", chunk=CHUNK, **kw):
    return v.check_support(answer, chunk, "", question, v.VerifyConfig(**kw))


def test_support_accepts_a_restatement_and_rejects_invented_content():
    assert ok("Mitosis is the process of cell division.")[0]
    assert not ok("Mitosis happens in the nucleus where ribosomes assemble proteins quickly.")[0]
    bad = ok("It has seven phases.")
    assert not bad[0] and "number" in bad[1]
    assert ok("It has four phases.")[0]  # "four" is in the chunk


def test_rare_word_check_catches_a_swapped_term():
    rare = {"cytokinesis", "kinetochore"}
    assert (
        v.check_support(
            "Mitosis ends with cytokinesis and kinetochore release.",
            CHUNK,
            "",
            "How does mitosis end?",
            CFG,
            rare.__contains__,
        )[0]
        is False
    )
    assert v.check_support(
        "Mitosis ends with the telophase.", CHUNK, "", "How does mitosis end?", CFG, rare.__contains__
    )[0]


def test_symbol_only_answers_are_judged_on_symbols():
    assert v.check_support("N = 6.", "We set N = 6 for all runs.", "", "What is N?", CFG)[0]
    assert not v.check_support("K = 6.", "We set N = 6 for all runs.", "", "What value is assigned?", CFG)[0]


# ----------------------------------------------------------------------------- question


def test_answer_must_add_something_to_the_question():
    assert not v.check_addresses_question("What is mitosis?", "Mitosis is what?")[0]
    assert v.check_addresses_question("What is mitosis?", "Cell division.")[0]


def test_quantity_and_purpose_questions_need_a_quantity_or_a_reason():
    assert not v.check_addresses_question("How many phases does mitosis have?", "Several distinct phases occur.")[0]
    assert v.check_addresses_question("How many phases does mitosis have?", "Four phases.")[0]
    assert not v.check_addresses_question("Why does the cell divide?", "The cell divides into daughters.")[0]
    assert v.check_addresses_question("Why does the cell divide?", "Because growth requires more cells.")[0]


# ---------------------------------------------------------------------------- pipeline


def test_verify_returns_the_exact_quote_and_skips_layers_without_helpers():
    verdict = v.verify(
        "What does mitosis produce?",
        "It produces two genetically identical daughter cells.",
        CHUNK,
        "result is two genetically identical daughter cells",
    )
    assert verdict.ok and verdict.quote == "The result is two genetically identical daughter cells."
    assert not v.verify("What?", "", CHUNK, "x").ok
    assert v.verify(
        "Q?", "Some answer about cells and division.", CHUNK, "Completely unrelated invented quote text here"
    ).reason.startswith("Weak quote")


def test_similarity_layer_rejects_an_answer_far_from_its_quote():
    args = (
        "What does mitosis produce?",
        "It produces two genetically identical daughter cells.",
        CHUNK,
        "The result is two genetically identical daughter cells.",
    )
    assert v.verify(*args, similarity=lambda a, b: 0.9).ok
    low = v.verify(*args, similarity=lambda a, b: 0.2)
    assert not low.ok and "does not follow" in low.reason


def test_pair_verifier_works_without_sentence_transformers():
    pv = v.PairVerifier(use_embeddings=False)
    assert pv.validate(
        "What does mitosis produce?",
        "It produces two genetically identical daughter cells.",
        CHUNK,
        "The result is two genetically identical daughter cells.",
    )[0]


# ------------------------------------------------------------------------------- code

CODE = "def retry(fn, attempts=3, delay=0.5):\n    for i in range(attempts):\n        try:\n            return fn()\n        except OSError:\n            time.sleep(delay * 2 ** i)\n    raise RuntimeError('gave up')"


@pytest.mark.parametrize(
    "answer, good",
    [
        ("It sleeps for `delay * 2 ** i` seconds after an `OSError`.", True),
        (
            "It raises `RuntimeError` once every attempt has failed, and returns `None` otherwise.",
            True,
        ),  # builtins are allowed
        ("It defaults to 3 attempts.", True),
        ("It defaults to 5 attempts.", False),  # 5 is not in the code
        ("It calls `exponential_backoff` between attempts.", False),  # invented identifier
        ("It reads `settings.max_retries`.", False),
    ],
)
def test_code_support_checks_numbers_and_backticked_identifiers(answer, good):
    assert v.check_code_support(answer, CODE)[0] is good


def test_code_verifier_end_to_end():
    cv = v.CodeVerifier()
    assert cv.validate(
        "What does retry raise when every attempt fails?",
        "It raises `RuntimeError`.",
        CODE,
        "raise RuntimeError('gave up')",
    )[0]
    ok, reason = cv.validate(
        "What does retry raise?", "It raises `RuntimeError`.", CODE, "raise ValueError('something else entirely')"
    )
    assert not ok and reason.startswith("Weak quote")


# ------------------------------------------------- numbers (found by running a real 2B model on real documents)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("The upload hash is SHA-256 over the file.", set()),  # a name, not a quantity
        ("Encoded as UTF-8 per ISO-8601, signed with HS256 or GPT-4.", set()),
        ("Retries after 30 seconds, status 409.", {30, 409}),
        ("Between 3-5 attempts.", {3, 5}),  # a range of real numbers
        ("The value is -5 here.", {5}),
        ("Chroma first, then SQLite; the second store follows.", set()),  # sequencing words are not claims
        ("There are three stores and a fourth cache.", {3, 4}),
        ("The third phase has twelve steps.", {3, 12}),
    ],
)
def test_numbers_that_are_names_or_sequencing_words_are_not_claims(text, expected):
    assert v._numbers(text) == expected


def test_a_real_number_is_still_caught_when_a_name_with_digits_is_present():
    ok, why = v.check_support(
        "The file is hashed with SHA-256 and rejected with status 409.",
        "The file is hashed with SHA-256 and rejected with status 400.",
        "",
        "What status?",
        CFG,
    )
    assert not ok and "[409]" in why
    assert v.check_code_support(
        "It uses SHA-256 and waits 30 seconds.", "def f():\n    time.sleep(30)\n    hashlib.sha256()"
    )[0]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("PBKDF2-SHA256 (260 000 iterations)", {260000}),  # a documentation page's own formatting
        ("about 1,000,000 rows and 12 345 678 bytes", {1000000, 12345678}),
        ("codes 5, 409 and 3, 4", {5, 409, 3, 4}),  # a comma followed by a space is a list, not a thousands separator
        (
            "version 2 100 items",
            {2100},
        ),  # known ambiguity: a space plus exactly three digits is read as a thousands group
        ("ports 8080 and 443", {8080, 443}),
    ],
)
def test_thousands_separators_make_one_number(text, expected):
    assert v._numbers(text) == expected


def test_a_grouped_number_matches_across_answer_and_source():
    ok, why = v.check_support(
        "It uses 260 000 iterations.", "PBKDF2-SHA256 (260 000 iterations)", "", "How many iterations?", CFG
    )
    assert ok, why
    ok, why = v.check_support(
        "It uses 260000 iterations.", "PBKDF2-SHA256 (260 000 iterations)", "", "How many iterations?", CFG
    )
    assert ok, why
    ok, why = v.check_support(
        "It uses 200 000 iterations.", "PBKDF2-SHA256 (260 000 iterations)", "", "How many iterations?", CFG
    )
    assert not ok and "200000" in why


# ----------------------------------------- identifiers (found by running a real 2B model on real code)

METHOD = "def get_pending_files(self, limit=10):\n    sql = 'SELECT DISTINCT file_id FROM chunks'\n    return self._run(sql, limit)"


@pytest.mark.parametrize(
    "span, supported",
    [
        ("get_pending_files", True),
        ("DBManager.get_pending_files()", True),  # the class is in the breadcrumb, not the text
        ("packages/qp-core/src/qp_core/DBManager.py", True),
        ("qp_core/src/qp_core/DBManager.py", True),
        ("PendingFilesManager", False),
        ("DBManager.delete_everything()", False),
    ],
)
def test_qualified_names_are_supported_by_the_chunks_breadcrumb(span, supported):
    label = "packages/qp-core/src/qp_core/DBManager.py > DBManager.get_pending_files"
    ok, why = v.check_code_support(f"It calls `{span}` to find them.", METHOD, context=label)
    assert ok is supported, why
    ok_without, _ = v.check_code_support(f"It calls `{span}` to find them.", METHOD)
    assert ok_without is (
        supported and span in ("get_pending_files",)
    )  # without the breadcrumb only the bare name is supported


@pytest.mark.parametrize("span", ["'\"", "^\\s*(?:export)?$", ". Furthermore, the", "-", "=", "x" * 90])
def test_backticked_fragments_that_are_not_identifiers_are_not_judged(span):
    assert v.check_code_support(f"The pattern is `{span}` here.", METHOD)[0]


def test_a_real_invented_identifier_is_still_caught_with_the_breadcrumb_present():
    label = "pkg/db.py > DBManager.get_pending_files"
    ok, why = v.check_code_support("It uses `RetryScheduler.run` to retry.", METHOD, context=label)
    assert not ok and "RetryScheduler.run" in why
    ok, why = v.check_code_support("It waits 30 seconds.", METHOD, context=label)
    assert not ok and "30" in why  # numbers are never satisfied by a breadcrumb


def test_missing_question_terms_is_a_hint_about_words_no_source_contains():
    sources = [
        "The orchestrator keeps interview results in active_sessions for thirty minutes.",
        "Sessions end after a restart.",
    ]
    assert v.missing_question_terms("What is the Redis cache expiry for interview sessions?", sources) == [
        "redis",
        "cache",
        "expiry",
    ]
    assert v.missing_question_terms("How long do interview results survive a restart?", sources) == [
        "survive"
    ]  # filler words never count; a paraphrase does (why this is only a hint)
    assert v.missing_question_terms("Where are interview results and sessions after a restart?", sources) == []
    assert v.missing_question_terms("sessions sessions SESSIONS", sources) == []
    assert v.missing_question_terms("Which Kafka topic and which kafka broker?", sources) == [
        "kafka",
        "topic",
        "broker",
    ]  # each word once
    assert v.missing_question_terms("", sources) == [] and v.missing_question_terms("slack", []) == ["slack"]


# ---- numbers in dates and questions -------------------------------------------------------------------------------


def test_an_ordinal_in_the_source_supports_the_plain_number_in_the_answer():
    cfg = v.VerifyConfig()
    src = "The Act received the assent of the President on the 23rd July, 1992, and was published on the 28th day of July."
    ok, why = v.check_support(
        "The President assented on July 23, 1992.", src, src, "When did the President assent?", cfg
    )
    assert ok, why


def test_a_number_stated_in_the_question_is_not_an_invented_number():
    cfg = v.VerifyConfig()
    src = "Section 7 bars compulsory re-acquisition of any enterprise transferred by the Government."
    q = "Could the Government take back a bank it privatized in 1995?"
    ok, why = v.check_support(
        "Section 7 bars re-acquisition of an enterprise transferred in 1995.", src, src, q, cfg, trusted_question=True
    )
    assert ok, why
    # a generated question is written by the model being checked, so its numbers prove nothing
    ok, why = v.check_support("Section 7 bars re-acquisition of an enterprise transferred in 1995.", src, src, q, cfg)
    assert not ok and "1995" in why


def test_an_invented_number_is_still_unsupported():
    cfg = v.VerifyConfig()
    src = "The Act received the assent of the President on the 23rd July, 1992."
    ok, why = v.check_support(
        "The President assented on July 24, 1992.", src, src, "When did the President assent?", cfg
    )
    assert not ok and "24" in why
