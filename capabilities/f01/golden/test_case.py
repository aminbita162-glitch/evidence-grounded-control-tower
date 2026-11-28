"""Verify the fixed-point agreement interval used by F01."""

from decimal import Decimal
from unittest import TestCase

from capabilities.f01 import Fact, Interval, quantity


class ConsistencyGolden(TestCase):
    def test_quantity(self) -> None:
        fact = Fact(
            "fact",
            "document",
            "COMMERCIAL_INVOICE",
            "gross_weight",
            "1250",
            "1250",
            "line 1",
            unit="kg",
            scale=0,
        )
        self.assertEqual(quantity(fact), ("kg", Interval(Decimal("1249.5"), Decimal("1250.5"))))
