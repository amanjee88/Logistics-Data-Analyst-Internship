"""Reproducible Week 2 cleaning pipeline for synthetic logistics training data.

Run from repository root:
    python src/cleaning_pipeline.py

Outputs:
    data/processed/cleaned_shipments.csv
    data/processed/records_for_manual_review.csv
    data/processed/cleaning_audit.csv

The input is synthetic practice data; results are not real company statistics.
"""
from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "raw" / "raw_shipments_simulated.csv"
OUTDIR = ROOT / "data" / "processed"
DATE_COLS = ["order_date", "promised_delivery_at", "delivered_at"]
NUMERIC_COLS = ["distance_km", "shipment_weight_kg", "transport_cost_inr"]
REQUIRED_COLS = ["shipment_id", "order_date", "promised_delivery_at", "region"]

REGION_MAP = {
    "n": "North", "north": "North", "north region": "North",
    "s": "South", "south": "South", "south region": "South",
    "e": "East", "east": "East", "east region": "East",
    "w": "West", "west": "West", "west region": "West",
    "c": "Central", "central": "Central", "cntral": "Central", "central region": "Central",
}
VEHICLE_MAP = {
    "mini truck": "Mini-truck", "mini-truck": "Mini-truck", "minitruck": "Mini-truck",
    "van": "Van", "two wheeler": "Two-wheeler", "two-wheeler": "Two-wheeler",
    "motorcycle": "Two-wheeler", "truck": "Truck",
}
STATUS_MAP = {
    "success": "Success", "successful": "Success", "succeeded": "Success", "yes": "Success", "y": "Success", "1": "Success",
    "failed": "Failed", "fail": "Failed", "failure": "Failed", "no": "Failed", "n": "Failed", "0": "Failed",
    "pending": "Pending", "unknown": "Unknown", "": "Unknown",
}


def clean_text(value: object) -> str:
    """Strip surrounding whitespace; preserve empty values as empty strings."""
    if pd.isna(value):
        return ""
    return str(value).replace("\u00a0", " ").strip()


def parse_numeric(series: pd.Series) -> pd.Series:
    """Parse numeric values including currency symbols and comma separators."""
    text = series.map(clean_text)
    text = text.str.replace(",", "", regex=False)
    text = text.str.replace(r"[^0-9.\-]", "", regex=True)
    return pd.to_numeric(text.replace("", pd.NA), errors="coerce")


def parse_dates(series: pd.Series) -> pd.Series:
    """Parse common mixed date representations into datetime values."""
    text = series.map(clean_text).replace({"": pd.NA, "—": pd.NA, "-": pd.NA})
    # pandas >=2.0 supports format='mixed' for files containing multiple date formats.
    return pd.to_datetime(text, format="mixed", errors="coerce")


def iqr_outlier_mask(series: pd.Series) -> pd.Series:
    """Flag non-missing observations outside Tukey's 1.5*IQR fences."""
    valid = series.dropna()
    if len(valid) < 4:
        return pd.Series(False, index=series.index)
    q1, q3 = valid.quantile([0.25, 0.75])
    iqr = q3 - q1
    if iqr == 0:
        return pd.Series(False, index=series.index)
    return series.notna() & ((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr))


