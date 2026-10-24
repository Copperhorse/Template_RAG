from rag_template.retrieve import zscore_fusion


def test_a_strong_match_counts_more_than_the_same_rank_with_a_weak_one():
    # dense: a clearly best, b and c close; lexical: only b matched strongly
    dense = {"a": 0.80, "b": 0.60, "c": 0.59}
    lexical = {"b": 12.0, "c": 1.0, "d": 0.9}
    fused = zscore_fusion([(dense, 1.0), (lexical, 1.0)])
    order = sorted(fused, key=fused.get, reverse=True)
    assert order[0] == "b" and set(fused) == {"a", "b", "c", "d"}


def test_a_chunk_a_signal_did_not_return_gets_that_signals_lowest_z():
    fused = zscore_fusion([({"a": 1.0, "b": 2.0, "c": 3.0}, 1.0), ({"c": 5.0}, 1.0)])
    assert fused["c"] > fused["b"] > fused["a"]
    low = (1.0 - 2.0) / (2 / 3) ** 0.5  # z of a, the dense minimum
    assert abs(fused["a"] - low) < 1e-9  # the lexical signal has no spread: contributes 0 for everyone


def test_weights_scale_each_signal_and_an_empty_signal_is_ignored():
    dense, lexical = {"a": 1.0, "b": 0.0}, {"a": 0.0, "b": 1.0}
    assert (
        max(
            zscore_fusion([(dense, 2.0), (lexical, 1.0)]),
            key=lambda c: zscore_fusion([(dense, 2.0), (lexical, 1.0)])[c],
        )
        == "a"
    )
    assert zscore_fusion([(dense, 1.0), ({}, 1.0)]).keys() == {"a", "b"}
