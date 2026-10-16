"""Train delivery-time regression models and create a what-if vehicle heuristic.

All results are based on synthetic teaching data. Run from repository root:
  python src/generate_week4_hypothetical_data.py
  python src/train_evaluate_optimize.py
"""
from pathlib import Path
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, KFold, cross_val_score, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "week4_hypothetical_shipments.csv"
OUT = ROOT / "data" / "analysis"
FIG = ROOT / "reports" / "figures"
SEED = 20261016
TARGET = "delivery_time_hours"
NUMERIC = ["distance_km", "weight_kg", "volume_m3", "route_stops", "traffic_index", "weather_severity", "warehouse_load_pct"]
CATEGORICAL = ["origin_region", "vehicle_type", "priority", "day_of_week"]
FEATURES = NUMERIC + CATEGORICAL
VEHICLES = ["Bike", "Van", "Truck"]
CAPACITY = {"Bike": (25.0, 0.12), "Van": (900.0, 6.0), "Truck": (5000.0, 30.0)}
COST_RATE = {"Bike": 5.8, "Van": 15.8, "Truck": 23.0}
COST_FIXED = {"Bike": 75.0, "Van": 220.0, "Truck": 500.0}
TIME_VALUE_INR_PER_HOUR = 85.0
SLA_HOURS = 12.0  # illustrative operating threshold for triage only


def build_preprocessor(scale_numeric=True):
    numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    numeric_pipe = Pipeline(numeric_steps)
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("numeric", numeric_pipe, NUMERIC),
        ("categorical", cat_pipe, CATEGORICAL),
    ])


def make_pipeline(estimator, scale_numeric=True):
    return Pipeline([("preprocessor", build_preprocessor(scale_numeric)), ("model", estimator)])


def metrics(y_true, y_pred):
    return {
        "MAE_hours": float(mean_absolute_error(y_true, y_pred)),
        "RMSE_hours": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "R2": float(r2_score(y_true, y_pred)),
    }


def vehicle_cost(vehicle, distance, weight, volume):
    return COST_RATE[vehicle] * distance + COST_FIXED[vehicle] + 0.25 * weight + 12.0 * volume


def feasible(vehicle, weight, volume):
    cap_w, cap_v = CAPACITY[vehicle]
    return (weight <= cap_w) and (volume <= cap_v)


def plot_save(path):
    plt.tight_layout()
    plt.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close()


