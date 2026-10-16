"""Basic integrity tests for the Week 3 synthetic EDA output.

Run from the repository root with:
    python tests/test_eda_logistics.py
"""
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pandas as pd  # noqa: E402
from eda_logistics import DATA, load_data, make_summaries  # noqa: E402


class TestWeek3EDA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = load_data()

    def test_dataset_size_and_unique_ids(self):
        self.assertEqual(len(self.df), 300)
        self.assertTrue(self.df["shipment_id"].is_unique)

    def test_business_ranges(self):
        self.assertTrue((self.df["distance_km"] > 0).all())
        self.assertTrue((self.df["transport_cost_inr"] >= 0).all())
        self.assertTrue((self.df["delivery_time_hours"] > 0).all())

    def test_derived_metrics_are_consistent(self):
        duration = (self.df["delivered_at"] - self.df["order_date"]).dt.total_seconds() / 3600
        delay = (self.df["delivered_at"] - self.df["promised_delivery_at"]).dt.total_seconds() / 3600
        self.assertTrue(((duration - self.df["delivery_time_hours"]).abs() <= 0.02).all())
        self.assertTrue(((delay - self.df["delivery_delay_hours"]).abs() <= 0.02).all())
        self.assertTrue((self.df["on_time_delivery"] == (self.df["delivery_delay_hours"] <= 0)).all())

    def test_summary_outputs_cover_expected_groups(self):
        outputs = make_summaries(self.df)
        self.assertEqual(len(outputs["region_kpis"]), 5)
        self.assertEqual(len(outputs["vehicle_kpis"]), 4)
        self.assertEqual(outputs["descriptive_statistics"]["count"].min(), 300)


if __name__ == "__main__":
    unittest.main(verbosity=2)
