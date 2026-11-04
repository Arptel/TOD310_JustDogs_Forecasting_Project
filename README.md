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

## Final Recommended Champion Model: Explicit Event-Aware Ridge Model (Arth)
Located in [`Arth/`](Arth/), this model combines:
1. **Explicit One-Hot Event Matrix (15 Binary Columns):** Maps Hindu lunar festival dates (Diwali, Rakhi, Ganesh Chaturthi, Navratri, Holi), global animal days (International Dog Day, World Animal Day), and monthly payday restock waves.
2. **Regularized Ridge Regression ($L_2$ Penalty, $\alpha = 60.0$):** Prevents overfitting on sparse annual festival days while isolating rupee-level impacts.
3. **4-Quarter Rolling Walk-Forward CV:** Achieved **88.94% 4-Season Average Accuracy** (**89.51%** on the Q3 historical season matching Prof. Amit's evaluation horizon).
4. **Projected Q3 2025 Revenue:** **₹1,30,86,263.14 (~₹1.31 Crores)** across 92 daily predictions.

### Quick Start
To reproduce Arth's model and regenerate the Excel workbook and forecast CSV:
```bash
cd Arth
python run_model.py
```
