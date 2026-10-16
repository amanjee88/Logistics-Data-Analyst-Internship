"""Generate a deterministic synthetic logistics dataset for Week 4 modeling.

The generated records are hypothetical training data, not real carrier records.
Run from the repository root: python src/generate_week4_hypothetical_data.py
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "week4_hypothetical_shipments.csv"
SEED = 20261016
N = 1200


def choose_vehicle(distance, weight, volume, rng):
    if weight > 900 or volume > 6.0:
        return "Truck"
    if weight > 25 or volume > 0.12 or distance > 500:
        return "Van" if (distance < 650 and rng.random() < 0.72) else "Truck"
    return "Bike" if (distance < 180 and rng.random() < 0.58) else "Van"


def main():
    rng = np.random.default_rng(SEED)
    regions = np.array(["North", "South", "East", "West", "Central"])
    region = rng.choice(regions, N, p=[0.23, 0.22, 0.17, 0.21, 0.17])
    distance = np.clip(rng.lognormal(mean=np.log(180), sigma=0.78, size=N), 10, 1100)
    weight = np.clip(rng.lognormal(mean=np.log(34), sigma=1.12, size=N), 0.5, 4200)
    volume = np.clip((weight * rng.uniform(0.0025, 0.008, N)) + rng.lognormal(-2.7, 0.9, N), 0.005, 28)
    vehicle = np.array([choose_vehicle(d, w, v, rng) for d, w, v in zip(distance, weight, volume)])
    priority = rng.choice(["Standard", "Express"], N, p=[0.77, 0.23])
    day = rng.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], N)
    traffic = rng.integers(1, 6, N)
    weather = rng.choice([0, 1, 2, 3], N, p=[0.48, 0.30, 0.16, 0.06])
    route_stops = np.clip(rng.poisson(4.2, N) + 1, 1, 16)
    warehouse_load = np.clip(rng.normal(68, 16, N), 25, 100)

    speed = {"Bike": 29.0, "Van": 47.0, "Truck": 43.0}
    region_delay = {"North": 0.45, "South": 0.15, "East": 0.85, "West": 0.28, "Central": 0.52}
    speed_values = np.array([speed[v] for v in vehicle])
    traffic_factor = 1 + 0.055 * (traffic - 1)
    weather_factor = 1 + 0.13 * weather
    warehouse_factor = 0.82 + 0.0045 * warehouse_load
    priority_adjustment = np.where(priority == "Express", -0.32, 0.0)
    noise = rng.normal(0, 0.55 + distance * 0.0014, N)
    delivery_time = (
        0.35
        + (distance / speed_values) * traffic_factor * weather_factor
        + route_stops * 0.19
        + warehouse_factor * 0.42
        + np.array([region_delay[r] for r in region])
        + priority_adjustment
        + noise
    )
    delivery_time = np.clip(delivery_time, 0.35, None)

    # Operational cost is simulated for optimization comparisons; it is not a real tariff.
    per_km = {"Bike": 5.8, "Van": 15.8, "Truck": 23.0}
    fixed = {"Bike": 75.0, "Van": 220.0, "Truck": 500.0}
    estimated_cost = np.array([per_km[v] for v in vehicle]) * distance + np.array([fixed[v] for v in vehicle]) + 0.25 * weight + 12 * volume

    dates = pd.Timestamp("2026-07-01") + pd.to_timedelta(rng.integers(0, 92, N), unit="D")
    df = pd.DataFrame({
        "shipment_id": [f"W4-{i:05d}" for i in range(1, N + 1)],
        "dispatch_date": dates.strftime("%Y-%m-%d"),
        "origin_region": region,
        "distance_km": np.round(distance, 2),
        "weight_kg": np.round(weight, 2),
        "volume_m3": np.round(volume, 3),
        "vehicle_type": vehicle,
        "route_stops": route_stops.astype(int),
        "traffic_index": traffic.astype(int),
        "weather_severity": weather.astype(int),
        "warehouse_load_pct": np.round(warehouse_load, 1),
        "priority": priority,
        "day_of_week": day,
        "delivery_time_hours": np.round(delivery_time, 3),
        "simulated_transport_cost_inr": np.round(estimated_cost, 2),
    })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Generated {len(df):,} hypothetical shipments: {OUT}")
    print(f"Target delivery-time range: {df.delivery_time_hours.min():.2f}-{df.delivery_time_hours.max():.2f} hours")
    print(f"Mean delivery time: {df.delivery_time_hours.mean():.2f} hours")


if __name__ == "__main__":
    main()
