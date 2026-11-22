"""Example module with a branch for mutation coverage testing."""


def classify(value: int) -> str:
    if value > 0:
        return "positive"
    return "non-positive"
