from kernel.example import classify


def test_positive():
    assert classify(1) == "positive"


def test_non_positive():
    assert classify(0) == "non-positive"
    assert classify(-1) == "non-positive"