def run_pipeline(input_path: Path = INPUT, output_dir: Path = OUTDIR) -> dict:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. Run python src/create_week2_fixture.py first.")
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    raw_rows = len(raw)
    exact_dup_mask = raw.duplicated(keep="first")
    exact_duplicates_removed = int(exact_dup_mask.sum())
    df = raw.loc[~exact_dup_mask].copy().reset_index(drop=True)

    # Trim whitespace consistently in all text fields.
    for col in df.columns:
        df[col] = df[col].map(clean_text)

    # Normalize dates, retaining missing/unparseable values for downstream decisions.
    original_delivery_text = df["delivered_at"].copy()
    for col in DATE_COLS:
        df[col] = parse_dates(df[col])
    df["delivered_at_unparseable"] = original_delivery_text.ne("") & df["delivered_at"].isna()

    # Normalize numeric columns; invalid strings become missing rather than guessed values.
    for col in NUMERIC_COLS:
        df[col] = parse_numeric(df[col])

    # Normalize controlled vocabularies while keeping unknown categories visible.
    df["shipment_id"] = df["shipment_id"].str.upper().str.strip()
    df["region_normalized"] = df["region"].str.casefold().map(REGION_MAP)
    df["region"] = df["region_normalized"].fillna(df["region"].str.title())
    df.loc[df["region"].str.strip().eq(""), "region"] = ""
    df["vehicle_type"] = df["vehicle_type"].str.casefold().map(VEHICLE_MAP).fillna(df["vehicle_type"].str.title())
    status_key = df["first_attempt_status"].str.casefold().str.strip()
    df["first_attempt_status"] = status_key.map(STATUS_MAP).fillna("Unknown")

    # Mark duplicate business keys after exact duplicates have been removed.
    duplicate_id_mask = df["shipment_id"].ne("") & df["shipment_id"].duplicated(keep=False)
    review_reasons = [[] for _ in range(len(df))]
    for i, dup in enumerate(duplicate_id_mask.tolist()):
        if dup:
            review_reasons[i].append("Conflicting duplicate shipment_id; verify source system before selecting a record")
    for col, label in [("order_date", "Missing or unparseable order_date"), ("promised_delivery_at", "Missing or unparseable promised_delivery_at")]:
        bad = df[col].isna()
        for i in df.index[bad]:
            review_reasons[i].append(label)
    bad_id = df["shipment_id"].eq("")
    for i in df.index[bad_id]:
        review_reasons[i].append("Missing shipment_id")
    bad_region = df["region"].str.strip().eq("")
    for i in df.index[bad_region]:
        review_reasons[i].append("Missing region; source correction required")

    review_mask = pd.Series([bool(items) for items in review_reasons], index=df.index)
    review = df.loc[review_mask].copy()
    review["review_reason"] = ["; ".join(review_reasons[i]) for i in review.index]
    review.to_csv(output_dir / "records_for_manual_review.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    clean = df.loc[~review_mask].copy().reset_index(drop=True)

    # Physical/business-rule validation: invalid nonpositive numeric values become missing.
    distance_invalid = clean["distance_km"].notna() & (clean["distance_km"] <= 0)
    weight_invalid = clean["shipment_weight_kg"].notna() & (clean["shipment_weight_kg"] <= 0)
    cost_invalid = clean["transport_cost_inr"].notna() & (clean["transport_cost_inr"] < 0)
    clean.loc[distance_invalid, "distance_km"] = pd.NA
    clean.loc[weight_invalid, "shipment_weight_kg"] = pd.NA
    clean.loc[cost_invalid, "transport_cost_inr"] = pd.NA

    # Flag statistical outliers before imputation; keep them for review rather than silently deleting.
    outlier_counts = {}
    for col in NUMERIC_COLS:
        mask = iqr_outlier_mask(clean[col])
        flag_col = f"outlier_{col}"
        clean[flag_col] = mask
        outlier_counts[col] = int(mask.sum())

    # Preserve the reason each imputed numeric value was missing/invalid.
    clean["distance_was_imputed"] = clean["distance_km"].isna()
    clean["weight_was_imputed"] = clean["shipment_weight_kg"].isna()
    clean["cost_was_imputed"] = clean["transport_cost_inr"].isna()

    # Group medians retain broad regional/vehicle context; global median is a fallback.
    region_distance_median = clean.groupby("region")["distance_km"].transform("median")
    global_distance_median = clean["distance_km"].median()
    clean["distance_km"] = clean["distance_km"].fillna(region_distance_median).fillna(global_distance_median)
    global_weight_median = clean["shipment_weight_kg"].median()
    clean["shipment_weight_kg"] = clean["shipment_weight_kg"].fillna(global_weight_median)
    vehicle_cost_median = clean.groupby("vehicle_type")["transport_cost_inr"].transform("median")
    global_cost_median = clean["transport_cost_inr"].median()
    clean["transport_cost_inr"] = clean["transport_cost_inr"].fillna(vehicle_cost_median).fillna(global_cost_median)

    # An undelivered shipment remains undelivered; do not impute its actual delivery time.
    clean["delivered_at_missing"] = clean["delivered_at"].isna()
    chronology_issue = clean["delivered_at"].notna() & (clean["delivered_at"] < clean["order_date"])
    clean["invalid_delivery_chronology"] = chronology_issue
    clean.loc[chronology_issue, "delivered_at"] = pd.NaT
    clean.loc[chronology_issue, "delivered_at_missing"] = True

    # Keep the report-facing clean data compact, transparent, and correctly typed.
    ordered_cols = [
        "shipment_id", "order_date", "promised_delivery_at", "delivered_at", "region", "distance_km",
        "shipment_weight_kg", "transport_cost_inr", "vehicle_type", "first_attempt_status",
        "distance_was_imputed", "weight_was_imputed", "cost_was_imputed",
        "outlier_distance_km", "outlier_shipment_weight_kg", "outlier_transport_cost_inr",
        "delivered_at_missing", "invalid_delivery_chronology", "delivered_at_unparseable",
    ]
    clean = clean[ordered_cols].sort_values("shipment_id").reset_index(drop=True)
    clean.to_csv(output_dir / "cleaned_shipments.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")

    # Re-read the raw file for a transparent raw missingness audit (before normalization).
    raw_read = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    missing_like_tokens = {"", "na", "n/a", "nan", "null", "none", "unknown", "—", "-"}
    raw_missing_total = int(raw_read.apply(lambda s: s.astype(str).str.strip().str.casefold().isin(missing_like_tokens).sum()).sum())
    audit_rows = [
        ("Raw synthetic rows loaded", raw_rows, "Rows in raw practice fixture before any cleaning"),
        ("Exact duplicate rows removed", exact_duplicates_removed, "Exact row duplicates removed automatically"),
        ("Rows routed to manual review", int(review_mask.sum()), "Conflicting business keys or required-field issues; not silently guessed"),
        ("Clean rows exported", len(clean), "Rows retained in cleaned teaching dataset"),
        ("Missing-like raw cells detected", raw_missing_total, "Counts blank/NA/unknown-style tokens in the raw fixture; not a count of all business errors"),
        ("Distance values imputed", int(clean["distance_was_imputed"].sum()), "Regional median, with overall median fallback"),
        ("Weight values imputed", int(clean["weight_was_imputed"].sum()), "Overall median"),
        ("Transport cost values imputed", int(clean["cost_was_imputed"].sum()), "Vehicle-type median, with overall median fallback"),
        ("Delivery timestamps missing or invalid after checks", int(clean["delivered_at_missing"].sum()), "Retained as missing; no fabricated delivery timestamp"),
        ("Invalid delivery chronology flags", int(clean["invalid_delivery_chronology"].sum()), "Delivery timestamp before order timestamp was cleared and flagged"),
        ("Unparseable delivered_at values", int(clean["delivered_at_unparseable"].sum()), "Optional timestamp could not be parsed; treated as missing and flagged"),
    ]
    for col, count in outlier_counts.items():
        audit_rows.append((f"IQR outliers flagged: {col}", count, "Flagged for investigation; values retained, not automatically deleted"))
    audit = pd.DataFrame(audit_rows, columns=["audit_item", "count", "interpretation"])
    audit.to_csv(output_dir / "cleaning_audit.csv", index=False)

    summary = {
        "raw_rows": raw_rows,
        "exact_duplicates_removed": exact_duplicates_removed,
        "rows_for_manual_review": int(review_mask.sum()),
        "clean_rows": len(clean),
        "imputed_distance": int(clean["distance_was_imputed"].sum()),
        "imputed_weight": int(clean["weight_was_imputed"].sum()),
        "imputed_cost": int(clean["cost_was_imputed"].sum()),
        "outlier_counts": outlier_counts,
    }
    print("WEEK 2 CLEANING PIPELINE — synthetic training data only")
    for key, value in summary.items():
        print(f"{key}: {value}")
    print(f"\nOutputs saved under: {output_dir.relative_to(ROOT)}")
    print("Outliers are flagged rather than automatically deleted; records with ambiguous required fields/duplicate keys are routed to manual review.")
    return summary


if __name__ == "__main__":
    run_pipeline()
