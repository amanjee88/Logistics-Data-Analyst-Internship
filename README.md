# Logistics Data Analysis — Week 1

**Portfolio-ready companion repository for the YuvaIntern Logistics Data Analyst task.**

## Project status
Week 1 is a strategy and planning deliverable. This repository contains the planning report, a submission description, and a starter Python KPI framework. It does **not** claim that a real logistics company was analysed, and it does not contain real customer or courier records.

## Scenario
A fictional e-commerce logistics operator serving an urban Indian market wants to improve on-time delivery, understand delivery delays, monitor transportation cost, and identify operational bottlenecks.

## Repository structure
- `reports/Week_1_Strategic_Planning_and_Data_Exploration.docx` — report for the Week 1 upload
- `submission/Week_1_Submission_Description.txt` — 200+ word description to paste into the portal
- `src/kpi_framework.py` — example KPI calculations and data-quality checks
- `data/sample_shipments_simulated.csv` — generated synthetic fixture solely for verifying that the starter code runs
- `requirements.txt` — minimal dependencies

## Run the starter code
Use Python 3.10+ from the repository root:

```bash
pip install -r requirements.txt
python src/kpi_framework.py
```

The console values produced by the starter script are **synthetic demonstration outputs only**. Do not describe them as real delivery statistics. For a real analysis, replace the fixture only with a properly licensed, documented dataset and update assumptions, definitions, and reporting dates.

## Planned analytical workflow
1. Define business questions, KPIs, data dictionary, and reporting scope.
2. Obtain and document lawful, relevant source data.
3. Validate schema, types, duplicate shipment identifiers, timestamps, units, and missingness.
4. Explore distributions and segment differences by region, vehicle, distance, and shipment characteristics.
5. Report interpretable delivery and cost KPIs.
6. In later project phases, evaluate prediction and optimization methods only if data quality and sample size support them.

## KPI definitions to confirm with stakeholders
- On-time delivery rate: shipments delivered no later than their promise time divided by the explicitly agreed eligible shipment population.
- Average delivery time versus promise: mean of actual delivery timestamp minus promised delivery timestamp among delivered shipments; a negative value indicates early delivery.
- Average late-delivery duration: mean positive lateness among delivered late shipments.
- Transportation cost per shipment: total eligible recorded transport cost divided by shipments with valid cost records.
- First-attempt success rate: shipments successful on first attempt divided by shipments with a valid first-attempt outcome.

Before production use, confirm how pending shipments, cancellations, rescheduled promises, reporting windows, and missing values are handled. The starter code uses a simplified snapshot rule and is a teaching example, not a production KPI specification.

## Research references
- World Bank, Logistics Performance Index 2023: https://www.worldbank.org/en/news/press-release/2023/04/21/world-bank-releases-logistics-performance-index-2023
- Government of India portal, MoRTH annual reports: https://www.india.gov.in/category/driving-transport/subcategory/roads-road-transport/details/annual-reports-of-ministry-of-road-transport-and-highways
- OpenStreetMap: https://www.openstreetmap.org/about (use required attribution and comply with applicable terms)
- Google OR-Tools, Vehicle Routing Problem: https://developers.google.com/optimization/routing/vrp

## Notes
- Public contextual sources support the rationale, not shipment-level factual claims.
- This plan does not establish causal claims, actual savings, or model accuracy.
- GitHub URL field in the portal should be populated only after the project is published and the URL has been checked.

## Week 2 — Data Collection, Cleaning, and Preprocessing

