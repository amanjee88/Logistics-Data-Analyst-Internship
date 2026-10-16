"""Integrity checks for Week 4 synthetic modeling artifacts.
Run from repository root: python tests/test_week4_modeling.py
"""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "week4_hypothetical_shipments.csv"
OUT = ROOT / "data" / "analysis"
FIG = ROOT / "reports" / "figures"


def main():
    df = pd.read_csv(DATA)
    assert len(df) == 1200, f"Expected 1200 synthetic rows, got {len(df)}"
    assert df.shipment_id.is_unique
    assert df.delivery_time_hours.gt(0).all()
    assert not df["delivery_time_hours"].isna().any()
    metrics = pd.read_csv(OUT / "week4_model_metrics.csv")
    assert set(["Median baseline", "Linear regression", "Tuned random forest"]).issubset(set(metrics.model))
    assert metrics[["MAE_hours", "RMSE_hours", "R2"]].notna().all().all()
    predictions = pd.read_csv(OUT / "week4_test_predictions.csv")
    assert len(predictions) == 240
    assert predictions.shipment_id.is_unique
    recs = pd.read_csv(OUT / "week4_vehicle_assignment_recommendations.csv")
    assert len(recs) == 240
    assert recs.recommended_vehicle.isin(["Bike", "Van", "Truck"]).all()
    summary = json.loads((OUT / "week4_modeling_summary.json").read_text(encoding="utf-8"))
    assert summary["rows"] == 1200
    for name in [
        "week4_actual_vs_predicted.png", "week4_residual_distribution.png", "week4_model_comparison.png",
        "week4_feature_importance.png", "week4_optimization_time_comparison.png",
        "week4_optimization_cost_comparison.png", "week4_test_error_by_region.png",
    ]:
        assert (FIG / name).exists() and (FIG / name).stat().st_size > 1000, name
    print("Week 4 tests passed: dataset, metrics, holdout predictions, recommendations and 7 figures validated.")


if __name__ == "__main__":
    main()
