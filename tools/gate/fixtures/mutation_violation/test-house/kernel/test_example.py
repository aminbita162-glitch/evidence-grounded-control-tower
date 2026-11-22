from kernel.example import classify


def test_positive():
    assert classify(1) == "positive"
