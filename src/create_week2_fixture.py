"""Create the small, synthetic Week 2 logistics data-quality training fixture.

This is intentionally synthetic. It is not a download from the cited public reference dataset.
Run from repository root: python src/create_week2_fixture.py
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "sample_shipments_simulated.csv"
OUTPUT = ROOT / "data" / "raw" / "raw_shipments_simulated.csv"

base = pd.read_csv(SOURCE, dtype=str, keep_default_na=False)
# Extend the original 30-row Week 1 fixture with six additional unique synthetic records.
extras = []
for i in range(6):
    row = base.iloc[i].copy()
    row["shipment_id"] = f"SHP{31+i:04d}"
    order = pd.to_datetime(row["order_date"]) + pd.Timedelta(days=1+i)
    promise = pd.to_datetime(row["promised_delivery_at"]) + pd.Timedelta(days=1+i)
    delivered_str = row["delivered_at"]
    delivered = (pd.to_datetime(delivered_str) + pd.Timedelta(days=1+i)) if delivered_str and delivered_str.lower() not in {"nan", "na"} else pd.NaT
    row["order_date"] = order.strftime("%Y-%m-%d %H:%M:%S")
    row["promised_delivery_at"] = promise.strftime("%Y-%m-%d %H:%M:%S")
    row["delivered_at"] = "" if pd.isna(delivered) else delivered.strftime("%Y-%m-%d %H:%M:%S")
    row["distance_km"] = str(round(float(row["distance_km"]) + 2.3, 1))
    row["shipment_weight_kg"] = str(round(float(row["shipment_weight_kg"]) + 0.7, 2))
    row["transport_cost_inr"] = str(round(float(row["transport_cost_inr"]) + 21.5, 2))
    extras.append(row)
raw = pd.concat([base, pd.DataFrame(extras)], ignore_index=True)

# Inject realistic data-quality problems for the cleaning pipeline to find.
raw.loc[0, "region"] = "  north "
raw.loc[0, "vehicle_type"] = "MINI TRUCK"
raw.loc[0, "first_attempt_status"] = " success "
raw.loc[1, "order_date"] = pd.to_datetime(raw.loc[1, "order_date"]).strftime("%d-%b-%Y %I:%M %p")
raw.loc[1, "region"] = "SOUTH"
raw.loc[2, "promised_delivery_at"] = pd.to_datetime(raw.loc[2, "promised_delivery_at"]).strftime("%B %d, %Y %I:%M %p")
raw.loc[2, "region"] = "cntral"
raw.loc[3, "vehicle_type"] = "mini truck"
raw.loc[3, "first_attempt_status"] = "successful"
raw.loc[4, "distance_km"] = ""
raw.loc[5, "transport_cost_inr"] = "unknown"
raw.loc[6, "shipment_weight_kg"] = "—"
raw.loc[7, "delivered_at"] = "not recorded"
raw.loc[8, "delivered_at"] = "2026-09-30 10:00:00"  # before order date; must be flagged, not silently accepted
raw.loc[9, "distance_km"] = "-12"
raw.loc[10, "shipment_weight_kg"] = "0"
raw.loc[11, "transport_cost_inr"] = "-45"
raw.loc[12, "distance_km"] = "9999"  # statistical outlier, retain and flag
raw.loc[13, "transport_cost_inr"] = "₹ 99,999.00"  # statistical outlier, retain and flag
raw.loc[14, "shipment_weight_kg"] = "750"  # statistical outlier, retain and flag
raw.loc[15, "promised_delivery_at"] = "31-02-2026 08:00"
raw.loc[16, "order_date"] = "not available"
raw.loc[17, "region"] = "   "
raw.loc[18, "first_attempt_status"] = "Fail"
raw.loc[19, "first_attempt_status"] = "Y"
raw.loc[20, "transport_cost_inr"] = "₹ 1,234.50"
raw.loc[21, "distance_km"] = " 42.5 "
raw.loc[22, "region"] = "NORTH"
raw.loc[23, "vehicle_type"] = "Two wheeler"
raw.loc[24, "first_attempt_status"] = "FAILED"

# An exact duplicate and a conflicting duplicate business key illustrate two distinct cases.
raw = pd.concat([raw, raw.iloc[[5]].copy()], ignore_index=True)
conflict = raw.iloc[[6]].copy()
conflict.loc[:, "transport_cost_inr"] = "₹ 9,999.00"
raw = pd.concat([raw, conflict], ignore_index=True)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
raw.to_csv(OUTPUT, index=False)
print(f"Created {OUTPUT.relative_to(ROOT)} with {len(raw)} synthetic raw rows")
print("NOTICE: This is a synthetic training fixture, not real shipment records or a downloaded public dataset.")
