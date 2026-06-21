"""Run with: python -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "data_quality"))

from dq_framework import check_completeness, check_uniqueness, check_referential_integrity, check_freshness


class TestDQFramework(unittest.TestCase):
    def test_completeness_passes_when_full(self):
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        check = check_completeness(df, "test", ["a", "b"], threshold=0.95)
        self.assertEqual(check.status, "PASS")
        self.assertEqual(check.metric_value, 1.0)

    def test_completeness_fails_with_nulls(self):
        df = pd.DataFrame({"a": [1, None, 3], "b": [4, 5, 6]})
        check = check_completeness(df, "test", ["a", "b"], threshold=0.95)
        self.assertEqual(check.status, "FAIL")

    def test_uniqueness_detects_duplicates(self):
        df = pd.DataFrame({"id": ["A", "A", "B"]})
        check = check_uniqueness(df, "test", "id", threshold=0.99)
        self.assertEqual(check.status, "FAIL")
        self.assertAlmostEqual(check.metric_value, 2 / 3, places=3)

    def test_referential_integrity_catches_orphans(self):
        df = pd.DataFrame({"customer_id": ["C1", "C2", "C99"]})
        valid = {"C1", "C2"}
        check = check_referential_integrity(df, "test", "customer_id", valid, threshold=0.99)
        self.assertEqual(check.status, "FAIL")

    def test_freshness_within_window_passes(self):
        df = pd.DataFrame({"d": [pd.Timestamp.now().strftime("%Y-%m-%d")]})
        check = check_freshness(df, "test", "d", max_age_days=7)
        self.assertEqual(check.status, "PASS")


class TestMedallionLogic(unittest.TestCase):
    def test_negative_quantity_rejected(self):
        df = pd.DataFrame({
            "transaction_id": ["T1", "T2"],
            "quantity": ["-1", "2"],
            "customer_id": ["C1", "C2"],
        })
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
        clean = df[df["quantity"] > 0]
        self.assertEqual(len(clean), 1)
        self.assertEqual(clean.iloc[0]["transaction_id"], "T2")

    def test_missing_customer_id_rejected(self):
        df = pd.DataFrame({"transaction_id": ["T1", "T2"], "customer_id": ["", "C2"]})
        clean = df[df["customer_id"].notna() & (df["customer_id"] != "")]
        self.assertEqual(len(clean), 1)

    def test_gross_margin_calculation(self):
        df = pd.DataFrame({"amount": [1000.0], "cost_price_pct": [0.6]})
        df["gross_margin"] = (df["amount"] * (1 - df["cost_price_pct"])).round(2)
        self.assertAlmostEqual(df.iloc[0]["gross_margin"], 400.0)


if __name__ == "__main__":
    unittest.main()