### Public reference vs. processed training data
This phase uses the public **DataCo SMART SUPPLY CHAIN FOR BIG DATA ANALYSIS** dataset as a domain and schema reference: [Mendeley Data, Version 5](https://data.mendeley.com/datasets/8gx2fvg2k6/5), DOI [10.17632/8gx2fvg2k6.5](https://doi.org/10.17632/8gx2fvg2k6.5). The original public dataset is **not** included in this repository and was **not** processed by the Week 2 script. For a lightweight, reproducible exercise, `data/raw/raw_shipments_simulated.csv` is a deliberately imperfect synthetic fixture created for this project.

### Week 2 files
- `reports/Week_2_Data_Collection_Cleaning_and_Preprocessing.docx` — full report with methodology, workflow diagram, results, references and audit appendix
- `submission/Week_2_Submission_Description.txt` — portal description (336 words; above the required 200-word minimum)
- `data/raw/raw_shipments_simulated.csv` — intentionally imperfect synthetic input
- `data/processed/cleaned_shipments.csv` — cleaned teaching dataset with imputation/outlier flags
- `data/processed/records_for_manual_review.csv` — conflicting duplicate keys and records missing required fields, with reasons
- `data/processed/cleaning_audit.csv` — output counts and treatment explanations
- `src/create_week2_fixture.py` — deterministic creation of the synthetic fixture from the existing Week 1 example
- `src/cleaning_pipeline.py` — reproducible pandas cleaning pipeline
- `tests/test_cleaning_pipeline.py` — basic checks for keys, numeric rules and output files
- `reports/figures/` — workflow diagram and executed row-count chart used in the report

### Run the Week 2 pipeline
Use Python 3.10+ from the repository root:

```bash
pip install -r requirements.txt
python src/create_week2_fixture.py
python src/cleaning_pipeline.py
python tests/test_cleaning_pipeline.py
```

The included fixture intentionally contains 38 synthetic input rows. The current run removes one exact duplicate row, sends five rows to manual review (including the two records with a conflicting shipment ID), and exports 32 cleaned teaching rows. Numeric values imputed by the pipeline have Boolean flags. Statistical outliers are flagged and retained for investigation; they are not automatically deleted. Missing or invalid actual delivery timestamps are left missing rather than fabricated. These counts are synthetic demonstration outputs only.

### Cleaning decisions and limitations
- Exact duplicate rows are removed; records sharing a conflicting shipment business key are routed to review rather than selecting a winner without source evidence.
- Missing or invalid required identifiers, order dates, promised timestamps or region values are routed to manual review.
- Non-positive distance/weight and negative cost are treated as invalid numeric measurements, then imputed using documented medians and tracked with flags.
- Distance is imputed using region median (overall median fallback), weight using overall median, and transportation cost using vehicle-type median (overall median fallback).
- IQR outliers are only screening flags. A domain expert should decide whether a flagged value is erroneous or a genuine exceptional shipment.
- Imputation rules are demonstrative, not production defaults. Validate them against data-owner definitions and downstream KPI sensitivity before using real operational data.

## Reference sources
- Constante, F., Silva, F., & Pereira, A. (2019). *DataCo SMART SUPPLY CHAIN FOR BIG DATA ANALYSIS* (Version 5). Mendeley Data. https://doi.org/10.17632/8gx2fvg2k6.5
- World Bank. (2023). *World Bank releases Logistics Performance Index 2023*. https://www.worldbank.org/en/news/press-release/2023/04/21/world-bank-releases-logistics-performance-index-2023
- pandas documentation: https://pandas.pydata.org/docs/

## Week 3 — Advanced Data Analysis and Visualization in Logistics

### Data transparency
Week 3 uses a deterministic, 300-row **synthetic/hypothetical** shipment dataset created locally with a fixed random seed. The file is designed for EDA practice and is not a download from DataCo or a record of any real carrier. The DataCo and World Bank references provide domain context only. Findings, KPI values, charts and correlations below describe only the generated training sample.

### Week 3 deliverables
- `reports/Week_3_Advanced_Data_Analysis_and_Visualization.docx` — formatted report with seven embedded charts, interpretation, descriptive statistics, segment comparisons, recommendations, limitations and references.
- `submission/Week_3_Submission_Description.txt` — detailed portal description exceeding the 200-word minimum.
- `src/generate_week3_hypothetical_data.py` — reproducible 300-row synthetic dataset generator (seed `20261016`).
- `src/eda_logistics.py` — timestamp validation, KPI summaries, descriptive statistics, correlation matrix and seven figures.
- `data/analysis/week3_hypothetical_shipments.csv` — synthetic shipment-level analysis data.
- `data/analysis/week3_descriptive_statistics.csv`, `week3_region_kpis.csv`, `week3_vehicle_kpis.csv`, `week3_weekly_kpis.csv`, `week3_correlation_matrix.csv`, `week3_data_quality_checks.csv`, `week3_overall_metrics.json` — generated analytical outputs.
- `reports/figures/week3_*.png` — individual charts embedded in the report.
- `tests/test_eda_logistics.py` — automated integrity tests for shipment keys, data ranges, timestamp-derived metrics and grouped summaries.

### Run the Week 3 analysis
Run from the repository root with Python 3.10+:

```bash
pip install -r requirements.txt
python src/generate_week3_hypothetical_data.py
python src/eda_logistics.py
python tests/test_eda_logistics.py
```

### Example synthetic findings
- 300 generated shipments; no missing cells or duplicate IDs by design.
- Overall synthetic on-time rate: 63.3%; mean delivery time: 10.05 hours; median: 8.07 hours.
- Mean synthetic transport cost: INR 1,681.51 per shipment; first-attempt success: 90.3%.
- East has the lowest simulated on-time rate (40.0%); South has the highest (76.4%).
- Pearson correlation between distance and cost is 0.983, partly because distance is built into the synthetic cost formula. Weight-volume and timestamp-derived correlations are similarly affected by how the data are generated. These results are teaching examples, not empirical claims.

### Analytical cautions
- Mean cost per shipment cannot be interpreted as vehicle efficiency without accounting for distance, payload and service level; use normalized measures such as cost per kilometre or kilogram where valid.
- A high correlation is not proof of causality, and some associations are deliberately encoded in the generator.
- The final weekly time bucket has only four orders because the simulated order window ends on 30 September 2026; its on-time rate is unstable.
- For operational decisions, replace the synthetic fixture with suitably licensed, documented real data and validate definitions, data quality and segment sample sizes.



## Week 4 — Predictive Modeling and Optimization in Logistics Systems

### Data transparency
Week 4 uses a deterministically generated **1,200-row synthetic/hypothetical shipment dataset** with a fixed seed. No real carrier records are included. Delivery-time values, vehicle assignments, operating-cost rates, evaluation metrics and all what-if recommendations in this section are illustrative results from the simulation. Do not present them as empirical findings or measured company savings.

### Week 4 deliverables
- `reports/Week_4_Predictive_Modeling_and_Optimization.docx` — professional report with model methodology, holdout evaluation, validation, feature diagnostics, vehicle what-if, recommendations, limitations and references.
- `submission/Week_4_Submission_Description.txt` — detailed portal description exceeding the 200-word minimum.
- `src/generate_week4_hypothetical_data.py` — reproducible creation of the synthetic shipment dataset (seed `20261016`).
- `src/train_evaluate_optimize.py` — feature preprocessing, baseline/Linear Regression/Random Forest comparison, training-only cross-validation, Random Forest grid search, final holdout metrics, feature diagnostics and capacity-constrained per-shipment what-if.
- `src/build_week4_report.py` — builds the formatted Word report from the saved, executed analysis outputs.
- `data/raw/week4_hypothetical_shipments.csv` — generated synthetic input data.
- `data/analysis/week4_model_metrics.csv`, `week4_cv_metrics.csv`, `week4_hyperparameter_search.csv`, `week4_feature_importance.csv`, `week4_test_predictions.csv`, `week4_test_error_by_region.csv`, `week4_vehicle_assignment_recommendations.csv`, JSON summaries and quality checks — reproducible outputs from the modeling run.
- `reports/figures/week4_*.png` — prediction diagnostics, model comparison, feature importance, regional errors and vehicle what-if charts.
- `tests/test_week4_modeling.py` — integrity tests for dataset, evaluation outputs, recommendations and figure files.

### Run Week 4
From the repository root, using Python 3.10+:

```bash
pip install -r requirements.txt
python src/generate_week4_hypothetical_data.py
python src/train_evaluate_optimize.py
python tests/test_week4_modeling.py
python src/build_week4_report.py
```

### Modeling design and current synthetic results
- Target: `delivery_time_hours`. Predictors are assumed dispatch-time features: distance, weight, volume, route stops, traffic index, weather severity, warehouse load, vehicle type, origin region, priority, and weekday. The target and synthetic cost column are excluded from predictors.
- Split: 80% training and 20% holdout test (960 / 240 rows), with fixed random state `20261016`.
- Model selection: five-fold training cross-validation compares a median baseline, Linear Regression and a default Random Forest. Linear Regression has the lower mean CV MAE among the predictive candidates and is selected before evaluating the holdout test.
- Holdout performance of selected Linear Regression in the current run: MAE about 0.826 hours, RMSE about 1.262 hours, R-squared about 0.955. Tuned Random Forest and baseline results are in `data/analysis/week4_model_metrics.csv`.
- A Random Forest grid search uses three-fold CV on training data. The held-out test set is not used for choosing model type/hyperparameters.
- The vehicle what-if scores feasible options by `estimated cost + ₹85 × predicted hours`, with hypothetical payload capacities and rate-card assumptions. It is a transparent per-shipment heuristic, not a fleet-wide route solver; results are not actual cost savings.

### Important limitations
The high predictive score should be interpreted cautiously because the target is generated from a known synthetic formula. Real shipment history may have unmeasured delays, data drift, route-specific effects and imperfect dispatch-time features. The random split is suitable only for this synthetic cross-sectional demonstration; use chronological or rolling validation with time-dependent production data. Feature importance is not causal evidence. The suggested 12-hour threshold is an illustrative triage rule, not a calibrated probability or contractual SLA. For production optimization, validate payload limits, fleet availability, driver hours, customer time windows, route networks and multi-stop constraints. Google OR-Tools can support formal routing models when a reliable distance/time matrix and operating constraints are available.

### References
- Scikit-learn model evaluation: https://scikit-learn.org/stable/modules/model_evaluation.html
- Scikit-learn LinearRegression: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html
- Scikit-learn RandomForestRegressor: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html
- Google OR-Tools Vehicle Routing Problem: https://developers.google.com/optimization/routing/vrp
