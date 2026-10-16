"""Starter KPI framework for the Logistics Data Analyst Week 1 project.

IMPORTANT: The accompanying CSV is a small synthetic fixture for code testing only.
It is not real company, customer, or courier data and should not be cited as operational evidence.

Run from the repository root:
    python src/kpi_framework.py
Dependencies: pandas
"""
from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_shipments_simulated.csv"
REQUIRED_COLUMNS = {
    "shipment_id", "promised_delivery_at", "delivered_at", "region",
    "distance_km", "transport_cost_inr", "first_attempt_status"
}


def load_shipments(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load the shipment table and validate the minimum schema."""
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Required columns missing: {sorted(missing)}")
    for col in ["promised_delivery_at", "delivered_at"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["distance_km", "transport_cost_inr"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def calculate_kpis(df: pd.DataFrame) -> dict:
    """Calculate planning KPIs; clarify denominators before any real use."""
    total = len(df)
    delivered = df[df["delivered_at"].notna()].copy()
    delivered["delivery_hours"] = (
        delivered["delivered_at"] - delivered["promised_delivery_at"]
    ).dt.total_seconds() / 3600
    on_time_n = int((delivered["delivery_hours"] <= 0).sum())
    late = delivered[delivered["delivery_hours"] > 0]
    cost = df["transport_cost_inr"].dropna()
    first_attempt = df["first_attempt_status"].dropna().astype(str).str.strip().str.lower()

    return {
        "shipments_in_extract": total,
        # Snapshot convention: only delivered shipments can count as on time here;
        # undelivered shipments are not counted as successful on-time deliveries.
        "on_time_delivery_rate_pct": round(100 * on_time_n / total, 2) if total else None,
        "average_delivery_time_vs_promise_hours": round(float(delivered["delivery_hours"].mean()), 2) if len(delivered) else None,
        "average_late_delivery_hours": round(float(late["delivery_hours"].mean()), 2) if len(late) else 0.0,
        "transport_cost_per_shipment_inr": round(float(cost.sum() / cost.count()), 2) if cost.count() else None,
        "first_attempt_success_rate_pct": round(100 * (first_attempt == "success").sum() / len(first_attempt), 2) if len(first_attempt) else None,
    }


def quality_checks(df: pd.DataFrame) -> pd.DataFrame:
    """Return simple quality checks to guide later cleaning; do not auto-delete rows."""
    checks = [
        ("duplicate_shipment_id_rows", int(df["shipment_id"].duplicated().sum())),
        ("missing_promised_delivery_at", int(df["promised_delivery_at"].isna().sum())),
        ("missing_delivered_at", int(df["delivered_at"].isna().sum())),
        ("missing_transport_cost_inr", int(df["transport_cost_inr"].isna().sum())),
        ("nonpositive_distance_km", int((df["distance_km"].dropna() <= 0).sum())),
        ("negative_transport_cost_inr", int((df["transport_cost_inr"].dropna() < 0).sum())),
    ]
    return pd.DataFrame(checks, columns=["check", "count"])


def main() -> None:
    df = load_shipments()
    print("DATA STATUS: synthetic demonstration data; not real operational evidence")
    print(f"Rows loaded: {len(df)}")
    print("\nKPI DEMONSTRATION")
    for name, value in calculate_kpis(df).items():
        print(f"- {name}: {value}")
    print("\nDATA QUALITY CHECKS")
    print(quality_checks(df).to_string(index=False))
    print("\nBefore real-world reporting, confirm status definitions, reporting window, missing-data rules, and business-owned targets.")


if __name__ == "__main__":
    main()
