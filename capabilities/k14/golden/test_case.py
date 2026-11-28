"""Verify the bilingual fixture and its alternate numeral forms."""

from unittest import TestCase

from kernel.lib.text import comparison_form


class BilingualGolden(TestCase):
    def test_comparison(self) -> None:
        self.assertEqual(comparison_form("وزن ١٢٥٠ كغ"), "وزن 1250 كغ")
