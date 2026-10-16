"""Generate the Week 3 hypothetical logistics shipment dataset.

Run from the repository root:
    python src/generate_week3_hypothetical_data.py

All records are synthetic and created for educational EDA practice. They are not
records from a real company and are not downloaded from the public reference.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "analysis" / "week3_hypothetical_shipments.csv"
SEED = 20261016
N_ROWS = 300


def generate_dataset(n_rows: int = N_ROWS, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    regions = np.array(["North", "South", "East", "West", "Central"])
    region = rng.choice(regions, size=n_rows, p=[0.23, 0.22, 0.18, 0.20, 0.17])
    vehicles = np.array(["Two-wheeler", "Van", "Mini-truck", "Truck"])
    vehicle = rng.choice(vehicles, size=n_rows, p=[0.18, 0.42, 0.28, 0.12])

    distance = np.empty(n_rows)
    weight = np.empty(n_rows)
    for i, v in enumerate(vehicle):
        if v == "Two-wheeler":
            distance[i] = np.clip(rng.gamma(2.2, 10.0), 2, 55)
            weight[i] = np.clip(rng.gamma(2.0, 1.7), 0.4, 18)
        elif v == "Van":
            distance[i] = np.clip(rng.gamma(2.1, 34.0), 5, 260)
            weight[i] = np.clip(rng.gamma(2.4, 8.0), 1.0, 85)
        elif v == "Mini-truck":
            distance[i] = np.clip(rng.gamma(2.5, 48.0), 10, 360)
            weight[i] = np.clip(rng.gamma(2.7, 23.0), 5, 190)
        else:
            distance[i] = np.clip(rng.gamma(2.8, 95.0), 35, 700)
            weight[i] = np.clip(rng.gamma(3.2, 92.0), 45, 900)

    volume = np.clip(weight / rng.uniform(180, 360, size=n_rows) + rng.gamma(1.8, 0.025, n_rows), 0.01, 4.5)
    start = pd.Timestamp("2026-07-01")
    end = pd.Timestamp("2026-09-30 23:00:00")
    total_hours = int((end - start).total_seconds() // 3600)
    order_ts = start + pd.to_timedelta(rng.integers(0, total_hours + 1, size=n_rows), unit="h")

    speed = np.select(
        [vehicle == "Two-wheeler", vehicle == "Van", vehicle == "Mini-truck", vehicle == "Truck"],
        [26.0, 32.0, 29.0, 36.0],
        default=30.0,
    )
    expected_transit = 1.5 + distance / speed + 0.25 * (weight / 50.0)
    service_buffer = np.select(
        [vehicle == "Two-wheeler", vehicle == "Van", vehicle == "Mini-truck", vehicle == "Truck"],
        [3.0, 4.2, 5.0, 7.5], default=4.0,
    )
    promised_hours = np.maximum(4.0, expected_transit * 1.35 + service_buffer)
    promised_ts = order_ts + pd.to_timedelta(promised_hours, unit="h")

    region_delay = pd.Series(region).map({"North": -0.5, "South": 0.2, "East": 2.3, "West": 0.5, "Central": -0.1}).to_numpy()
    vehicle_delay = pd.Series(vehicle).map({"Two-wheeler": -0.3, "Van": 0.0, "Mini-truck": 0.7, "Truck": 1.0}).to_numpy()
    load_effect = np.maximum(weight - 25, 0) / 70.0
    disruption = rng.choice([0.0, 3.0, 7.0], size=n_rows, p=[0.78, 0.17, 0.05])
    delay_hours = rng.normal(loc=-5.0, scale=4.8, size=n_rows) + 0.009 * distance + region_delay + vehicle_delay + load_effect + disruption
    # Keep delivered timestamp later than order, while preserving true lateness/early delivery relative to promise.
    delay_hours = np.maximum(delay_hours, -promised_hours + 0.5)
    delivered_ts = promised_ts + pd.to_timedelta(delay_hours, unit="h")
    delivery_time_hours = (delivered_ts - order_ts).total_seconds() / 3600.0
    delay_hours_actual = (delivered_ts - promised_ts).total_seconds() / 3600.0

    base_rate = pd.Series(vehicle).map({"Two-wheeler": 7.5, "Van": 11.0, "Mini-truck": 14.5, "Truck": 18.0}).to_numpy()
    base_fee = pd.Series(vehicle).map({"Two-wheeler": 45, "Van": 95, "Mini-truck": 160, "Truck": 300}).to_numpy()
    region_cost = pd.Series(region).map({"North": 0, "South": 8, "East": 18, "West": 12, "Central": 5}).to_numpy()
    transport_cost = base_fee + base_rate * distance + 0.65 * weight + 22.0 * volume + region_cost + rng.normal(0, 55, size=n_rows)
    transport_cost = np.maximum(transport_cost, base_fee * 0.7)

    # First-attempt success is probabilistic and intentionally imperfect; it is not presented as real-world evidence.
    fail_logit = -3.0 + 0.0015 * distance + 0.0020 * weight + 0.55 * (delay_hours_actual > 0) + 0.25 * (region == "East")
    fail_prob = 1 / (1 + np.exp(-fail_logit))
    first_attempt = np.where(rng.random(n_rows) < fail_prob, "Failed", "Success")

    df = pd.DataFrame({
        "shipment_id": [f"W3SHP{i:04d}" for i in range(1, n_rows + 1)],
        "order_date": order_ts,
        "promised_delivery_at": promised_ts,
        "delivered_at": delivered_ts,
        "region": region,
        "distance_km": np.round(distance, 1),
        "shipment_weight_kg": np.round(weight, 2),
        "shipment_volume_m3": np.round(volume, 3),
        "transport_cost_inr": np.round(transport_cost, 2),
        "vehicle_type": vehicle,
        "first_attempt_status": first_attempt,
        "delivery_time_hours": np.round(delivery_time_hours, 2),
        "delivery_delay_hours": np.round(delay_hours_actual, 2),
        "on_time_delivery": delay_hours_actual <= 0,
        "shipment_units": rng.integers(1, 9, size=n_rows),
    })
    for col in ["order_date", "promised_delivery_at", "delivered_at"]:
        df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return df


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df = generate_dataset()
    df.to_csv(OUT, index=False)
    print(f"Saved {len(df)} synthetic shipment rows to: {OUT.relative_to(ROOT)}")
    print("DATA NOTE: This file is generated synthetic data, not real shipment records.")


if __name__ == "__main__":
    main()
