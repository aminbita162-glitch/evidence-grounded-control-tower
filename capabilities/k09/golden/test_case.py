"""Verify the fail-closed duplicate shield result for an offline index."""

from unittest import TestCase

from capabilities.k09 import FingerprintIndex


class ShieldGolden(TestCase):
    def test_index_unavailable(self) -> None:
        index = FingerprintIndex()
        index.available = False
        report = index.evaluate("SYN-TENANT", "SYN-CASE")
        self.assertEqual(report.reason_codes, ("K09.ABSTAIN.INDEX_UNAVAILABLE",))
