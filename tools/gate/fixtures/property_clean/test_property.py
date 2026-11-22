def test_key_order_basic():
    assert {"a": 1, "b": 2} == dict(sorted({"b": 2, "a": 1}.items()))
