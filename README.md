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
