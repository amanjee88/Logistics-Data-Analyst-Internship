"""Week 3 exploratory analysis for hypothetical logistics shipments.

Run from the repository root:
    python src/generate_week3_hypothetical_data.py
    python src/eda_logistics.py

Outputs summary CSV files under data/analysis/ and figures under reports/figures/.
All inferences describe only the included synthetic teaching dataset.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "analysis" / "week3_hypothetical_shipments.csv"
OUT = ROOT / "data" / "analysis"
FIG = ROOT / "reports" / "figures"

NUMERIC = ["distance_km", "shipment_weight_kg", "shipment_volume_m3", "transport_cost_inr", "delivery_time_hours", "delivery_delay_hours"]


def load_data(path: Path = DATA) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {path}. Run python src/generate_week3_hypothetical_data.py first.")
    df = pd.read_csv(path, parse_dates=["order_date", "promised_delivery_at", "delivered_at"])
    needed = {"shipment_id", "order_date", "promised_delivery_at", "delivered_at", "region", "distance_km", "shipment_weight_kg", "shipment_volume_m3", "transport_cost_inr", "vehicle_type", "first_attempt_status", "delivery_time_hours", "delivery_delay_hours", "on_time_delivery", "shipment_units"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {sorted(missing)}")
    if df["shipment_id"].duplicated().any():
        raise ValueError("shipment_id must be unique")
    if (df["distance_km"] <= 0).any() or (df["transport_cost_inr"] < 0).any():
        raise ValueError("Non-positive distance or negative cost found")
    df["on_time_delivery"] = df["on_time_delivery"].astype(str).str.lower().map({"true": True, "false": False, "1": True, "0": False})
    if df["on_time_delivery"].isna().any():
        raise ValueError("on_time_delivery includes unrecognized values")
    # Recompute derived metrics from timestamps to validate data consistency.
    computed_duration = (df["delivered_at"] - df["order_date"]).dt.total_seconds() / 3600
    computed_delay = (df["delivered_at"] - df["promised_delivery_at"]).dt.total_seconds() / 3600
    if not np.allclose(computed_duration, df["delivery_time_hours"], atol=0.02):
        raise ValueError("delivery_time_hours does not agree with timestamps")
    if not np.allclose(computed_delay, df["delivery_delay_hours"], atol=0.02):
        raise ValueError("delivery_delay_hours does not agree with timestamps")
    return df


def make_summaries(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    df = df.copy()
    df["cost_per_km_inr"] = df["transport_cost_inr"] / df["distance_km"]
    descriptive = df[NUMERIC].describe(percentiles=[0.25, 0.5, 0.75]).T
    descriptive.insert(0, "variable", descriptive.index)
    descriptive = descriptive.reset_index(drop=True).round(3)

    on_time = df.groupby("region", observed=True).agg(
        shipment_count=("shipment_id", "count"),
        on_time_rate=("on_time_delivery", "mean"),
        mean_delivery_hours=("delivery_time_hours", "mean"),
        mean_delay_hours=("delivery_delay_hours", "mean"),
        mean_cost_inr=("transport_cost_inr", "mean"),
        late_shipment_count=("on_time_delivery", lambda s: int((~s).sum())),
    ).reset_index()
    on_time["on_time_rate_pct"] = (on_time["on_time_rate"] * 100).round(1)
    on_time = on_time.drop(columns=["on_time_rate"]).round(2)

    vehicle = df.groupby("vehicle_type", observed=True).agg(
        shipment_count=("shipment_id", "count"),
        mean_distance_km=("distance_km", "mean"),
        mean_cost_inr=("transport_cost_inr", "mean"),
        mean_cost_per_km_inr=("cost_per_km_inr", "mean"),
        median_cost_inr=("transport_cost_inr", "median"),
        mean_delivery_hours=("delivery_time_hours", "mean"),
        on_time_rate_pct=("on_time_delivery", lambda s: 100 * s.mean()),
        first_attempt_success_pct=("first_attempt_status", lambda s: 100 * (s == "Success").mean()),
    ).reset_index().round(2)

    weekly = df.assign(order_week=df["order_date"].dt.to_period("W").astype(str)).groupby("order_week", observed=True).agg(
        shipment_count=("shipment_id", "count"),
        mean_cost_inr=("transport_cost_inr", "mean"),
        on_time_rate_pct=("on_time_delivery", lambda s: 100 * s.mean()),
        mean_delivery_hours=("delivery_time_hours", "mean"),
    ).reset_index().round(2)

    corr = df[NUMERIC].corr(method="pearson").round(3)
    quality = pd.DataFrame([
        ("Rows", len(df), "One record per synthetic shipment"),
        ("Columns", len(df.columns), "Shipment attributes and derived metrics"),
        ("Duplicate shipment IDs", int(df["shipment_id"].duplicated().sum()), "Must equal zero"),
        ("Missing cells", int(df.isna().sum().sum()), "Expected zero for this generated fixture"),
        ("Non-positive distance rows", int((df["distance_km"] <= 0).sum()), "Must equal zero"),
        ("Negative cost rows", int((df["transport_cost_inr"] < 0).sum()), "Must equal zero"),
        ("Timestamp duration mismatch rows", int((np.abs((df["delivered_at"] - df["order_date"]).dt.total_seconds()/3600 - df["delivery_time_hours"]) > 0.02).sum()), "Must equal zero"),
    ], columns=["check", "result", "interpretation"])
    return {"descriptive_statistics": descriptive, "region_kpis": on_time, "vehicle_kpis": vehicle, "weekly_kpis": weekly, "correlation_matrix": corr, "data_quality_checks": quality}


def make_figures(df: pd.DataFrame) -> list[Path]:
    FIG.mkdir(parents=True, exist_ok=True)
    sns.set_theme(context="notebook", style="whitegrid", font_scale=0.95)
    paths = []

    # 1 Delivery time distribution.
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    sns.histplot(data=df, x="delivery_time_hours", bins=24, kde=True, color="#4472C4", ax=ax)
    ax.axvline(df["delivery_time_hours"].median(), linestyle="--", linewidth=1.8, label=f"Median: {df['delivery_time_hours'].median():.1f} h")
    ax.set(title="Distribution of Delivery Time", xlabel="Order-to-delivery time (hours)", ylabel="Shipment count")
    ax.legend(frameon=True)
    fig.tight_layout()
    p = FIG / "week3_delivery_time_distribution.png"; fig.savefig(p, dpi=180, bbox_inches="tight"); plt.close(fig); paths.append(p)

    # 2 Cost vs distance colored by vehicle type.
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    sns.scatterplot(data=df, x="distance_km", y="transport_cost_inr", hue="vehicle_type", palette="deep", alpha=0.78, s=42, ax=ax)
    ax.set(title="Transport Cost vs Distance by Vehicle Type", xlabel="Distance (km)", ylabel="Transport cost (INR)")
    ax.legend(title="Vehicle", fontsize=8, frameon=True)
    fig.tight_layout()
    p = FIG / "week3_cost_vs_distance.png"; fig.savefig(p, dpi=180, bbox_inches="tight"); plt.close(fig); paths.append(p)

    # 3 Delay distribution by region.
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    order = df.groupby("region")["delivery_delay_hours"].median().sort_values().index
    sns.boxplot(data=df, x="region", y="delivery_delay_hours", order=order, color="#70AD47", ax=ax, showfliers=True)
    ax.axhline(0, linestyle="--", linewidth=1.5, label="Promise time threshold")
    ax.set(title="Delivery Delay by Region", xlabel="Region", ylabel="Hours versus promise (negative = early)")
    ax.legend(frameon=True)
    fig.tight_layout()
    p = FIG / "week3_delay_by_region.png"; fig.savefig(p, dpi=180, bbox_inches="tight"); plt.close(fig); paths.append(p)

    # 4 Average cost per shipment by vehicle.
    vs = df.groupby("vehicle_type", observed=True)["transport_cost_inr"].mean().sort_values(ascending=False).reset_index()
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    sns.barplot(data=vs, x="vehicle_type", y="transport_cost_inr", color="#4472C4", ax=ax)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.0f", padding=3, fontsize=8)
    ax.set(title="Mean Transport Cost by Vehicle Type", xlabel="Vehicle type", ylabel="Mean cost per shipment (INR)")
    ax.tick_params(axis="x", rotation=12)
    fig.tight_layout()
    p = FIG / "week3_mean_cost_by_vehicle.png"; fig.savefig(p, dpi=180, bbox_inches="tight"); plt.close(fig); paths.append(p)

    # 5 On-time rate by region.
    rs = df.groupby("region", observed=True)["on_time_delivery"].mean().mul(100).sort_values(ascending=False).reset_index(name="on_time_rate_pct")
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    sns.barplot(data=rs, x="region", y="on_time_rate_pct", color="#70AD47", ax=ax)
    ax.axhline(df["on_time_delivery"].mean()*100, linestyle="--", linewidth=1.5, label=f"Overall: {df['on_time_delivery'].mean()*100:.1f}%")
    ax.set_ylim(0, 100)
    ax.set(title="On-Time Delivery Rate by Region", xlabel="Region", ylabel="On-time deliveries (%)")
    ax.legend(frameon=True)
    fig.tight_layout()
    p = FIG / "week3_on_time_by_region.png"; fig.savefig(p, dpi=180, bbox_inches="tight"); plt.close(fig); paths.append(p)

    # 6 Correlation heatmap.
    fig, ax = plt.subplots(figsize=(8.4, 6.0))
    corr = df[NUMERIC].corr()
    sns.heatmap(corr, annot=True, fmt=".2f", center=0, cmap="vlag", vmin=-1, vmax=1, square=True, linewidths=0.4, ax=ax, cbar_kws={"shrink": 0.78})
    ax.set(title="Pearson Correlation of Key Numeric Variables")
    ax.tick_params(axis="x", rotation=35)
    ax.tick_params(axis="y", rotation=0)
    fig.tight_layout()
    p = FIG / "week3_correlation_heatmap.png"; fig.savefig(p, dpi=180, bbox_inches="tight"); plt.close(fig); paths.append(p)

    # 7 weekly volumes and on-time rate.
    wk = df.assign(order_week=df["order_date"].dt.to_period("W").astype(str)).groupby("order_week", observed=True).agg(shipment_count=("shipment_id", "count"), on_time_rate_pct=("on_time_delivery", lambda s: 100*s.mean())).reset_index()
    fig, ax1 = plt.subplots(figsize=(9.0, 4.8))
    ax1.bar(wk["order_week"], wk["shipment_count"], alpha=0.82, label="Shipment count")
    ax1.set_xlabel("Order week")
    ax1.set_ylabel("Shipment count")
    ax1.tick_params(axis="x", rotation=55, labelsize=7)
    ax2 = ax1.twinx()
    ax2.plot(wk["order_week"], wk["on_time_rate_pct"], marker="o", linewidth=1.8, label="On-time rate")
    ax2.set_ylabel("On-time delivery (%)")
    ax2.set_ylim(0, 100)
    ax1.set_title("Weekly Shipment Volume and On-Time Delivery")
    fig.tight_layout()
    p = FIG / "week3_weekly_volume_ontime.png"; fig.savefig(p, dpi=180, bbox_inches="tight"); plt.close(fig); paths.append(p)

    return paths


def run_eda() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_data()
    summary = make_summaries(df)
    for name, table in summary.items():
        dest = OUT / f"week3_{name}.csv"
        # Correlation matrix keeps index as labelled first column.
        table.to_csv(dest, index=(name == "correlation_matrix"))
    figure_paths = make_figures(df)
    overall = {
        "rows": int(len(df)),
        "on_time_rate_pct": round(float(df["on_time_delivery"].mean() * 100), 1),
        "mean_delivery_time_hours": round(float(df["delivery_time_hours"].mean()), 2),
        "median_delivery_time_hours": round(float(df["delivery_time_hours"].median()), 2),
        "mean_delay_hours": round(float(df["delivery_delay_hours"].mean()), 2),
        "late_shipments": int((~df["on_time_delivery"]).sum()),
        "mean_cost_inr": round(float(df["transport_cost_inr"].mean()), 2),
        "mean_cost_per_km_inr": round(float((df["transport_cost_inr"] / df["distance_km"]).mean()), 2),
        "median_cost_inr": round(float(df["transport_cost_inr"].median()), 2),
        "first_attempt_success_pct": round(float((df["first_attempt_status"] == "Success").mean() * 100), 1),
        "correlation_distance_cost": round(float(df[["distance_km", "transport_cost_inr"]].corr().iloc[0,1]), 3),
        "correlation_distance_delivery_time": round(float(df[["distance_km", "delivery_time_hours"]].corr().iloc[0,1]), 3),
        "largest_mean_region_delay": str(df.groupby("region")["delivery_delay_hours"].mean().idxmax()),
        "highest_mean_vehicle_cost": str(df.groupby("vehicle_type")["transport_cost_inr"].mean().idxmax()),
    }
    (OUT / "week3_overall_metrics.json").write_text(json.dumps(overall, indent=2), encoding="utf-8")
    print("WEEK 3 EDA COMPLETE (synthetic dataset)")
    print(json.dumps(overall, indent=2))
    print("Saved summary CSVs and figures:")
    for p in figure_paths:
        print(f"  {p.relative_to(ROOT)}")
    return overall


if __name__ == "__main__":
    run_eda()
