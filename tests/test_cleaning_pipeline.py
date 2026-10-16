"""Small regression checks for the Week 2 cleaning pipeline."""
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cleaning_pipeline import run_pipeline  # noqa: E402


def test_pipeline_outputs():
    result = run_pipeline()
    cleaned = pd.read_csv(ROOT / "data" / "processed" / "cleaned_shipments.csv")
    audit = pd.read_csv(ROOT / "data" / "processed" / "cleaning_audit.csv")
    review = pd.read_csv(ROOT / "data" / "processed" / "records_for_manual_review.csv")
    assert result["raw_rows"] > result["clean_rows"] > 0
    assert cleaned["shipment_id"].is_unique
    assert cleaned["distance_km"].gt(0).all()
    assert cleaned["shipment_weight_kg"].gt(0).all()
    assert cleaned["transport_cost_inr"].ge(0).all()
    assert "delivered_at_missing" in cleaned.columns
    assert not audit.empty
    assert "review_reason" in review.columns
    print("All Week 2 pipeline checks passed.")


if __name__ == "__main__":
    test_pipeline_outputs()
