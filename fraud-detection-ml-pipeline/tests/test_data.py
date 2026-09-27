from src.data import FEATURES, generate_transactions


def test_generator_is_reproducible_and_valid():
    first = generate_transactions(1_000, seed=7)
    second = generate_transactions(1_000, seed=7)
    assert first.equals(second)
    assert set(FEATURES + ["is_fraud"]) == set(first.columns)
    assert 0 < first["is_fraud"].mean() < 0.25
    assert (first["amount"] >= 0).all()

