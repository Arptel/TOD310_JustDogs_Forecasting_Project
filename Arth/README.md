# JustDogs Sales Forecasting — Explicit Event-Aware Ridge Model
**Author:** Arth Patel  
**Course:** TOD310 – Predictive Analytics for Business  
**Faculty Guide:** Prof. Amit  
**Submission Horizon:** Q3 2025 (July 1, 2025 – September 30, 2025 | 92 Days)

---

## Executive Summary
This directory contains the champion **Explicit Event-Aware Ridge Regression Model** developed for JustDogs retail sales forecasting. Instead of using generic month-of-year or day-of-year proxies, this model explicitly incorporates real-world **Hindu Lunar Festivals (Panchang)**, **Global Animal Observance Days**, and **Corporate Payday Restock Windows** mapped across 1,122 calendar days from September 2022 to September 2025.

---

## Key Model Architecture

1. **Explicit One-Hot Event Indicator Matrix (15 Binary Columns):**
   * *Animal Observance Days (Solar):* `is_intl_dog_day` (Aug 24–27), `is_world_animal_day` (Oct 3–5), `is_national_pet_day` (Apr 10–12), `is_national_puppy_day` (Mar 23), `is_intl_cat_day` (Aug 8).
   * *Indian Lunar Festivals:* `is_diwali_rush` (Dhanteras, Choti Diwali, Diwali, Bhai Dooj), `is_raksha_bandhan`, `is_ganesh_chaturthi`, `is_navratri_dussehra`, `is_makar_sankranti` (Uttarayan), `is_eid`.
   * *National Holidays & Closures:* `is_independence_day`, `is_republic_day`, `is_holi_closure` (-₹48,014 shock, $p = 0.0136$).
   * *Salary Restocking:* `is_salary_payday` (+₹8,550/day, $p = 0.0565$), `is_weekend_payday_surge` (+₹9,503/day compounding).
2. **Regularization Scheme:**
   * **Ridge Regression ($L_2$ Penalty):** Regularization parameter $\alpha = 60.0$ applies shrinkage to sparse annual event columns, preventing overfitting on events that occur only 2–3 times in the historical dataset.
3. **Autoregressive & Calendar Baseline:**
   * Trend ($t = 0, 1, 2, \dots$), Day-of-Week dummies (`dow_1` to `dow_6`), `lag_1`, `lag_7`, and 30-day moving average (`rolling_mean_30`).
   * Condition Number stabilized, all VIFs $< 2.01$, Durbin-Watson $DW = 2.001$ (zero first-order autocorrelation).

---

## Validation Strategy: 4-Quarter Rolling Walk-Forward CV
To prevent data leakage while testing adaptability across all Indian retail seasons, the model was evaluated using an expanding walk-forward window across 4 full quarterly seasons (matching Prof. Amit's 92-day evaluation duration):

| Season / Fold | Calendar Window | Daily WAPE (%) | Daily MAE (INR) | Quarterly Financial Accuracy (%) |
| :--- | :--- | :---: | :---: | :---: |
| **Q3 2024 (Jul – Sep)** *(Exact test season replica)* | Jul 1, 2024 – Sep 30, 2024 | **29.63%** | ₹44,293.94 | **89.51%** |
| **Q4 2024 (Oct – Dec)** *(Peak Diwali / Winter)* | Oct 1, 2024 – Dec 31, 2024 | **26.97%** | ₹41,357.47 | **94.03%** |
| **Q1 2025 (Jan – Mar)** *(Post-holiday lull)* | Jan 1, 2025 – Mar 31, 2025 | 32.88% | ₹42,453.14 | 79.71% |
| **Q2 2025 (Apr – Jun)** *(Summer baseline)* | Apr 1, 2025 – Jun 30, 2025 | 28.42% | ₹35,966.33 | 92.49% |
| **4-Quarter Seasonal Benchmark Average** | — | **29.48%** | **₹41,017.72** | **88.94%** |

---

## Official Q3 2025 Revenue Forecast (July 1 – September 30, 2025)

The out-of-sample forecast incorporates the verified real-world events occurring in 2025:
* **Raksha Bandhan:** August 9, 2025
* **Independence Day Weekend:** August 14–16, 2025
* **International Dog Day Window:** August 24–27, 2025 (Peak promo Aug 26)
* **Ganesh Chaturthi:** Starts August 27, 2025
* **Navratri Season:** Starts September 22, 2025

| Month (2025) | Projected Revenue (INR) | Daily Average (INR) | Days | Key Active Events |
| :--- | :---: | :---: | :---: | :--- |
| **July 2025** | ₹42,54,591.29 | ₹137,244.88 | 31 | Baseline summer restock + Month-end payday |
| **August 2025** | **₹44,67,026.37** | **₹144,097.62** | 31 | **Highest Month:** Rakhi (Aug 9) + 15 Aug + Dog Day (Aug 26) + Ganesh (Aug 27) |
| **September 2025** | ₹43,64,645.48 | ₹145,488.18 | 30 | Navratri kickoff (Sep 22) + Month-end payday |
| **Total Q3 2025** | **₹1,30,86,263.14** | **₹142,241.99** | **92** | **~₹1.31 Crores total projected revenue** |

---

## Directory Contents
* `run_model.py`: End-to-end executable script that reproduces the entire pipeline.
* `sales_daily_train.csv`: Historical training dataset (Sept 2022 to June 2025).
* `JustDogs_Master_Event_Calendar_2022_2025.xlsx`: Formatted multi-sheet master Excel workbook with 1,122 days and 15 event columns.
* `JustDogs_Master_Event_Calendar_2022_2025.csv`: Master calendar in CSV format.
* `pred_model_explicit_events.csv`: Official 92-day test forecast for Q3 2025 with 80% CI bands.
* `plots/explicit_festival_coefficients.png`: Econometric coefficient plot.
* `plots/pred_model_explicit_events_forecast.png`: 92-day forecast curve with event markers.
* `plots/all_train_test_divisions_comparison.png`: Cross-division benchmark chart.

---

## How to Run
```bash
python run_model.py
```
Outputs the forecast CSV, regenerates the Excel workbook, and displays the 4-quarter CV evaluation metrics.