def main():
    warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA)
    assert df[TARGET].notna().all() and (df[TARGET] > 0).all()
    assert df["shipment_id"].is_unique
    X = df[FEATURES].copy()
    y = df[TARGET].astype(float)
    X_train, X_test, y_train, y_test, train_idx, test_idx = train_test_split(
        X, y, df.index, test_size=0.20, random_state=SEED
    )
    cv = KFold(n_splits=5, shuffle=True, random_state=SEED)

    dummy = DummyRegressor(strategy="median")
    dummy.fit(X_train, y_train)
    dummy_pred = dummy.predict(X_test)

    linear = make_pipeline(LinearRegression(), scale_numeric=True)
    linear.fit(X_train, y_train)
    linear_pred = linear.predict(X_test)
    linear_cv = -cross_val_score(linear, X_train, y_train, cv=cv, scoring="neg_mean_absolute_error", n_jobs=-1)

    # Use an untuned Random Forest for apples-to-apples 5-fold CV comparison.
    # The grid-searched RF is assessed on the untouched test set afterward.
    default_rf = make_pipeline(RandomForestRegressor(n_estimators=150, random_state=SEED, n_jobs=-1), scale_numeric=False)
    default_rf_cv = -cross_val_score(default_rf, X_train, y_train, cv=cv, scoring="neg_mean_absolute_error", n_jobs=-1)

    rf_pipeline = make_pipeline(RandomForestRegressor(random_state=SEED, n_jobs=-1), scale_numeric=False)
    param_grid = {
        "model__n_estimators": [120, 220],
        "model__max_depth": [None, 18],
        "model__min_samples_leaf": [1, 3],
    }
    search = GridSearchCV(
        rf_pipeline, param_grid=param_grid, scoring="neg_mean_absolute_error",
        cv=3, n_jobs=-1, refit=True, return_train_score=False
    )
    search.fit(X_train, y_train)
    best_rf = search.best_estimator_
    rf_pred = best_rf.predict(X_test)

    rows = []
    for name, pred in [("Median baseline", dummy_pred), ("Linear regression", linear_pred), ("Tuned random forest", rf_pred)]:
        rows.append({"model": name, **metrics(y_test, pred)})
    model_metrics = pd.DataFrame(rows)
    model_metrics.to_csv(OUT / "week4_model_metrics.csv", index=False)

    dummy_cv = -cross_val_score(DummyRegressor(strategy="median"), X_train, y_train, cv=cv, scoring="neg_mean_absolute_error", n_jobs=-1)
    cv_metrics = pd.DataFrame([
        {"model": "Median baseline", "cv_folds": 5, "mean_cv_mae_hours": float(dummy_cv.mean()), "std_cv_mae_hours": float(dummy_cv.std())},
        {"model": "Linear regression", "cv_folds": 5, "mean_cv_mae_hours": float(linear_cv.mean()), "std_cv_mae_hours": float(linear_cv.std())},
        {"model": "Random forest (default; 150 trees)", "cv_folds": 5, "mean_cv_mae_hours": float(default_rf_cv.mean()), "std_cv_mae_hours": float(default_rf_cv.std())},
    ])
    cv_metrics.to_csv(OUT / "week4_cv_metrics.csv", index=False)
    pd.DataFrame(search.cv_results_).sort_values("rank_test_score").to_csv(OUT / "week4_hyperparameter_search.csv", index=False)

    # Select between LR and default RF using training-fold CV only, before reading test scores.
    best_name = cv_metrics[cv_metrics.model.isin(["Linear regression", "Random forest (default; 150 trees)"])].sort_values("mean_cv_mae_hours").iloc[0]["model"]
    final_model = linear if best_name == "Linear regression" else default_rf
    final_pred = linear_pred if best_name == "Linear regression" else default_rf.predict(X_test)
    y_test_series = y_test.reset_index(drop=True)
    test_predictions = pd.DataFrame({
        "shipment_id": df.loc[test_idx, "shipment_id"].to_numpy(),
        "origin_region": df.loc[test_idx, "origin_region"].to_numpy(),
        "vehicle_type": df.loc[test_idx, "vehicle_type"].to_numpy(),
        "actual_delivery_time_hours": y_test.to_numpy(),
        "predicted_delivery_time_hours": final_pred,
    })
    test_predictions["residual_hours"] = test_predictions.actual_delivery_time_hours - test_predictions.predicted_delivery_time_hours
    test_predictions["predicted_sla_exception"] = test_predictions.predicted_delivery_time_hours > SLA_HOURS
    test_predictions.to_csv(OUT / "week4_test_predictions.csv", index=False)

    # Feature importance for Random Forest is documented even if Linear Regression
    # happens to edge it out; the report clearly indicates which model was selected.
    rf_pre = best_rf.named_steps["preprocessor"]
    rf_model = best_rf.named_steps["model"]
    feat_names = rf_pre.get_feature_names_out()
    importance = pd.DataFrame({"feature": feat_names, "importance": rf_model.feature_importances_}).sort_values("importance", ascending=False)
    importance.to_csv(OUT / "week4_feature_importance.csv", index=False)

    # Capacity-constrained what-if vehicle choice. Score = estimated cost + time value * predicted time.
    # This is a transparent heuristic, not an industrial route solver or real savings estimate.
    holdout_indices = X_test.index.to_list()
    current_pred_holdout = final_model.predict(X_test)
    rec_rows = []
    for position, i in enumerate(holdout_indices):
        row = df.loc[i]
        feasible_candidates = [v for v in VEHICLES if feasible(v, row.weight_kg, row.volume_m3)]
        if not feasible_candidates:
            feasible_candidates = ["Truck"]  # all generated shipments are within truck capacity, fallback documented
        candidate_rows = []
        for v in feasible_candidates:
            cand = X.loc[[i]].copy()
            cand.loc[cand.index[0], "vehicle_type"] = v
            pred_h = float(final_model.predict(cand)[0])
            cost = float(vehicle_cost(v, row.distance_km, row.weight_kg, row.volume_m3))
            score = cost + TIME_VALUE_INR_PER_HOUR * pred_h
            candidate_rows.append((score, v, pred_h, cost))
        best = min(candidate_rows, key=lambda z: z[0])
        curr_v = str(row.vehicle_type)
        curr_pred = float(current_pred_holdout[position])
        curr_cost = float(vehicle_cost(curr_v, row.distance_km, row.weight_kg, row.volume_m3))
        curr_score = curr_cost + TIME_VALUE_INR_PER_HOUR * curr_pred
        rec_rows.append({
            "shipment_id": row.shipment_id,
            "current_vehicle": curr_v,
            "recommended_vehicle": best[1],
            "weight_kg": row.weight_kg,
            "volume_m3": row.volume_m3,
            "distance_km": row.distance_km,
            "predicted_hours_current": curr_pred,
            "predicted_hours_recommended": best[2],
            "estimated_cost_current_inr": curr_cost,
            "estimated_cost_recommended_inr": best[3],
            "objective_score_current": curr_score,
            "objective_score_recommended": best[0],
            "objective_score_improvement_pct": (curr_score - best[0]) / curr_score * 100 if curr_score else 0.0,
            "decision_note": "Capacity-constrained synthetic what-if; validate with dispatch rules before use",
        })
    recs = pd.DataFrame(rec_rows)
    recs.to_csv(OUT / "week4_vehicle_assignment_recommendations.csv", index=False)
    changed = recs.current_vehicle != recs.recommended_vehicle
    opt_summary = {
        "n_shipments": int(len(recs)),
        "evaluation_population": "Untouched 20% test split; recommendations use features only and are not evaluated as real operational savings.",
        "shipments_with_vehicle_change": int(changed.sum()),
        "vehicle_change_share_pct": float(changed.mean() * 100),
        "mean_predicted_hours_current": float(recs.predicted_hours_current.mean()),
        "mean_predicted_hours_recommended": float(recs.predicted_hours_recommended.mean()),
        "mean_estimated_cost_current_inr": float(recs.estimated_cost_current_inr.mean()),
        "mean_estimated_cost_recommended_inr": float(recs.estimated_cost_recommended_inr.mean()),
        "mean_objective_score_improvement_pct": float(recs.objective_score_improvement_pct.mean()),
        "time_value_inr_per_hour": TIME_VALUE_INR_PER_HOUR,
        "sla_triage_threshold_hours": SLA_HOURS,
        "note": "All costs, model estimates, assignments, and improvements are synthetic scenario outputs; not measured operational savings.",
    }
    (OUT / "week4_optimization_summary.json").write_text(json.dumps(opt_summary, indent=2), encoding="utf-8")

    # Data quality summary
    quality = pd.DataFrame([
        ["Rows", int(len(df)), "Expected 1200 generated records"],
        ["Unique shipment IDs", int(df.shipment_id.nunique()), "Must equal row count"],
        ["Missing cells", int(df[FEATURES + [TARGET]].isna().sum().sum()), "Required modeled columns must be complete"],
        ["Non-positive delivery times", int((df[TARGET] <= 0).sum()), "Target values must be positive"],
        ["Rows above 12-hour triage threshold", int((df[TARGET] > SLA_HOURS).sum()), "Illustrative business-rule reference only"],
    ], columns=["check", "value", "interpretation"])
    quality.to_csv(OUT / "week4_data_quality_checks.csv", index=False)

    # Visual 1: actual vs predicted
    plt.figure(figsize=(7.0, 5.0))
    plt.scatter(y_test, final_pred, alpha=0.65, s=20)
    lim = [min(float(y_test.min()), float(np.min(final_pred))), max(float(y_test.max()), float(np.max(final_pred)))]
    plt.plot(lim, lim, linestyle="--", linewidth=1.5)
    plt.xlabel("Actual delivery time (hours)")
    plt.ylabel("Predicted delivery time (hours)")
    plt.title(f"Actual vs Predicted — {best_name}")
    plot_save(FIG / "week4_actual_vs_predicted.png")

    # Visual 2: residual distribution
    residual = y_test.to_numpy() - final_pred
    plt.figure(figsize=(7.0, 4.8))
    plt.hist(residual, bins=28, edgecolor="white")
    plt.axvline(0, linestyle="--", linewidth=1.5)
    plt.xlabel("Residual (actual - predicted), hours")
    plt.ylabel("Shipment count")
    plt.title("Holdout Residual Distribution")
    plot_save(FIG / "week4_residual_distribution.png")

    # Visual 3: metric comparison
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.6))
    names = model_metrics.model.tolist()
    axes[0].bar(names, model_metrics.MAE_hours)
    axes[0].set_title("Mean Absolute Error (lower is better)")
    axes[0].set_ylabel("Hours")
    axes[0].tick_params(axis="x", rotation=18)
    axes[1].bar(names, model_metrics.RMSE_hours)
    axes[1].set_title("Root Mean Squared Error (lower is better)")
    axes[1].set_ylabel("Hours")
    axes[1].tick_params(axis="x", rotation=18)
    plot_save(FIG / "week4_model_comparison.png")

    # Visual 4: feature importance
    top = importance.head(12).sort_values("importance")
    plt.figure(figsize=(8.0, 5.6))
    plt.barh(top.feature.str.replace("numeric__", "", regex=False).str.replace("categorical__", "", regex=False), top.importance)
    plt.xlabel("Random Forest feature importance")
    plt.title("Top Predictive Features (model-specific, not causal effects)")
    plot_save(FIG / "week4_feature_importance.png")

    # Visual 5: estimated trade-off
    compare = pd.DataFrame({
        "measure": ["Predicted delivery time (h)", "Estimated cost (₹)"],
        "Current": [recs.predicted_hours_current.mean(), recs.estimated_cost_current_inr.mean()],
        "Recommended": [recs.predicted_hours_recommended.mean(), recs.estimated_cost_recommended_inr.mean()],
    })
    # Separate axes/plots because the measures have different units.
    plt.figure(figsize=(6.6, 4.5))
    plt.bar(["Current", "Recommended"], [compare.loc[0, "Current"], compare.loc[0, "Recommended"]])
    plt.ylabel("Predicted hours")
    plt.title("What-if Mean Predicted Delivery Time")
    plot_save(FIG / "week4_optimization_time_comparison.png")
    plt.figure(figsize=(6.6, 4.5))
    plt.bar(["Current", "Recommended"], [compare.loc[1, "Current"], compare.loc[1, "Recommended"]])
    plt.ylabel("Estimated INR per shipment")
    plt.title("What-if Mean Estimated Shipment Cost")
    plot_save(FIG / "week4_optimization_cost_comparison.png")

    # Visual 6: model holdout MAE by region
    pred_df = test_predictions.copy()
    pred_df["abs_error_hours"] = pred_df.residual_hours.abs()
    region_mae = pred_df.groupby("origin_region", as_index=False).agg(n_test_shipments=("shipment_id", "count"), mae_hours=("abs_error_hours", "mean"))
    region_mae.to_csv(OUT / "week4_test_error_by_region.csv", index=False)
    plt.figure(figsize=(7.0, 4.6))
    plt.bar(region_mae.origin_region, region_mae.mae_hours)
    plt.xlabel("Origin region")
    plt.ylabel("Mean absolute error (hours)")
    plt.title("Holdout Prediction Error by Region")
    plot_save(FIG / "week4_test_error_by_region.png")

    # Save compact reproducibility metadata for report generation.
    selected_metrics = model_metrics.loc[model_metrics.model == best_name].iloc[0].to_dict()
    metadata = {
        "rows": int(len(df)), "train_rows": int(len(X_train)), "test_rows": int(len(X_test)),
        "seed": SEED, "selected_model": best_name, "selected_test_metrics": selected_metrics,
        "best_random_forest_params": {k.replace("model__", ""): (None if pd.isna(v) else v) for k, v in search.best_params_.items()},
        "random_forest_best_grid_cv_mae_hours": float(-search.best_score_),
        "model_selection_rule": "Lowest five-fold training cross-validation MAE among Linear Regression and default Random Forest; test set not used for model selection.",
        "top_features": importance.head(5).to_dict(orient="records"),
        "optimization": opt_summary,
        "caveats": [
            "All 1200 records are synthetic; no real operations data are included.",
            "The random train/test split is appropriate only for this simulated cross-sectional exercise; production time-dependent data should use a chronological split.",
            "Random Forest impurity importance is not causal evidence.",
            "Vehicle recommendations are a scenario-based capacity and score heuristic, not a route sequence optimizer.",
        ],
    }
    (OUT / "week4_modeling_summary.json").write_text(json.dumps(metadata, indent=2, default=float), encoding="utf-8")

    print("Model holdout metrics:\n", model_metrics.to_string(index=False))
    print("CV metrics:\n", cv_metrics.to_string(index=False))
    print("Selected model:", best_name)
    print("Best RF params:", search.best_params_)
    print("Optimization summary:", json.dumps(opt_summary, indent=2))
    print(f"Saved model outputs to {OUT} and figures to {FIG}")


if __name__ == "__main__":
    main()
