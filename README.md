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
