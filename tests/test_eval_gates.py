"""The adversarial gate eval run on a small corpus: the guarantees the gates make must hold on every scenario."""

import pytest

from rag_template.evals.gates import CORRUPTIONS, build_scenarios, run_gate_eval
from rag_template.evals.gold import GoldItem, Query
from rag_template.evals.workspace import Workspace


@pytest.fixture(scope="module")
def scenarios(tmp_path_factory):
    root = tmp_path_factory.mktemp("corpus")
    (root / "retry.py").write_text(
        'import time\n\nDEFAULT_ATTEMPTS = 3\n\n\ndef retry(fn, attempts=DEFAULT_ATTEMPTS, delay=0.5):\n    """Call fn until it succeeds, sleeping delay * 2 ** i between attempts."""\n    for i in range(attempts):\n        try:\n            return fn()\n        except OSError:\n            time.sleep(delay * 2 ** i)\n    raise RuntimeError("gave up after repeated failures")\n'
    )
    (root / "cache.py").write_text(
        'import time\n\n\nclass Cache:\n    """A tiny time-to-live cache for expensive lookups."""\n\n    def __init__(self, ttl=60):\n        self.ttl = ttl\n        self._items = {}\n\n    def get(self, key):\n        value, stored_at = self._items.get(key, (None, 0))\n        if time.time() - stored_at > self.ttl:\n            return None\n        return value\n'
    )
    (root / "deploy.md").write_text(
        "# Deploy\n\n## Rollbacks\n\nA rollback redeploys the previous image tag. The tag is stored in the release manifest, so rolling back never needs a rebuild and completes in under 2 minutes.\n\n## Builds\n\nEvery merge to the main branch triggers a build, and the build fails when the test suite fails within 15 minutes.\n"
    )
    (root / "notes.md").write_text(
        "# Notes\n\n## Storage\n\nThe service keeps every uploaded file for 30 days before the nightly cleanup job removes it from the bucket and the index.\n\n## Access\n\nAccess tokens expire after 24 hours and must be refreshed by the client library before the next request is made.\n"
    )
    ws = Workspace(root, min_tokens=5)
    ws.ingest()
    qs = [
        Query("c1", "how does retry wait", "code", gold=[GoldItem("retry.py", "time.sleep(delay * 2 ** i)")]),
        Query("c2", "ttl check", "code", gold=[GoldItem("cache.py", "if time.time() - stored_at > self.ttl:")]),
        Query(
            "d1",
            "rollback time",
            "doc",
            gold=[GoldItem("deploy.md", "so rolling back never needs a rebuild and completes in under 2 minutes.")],
        ),
        Query(
            "d2",
            "token expiry",
            "doc",
            gold=[
                GoldItem(
                    "notes.md",
                    "Access tokens expire after 24 hours and must be refreshed by the client library before the next request is made.",
                )
            ],
        ),
    ]
    return build_scenarios(qs, ws.db.iter_chunks())


def rates(scenarios, policy="strict"):
    """{corruption: {n, flag_rate}} for one policy."""
    return {
        r["name"]: {
            "n": r["by_policy"][policy]["n"],
            "flag_rate": r["by_policy"][policy]["flag_rate"],
            "expect": r["expect"],
        }
        for r in run_gate_eval(scenarios).rows
    }


def test_scenarios_have_the_gold_chunk_first_and_two_distractors(scenarios):
    assert len(scenarios) == 4
    for s in scenarios:
        assert len(s.hits) == 3 and s.snippet.split()[0] in s.hits[0].content and "[S1]" in s.answer


def test_clean_answers_and_retyped_quotes_are_accepted(scenarios):
    r = rates(scenarios)
    assert r["clean"]["flag_rate"] == 0.0 and r["clean"]["n"] == 4
    assert r["quote_retyped"]["flag_rate"] == 0.0


@pytest.mark.parametrize(
    "name",
    [
        "fabricated_quote",
        "quote_from_wrong_source",
        "no_quotes",
        "no_citation",
        "nonexistent_citation",
        "invented_identifier",
    ],
)
def test_structural_corruptions_are_always_caught(scenarios, name):
    r = rates(scenarios)[name]
    assert r["n"] == 4 and r["flag_rate"] == 1.0, r


def test_a_changed_number_is_caught_where_there_is_one(scenarios):
    r = rates(scenarios)["wrong_number"]
    assert r["n"] >= 2 and r["flag_rate"] == 1.0


def test_negation_is_a_known_blind_spot_and_the_report_says_so(scenarios):
    rep = run_gate_eval(scenarios)
    neg = next(r for r in rep.rows if r["name"] == "negation")
    assert neg["expect"] == "info" and neg["n"] >= 1
    assert neg["flag_rate"] < 0.5  # word-level support checks cannot see a flipped meaning
    assert "negation" in rep.markdown() and "| info |" in rep.markdown()


def test_every_corruption_has_a_unique_name_and_a_kind():
    names = [c.name for c in CORRUPTIONS]
    assert len(names) == len(set(names)) and {c.expect for c in CORRUPTIONS} == {"accept", "flag", "info"}


def test_the_number_corruption_never_touches_the_citation():
    from rag_template.evals.gates import _bump_number

    assert _bump_number("It waits 30 seconds [S1].") == "It waits 37 seconds [S1]."
    assert (
        _bump_number("It defines `retry` [S1].") is None
    )  # no number in the text: not applicable, not a citation change
    assert _bump_number("Tokens last 24 hours. [S1]") == "Tokens last 31 hours. [S1]"


@pytest.mark.parametrize("policy", ["strict", "tolerant", "balanced", "lenient"])
def test_no_policy_lets_a_fabricated_or_foreign_quote_or_a_wrong_number_through(scenarios, policy):
    r = rates(scenarios, policy)
    for name in ("fabricated_quote", "quote_from_wrong_source"):
        # lenient replaces the bad quote with an extracted span, so an answer that is *supported* by the source passes
        # (the clean answer here is); the other policies must flag it outright
        assert r[name]["flag_rate"] == (0.0 if policy == "lenient" else 1.0), (policy, name, r[name])
    for name in ("nonexistent_citation", "no_citation", "invented_identifier", "wrong_number"):
        assert r[name]["flag_rate"] == 1.0, (policy, name, r[name])
    assert r["clean"]["flag_rate"] == 0.0 and r["quote_retyped"]["flag_rate"] == 0.0


def test_loosening_the_policy_only_ever_accepts_more(scenarios):
    rows = run_gate_eval(scenarios).rows
    for row in rows:
        f = [row["by_policy"][p]["flag_rate"] for p in ("strict", "tolerant", "balanced", "lenient")]
        assert f[0] >= f[1] - 1e-9 and f[1] >= f[3] - 1e-9 or row["name"] in ("answer_from_other_source",), (
            row["name"],
            f,
        )
