# TOD310: Predictive Analytics for Business
## JustDogs Omnichannel Retail Sales Forecasting Project
**Faculty Guide:** Prof. Amit  
**Academic Term:** Semester 7 (Nov 2026)  
**Evaluation Horizon:** Q3 2025 (July 1, 2025 – September 30, 2025 | 92 Days)

---

## Project Overview
This repository contains the collaborative predictive analytics workstreams for forecasting daily omnichannel sales at **JustDogs** (India's leading pet retail store network).

The goal is to produce highly defensible, explainable, and operationally realistic daily revenue forecasts for the evaluation quarter (Q3 2025), balancing seasonal retail trends, intra-week shopping patterns, corporate payday restocking waves, and culturally shifting Indian festival calendars.

---

## Team Workstreams & Repository Layout
The repository is structured by team member workspaces:

```
TOD310_JustDogs_Forecasting_Project/
├── README.md                                  # Repository overview and guide
├── .gitignore                                 # Git ignore file
├── Arth/                                      # Arth Patel's Champion Model Stream
│   ├── run_model.py                           # Standalone executable pipeline
│   ├── sales_daily_train.csv                  # Historical daily sales dataset (2022-2025)
│   ├── JustDogs_Master_Event_Calendar_2022_2025.xlsx  # Multi-sheet Excel workbook (1,122 days)
│   ├── JustDogs_Master_Event_Calendar_2022_2025.csv   # Master 0/1 event matrix (CSV)
│   ├── pred_model_explicit_events.csv         # Official Q3 2025 daily test predictions
│   ├── plots/                                 # Diagnostic and forecast visual plots
│   └── README.md                              # Complete methodology documentation
├── Jay/                                       # Jay's Workstream
├── Avadh/                                     # Avadh's Workstream
├── Radha/                                     # Radha's Workstream
├── Kushal/                                    # Kushal's Workstream
├── Mukesh/                                    # Mukesh's Workstream
├── Deep/                                      # Deep's Workstream
├── Hritik/                                    # Hritik's Workstream
└── Shyam/                                     # Shyam's Workstream
```

---

## Final Recommended Champion Model: Top 5 Products Explicit Event-Aware Ridge Model (Arth)
Located in [`Arth/`](Arth/), this model focuses on the **Top 5 Strategic Products** of JustDogs:
1. **P04606 (Premium 10kg Dog Nutrition):** #1 Revenue Driver (INR 30.55 Lakhs recent sales, 93.7% Q3 accuracy).
2. **P02065 (Essential Care & Grooming):** #1 Frequency Leader (250/365 active days, 81.0% Q2 accuracy).
3. **P01032 (Luxury Orthopedic Crates & Bedding):** #1 Lifetime Revenue Asset (INR 53.53 Lakhs total sales, 95.0% Q2 accuracy).
4. **P00084 (Wet Food Gravy Pouches):** #1 Predictability Staple (99.2% Q2 accuracy, 3-year unbroken stability).
5. **P04291 (High-Velocity Dental Treats):** FMCG Volume Leader (2,986 units sold, 94.3% Q2 accuracy).

### Key Features:
* **15 Explicit One-Hot Event Columns:** Hindu lunar festival dates (Diwali, Rakhi, Ganesh Chaturthi, Navratri, Holi), global animal days (Dog Day, World Animal Day), and monthly payday restock waves.
* **Ridge Regularization ($L_2$ Penalty, $\alpha = 40.0$):** Stabilizes sparse festival parameters.
* **Total Projected Q3 2025 Portfolio Sales:** **₹12,43,397.80 (~₹12.43 Lakhs)** across **2,548 units**.

### Quick Start
To reproduce Arth's model and regenerate the Excel workbook and forecast CSV:
```bash
cd Arth
python run_model.py
```

