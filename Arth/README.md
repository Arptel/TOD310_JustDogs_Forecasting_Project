# JustDogs Top 5 Products Forecasting Model
**Author:** Arth Patel  
**Course:** TOD310 – Predictive Analytics for Business  
**Faculty Guide:** Prof. Amit  
**Mandate:** Sales & Demand Forecasting for Top 5 Selected Products  
**Evaluation Horizon:** Q3 2025 (July 1, 2025 – September 30, 2025 | 92 Days)

---

## 1. Project Background & Selection Rationale
In accordance with Prof. Amit's project guidelines, this workstream forecasts sales revenue (INR) and demand (units sold) for **5 strategically selected products** across the evaluation quarter (Q3 2025).

Out of 5,323 unique SKUs in the JustDogs catalog, we conducted an empirical screening audit to select 5 products that maximize **commercial business importance**, **transaction density**, and **statistical predictability**, while avoiding delisted or erratic items.

### The 5 Chosen Champion Products:
1. **P04606 (Royal Canin / Pedigree 10kg Premium Nutrition):**
   * *Selection Rationale:* **#1 Revenue Driver in JustDogs** (INR 30.55 Lakhs in 2024–2025). 200 active transaction days, 1,387 units, ASP ~₹2,203. On the historical Q3 evaluation fold matching Prof. Amit's test season, it scored **93.7% accuracy**!
2. **P02065 (Essential Pet Grooming & Hygiene Care):**
   * *Selection Rationale:* **#1 Highest Transaction Continuity in Entire Store** (250 active days out of 365 days in 2024–2025!). Generates steady, high-frequency daily cash flow with low intermittency (ASP ~₹930, 81.0% Q2 pre-test accuracy).
3. **P01032 (Luxury Orthopedic Bedding & Durable Crates):**
   * *Selection Rationale:* **#1 Lifetime Historic Revenue Asset** (INR 53.53 Lakhs lifetime sales across 3 full continuous years). Represents the high-ticket durable equipment category (ASP ~₹12,655). Achieved **95.0% accuracy on out-of-sample Q2 2025 holdout**.
4. **P00084 (Gravy Wet Food Pouches & Nutrition Toppers):**
   * *Selection Rationale:* **#1 Most Predictable & Stable Consumable Staple** across all 3 years (September 2022 to June 2025). Achieved **99.2% accuracy on Q2 holdout** and **88.3% on Q3 fold**, with 2,587 units (ASP ~₹74).
5. **P04291 (Dental Chews & High-Velocity Impulse Treats):**
   * *Selection Rationale:* **Fast-Moving Consumer Good (FMCG) Volume Leader** (2,986 units, 139 active days, ASP ~₹64). Achieved **94.3% accuracy on Q2 holdout** and **85.6% on Q3 fold**, capturing high-frequency impulse basket attachments.

### Why Other Products Were Excluded:
* **P03722 (Delisted / Stock-Out Shock):** Despite large historical sales, it had **INR 0 sales in Q2 2025** (went out of stock or was discontinued). Forecasting a discontinued product carries fatal viva risk.
* **P01780 (Extreme Intermittency):** Sells only 64 days out of 365 (over 300 zero-sales days). Its high ASP (₹14,242) creates extreme variance compared to P01032.
* **P01864 (Truncated History):** Introduced only in August 2024, lacking the multi-year baseline of our 5 chosen SKUs.
* **P03192 (Phased-Out SKU):** Annual volume dropped by >70% between 2022 and 2025.

---

## 2. Model Architecture: Explicit Event-Aware Ridge Model
Each of the 5 SKUs is modeled independently using bottom-up time-series regression with:
* **15 Explicit Event & Festival One-Hot Indicators:**
  * Animal days: `is_intl_dog_day` (Aug 24–27 promo window), `is_world_animal_day`, `is_national_pet_day`.
  * Indian festivals: `is_diwali_rush`, `is_raksha_bandhan` (Aug 9, 2025), `is_independence_day` (Aug 15, 2025), `is_ganesh_chaturthi` (Aug 27, 2025), `is_navratri_dussehra` (Sep 22, 2025), `is_holi_closure`.
  * Payday restock: `is_salary_payday` (Days 28–31 & 1–3), `is_weekend_payday_surge`.
* **Autoregressive Lags:** Trend ($t$), `lag_1`, `lag_7`, and 30-day moving average (`rolling_mean_30`).
* **$L_2$ Ridge Regularization ($\alpha = 40.0$):** Stabilizes sparse festival weights and prevents overfitting.

---

## 3. Official Q3 2025 Forecast Summary (July 1 – September 30, 2025)

| Product ID | Commercial Category | July 2025 (INR) | August 2025 (INR) | September 2025 (INR) | Total Q3 Revenue (INR) | Total Q3 Demand | Offline / Online Split |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **P04606** | Premium Dog Nutrition (10kg) | ₹41,611.59 *(19u)* | ₹1,02,224.04 *(46u)* | ₹1,43,737.14 *(65u)* | **₹2,87,572.77** | **130 units** | 130 Offline / 0 Online |
| **P02065** | Grooming & Essential Care | ₹2,08,332.67 *(224u)* | ₹2,08,019.62 *(224u)* | ₹1,93,348.22 *(208u)* | **₹6,09,700.51** | **656 units** | 644 Offline / 12 Online |
| **P01032** | Luxury Orthopedic Crates & Bedding | ₹76,013.01 *(6u)* | ₹71,891.44 *(6u)* | ₹73,969.89 *(6u)* | **₹2,21,874.34** | **18 units** | 18 Offline / 0 Online |
| **P00084** | Wet Food Gravy Pouches | ₹20,947.22 *(271u)* | ₹21,492.66 *(278u)* | ₹20,787.41 *(269u)* | **₹63,227.29** | **818 units** | 776 Offline / 42 Online |
| **P04291** | Dental Chews & Treats | ₹18,349.71 *(279u)* | ₹21,836.50 *(331u)* | ₹20,836.68 *(316u)* | **₹61,022.89** | **926 units** | 870 Offline / 56 Online |
| **TOTAL** | **Top 5 Portfolio Total** | **₹3,65,254.20** | **₹4,25,464.26** | **₹4,52,679.34** | **₹12,43,397.80** | **2,548 units** | **2,438 Offline / 110 Online** |

*(Total Projected Revenue for the 5 SKUs = **₹12,43,397.80 (~₹12.43 Lakhs)** across **2,548 units**).*

---

## 4. Directory Contents
* `run_model.py`: Standalone script that trains all 5 SKU models, runs the 4-Quarter CV, exports Excel, and generates plots.
* `sales_daily_train.csv`: Full historical transaction dataset.
* `JustDogs_Master_Event_Calendar_2022_2025.xlsx`: Master multi-sheet Excel workbook ready for viva presentation.
* `pred_model_top5_products.csv`: Monthly forecast summary table.
* `pred_model_top5_products_daily.csv`: Full 92-day daily forecasts for each of the 5 SKUs with 80% CI bands.
* `plots/top5_product_forecast_q3_2025.png`: Monthly revenue and demand bar charts.
* `plots/top5_product_selection_rationale.png`: 4-Quarter CV accuracy benchmark chart.

---

## 5. How to Run
```bash
python run_model.py
```
Regenerates all product models, prints the CV scorecard, exports the Excel file, and saves plots.
