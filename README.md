🧾 Synthetic Tax Dataset Generator
📌 Overview

The Synthetic Tax Dataset Generator is a Python-based tool designed to generate realistic, structured tax data for testing, training, and experimentation. It simulates taxpayer information, income sources, deductions, credits, and tax calculations aligned with typical tax filing structures (e.g., Form 1040 logic).


This project is especially useful for:

i) Machine Learning model training (tax prediction, anomaly detection)
ii) Testing financial software systems
iii) Generating large-scale, privacy-safe datasets
iv) Educational and research purposes

Features
i) Realistic Tax Simulation
ii) enerates W-2 income, interest income, dividends, and self-employment (Schedule C)
iii) Supports multiple filing statuses:
iv) Single
v) Married Filing Jointly
vi) Head of Household

🧮 Tax Calculation Engine

Computes:
Total income
Adjusted Gross Income (AGI)
Taxable income
Federal tax liability
Includes logic for:
Standard deductions
Tax brackets
Earned Income Tax Credit (EITC)

📊 Dataset Generation
Produces structured datasets (CSV/JSON)
Configurable dataset size (small → large scale)
Randomized yet logically consistent entries

🔍 Data Consistency Checks
Ensures no invalid tax scenarios
Validates relationships between income, deductions, and tax outputs
