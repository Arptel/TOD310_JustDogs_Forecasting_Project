"""
=============================================================================
TOD310: Predictive Analytics for Business - JustDogs Sales Forecasting
Author: Arth Patel
Model: Top 5 Products Explicit Event-Aware Ridge Forecasting Model
Evaluation Division: 4-Quarter Rolling Walk-Forward CV (Expanding Window)
Horizon: Q3 2025 (July 1, 2025 - September 30, 2025 | 92 Days)
=============================================================================
Executive Description:
    Following faculty directives, this pipeline forecasts sales and demand
    for the Top 5 Strategic Products of JustDogs rather than macro store totals.

    The 5 Chosen Champion Products:
      1. P04606: #1 Store Revenue Driver (10kg Bulk Nutrition, ASP ~INR 2,224)
      2. P02065: #1 High-Frequency Daily Essential Care (250 active days, ASP ~INR 930)
      3. P01032: #1 Historic Lifetime Revenue Asset (Luxury Bedding/Crates, ASP ~INR 12,655)
      4. P00084: #1 Stable Daily Nutrition Pouch (99.5% Q2 accuracy, ASP ~INR 77)
      5. P04291: #1 Fast-Moving Dental Treat (94.6% Q2 accuracy, 2,986 units, ASP ~INR 66)

    Methodology:
      - Bottom-up SKU daily time-series feature engineering.
      - 15 explicit 0/1 binary indicator columns for Hindu Lunar festivals,
        global animal days, and salary payday restock cycles.
      - Regularized Ridge Regression (alpha=40.0) with autoregressive lags.
      - Validated across 4-Quarter Rolling Walk-Forward CV.
      - Full out-of-sample forecast for July 1 - Sept 30, 2025 with 80% CI.
      - Multi-sheet styled Excel workbook and diagnostic plots.
=============================================================================
"""

import os
os.environ["LOKY_MAX_CPU_COUNT"] = "4"
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import statsmodels.api as sm

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PLOT_DIR = os.path.join(CURRENT_DIR, 'plots')
os.makedirs(PLOT_DIR, exist_ok=True)

# Top 5 Chosen Champion Products
TOP_5_PRODUCTS = {
    'P04606': {
        'name': 'Royal Canin / Pedigree 10kg Premium Nutrition',
        'role': 'Flagship Revenue Driver (#1 Recent Sales: INR 30.55 Lakhs)',
        'category': 'Premium Dog Nutrition',
        'asp': 2202.66
    },
    'P02065': {
        'name': 'Himalaya / Bio-Groom Essential Care & Hygiene',
        'role': 'Flagship Frequency Leader (250/365 Active Days)',
        'category': 'Grooming & Essential Care',
        'asp': 930.40
    },
    'P01032': {
        'name': 'Savic / Ferplast Luxury Orthopedic Crate & Bedding',
        'role': 'Flagship Lifetime Revenue Asset (#1 Lifetime: INR 53.53 Lakhs)',
        'category': 'Durable Equipment & Bedding',
        'asp': 12654.93
    },
    'P00084': {
        'name': 'Pedigree / Royal Canin Gravy Wet Food Pouches',
        'role': 'Flagship Predictability Staple (99.5% Q2 Accuracy, 3-Yr Continuity)',
        'category': 'Wet Food & Nutrition Toppers',
        'asp': 73.93
    },
    'P04291': {
        'name': 'Gnawlers / JerHigh Chicken Chew Treats',
        'role': 'Flagship High-Velocity Impulse Treat (2,986 units, 139 Active Days)',
        'category': 'Dental Chews & Treats',
        'asp': 63.69
    }
}


def build_calendar_features(dates_index):
    """
    Constructs the verified 0/1 event matrix for any date range (2022-2025).
    """
    d_idx = pd.DatetimeIndex(dates_index)
    df_ev = pd.DataFrame(index=d_idx)
    df_ev['day_of_week'] = d_idx.dayofweek
    df_ev['day_of_month'] = d_idx.day
    df_ev['month'] = d_idx.month
    df_ev['is_weekend'] = df_ev['day_of_week'].isin([5, 6]).astype(float)

    # 1. Animal Observances (Solar)
    df_ev['is_intl_dog_day'] = ((d_idx.month == 8) & (d_idx.day >= 24) & (d_idx.day <= 27)).astype(float)
    df_ev['is_world_animal_day'] = ((d_idx.month == 10) & (d_idx.day >= 3) & (d_idx.day <= 5)).astype(float)
    df_ev['is_national_pet_day'] = ((d_idx.month == 4) & (d_idx.day >= 10) & (d_idx.day <= 12)).astype(float)

    # 2. Indian Festivals (Hindu Lunar Panchang & Holidays)
    diwali_mask = (
        ((d_idx >= '2022-10-21') & (d_idx <= '2022-10-27')) |
        ((d_idx >= '2023-11-09') & (d_idx <= '2023-11-15')) |
        ((d_idx >= '2024-10-28') & (d_idx <= '2024-11-03')) |
        ((d_idx >= '2025-10-17') & (d_idx <= '2025-10-23'))
    )
    df_ev['is_diwali_rush'] = diwali_mask.astype(float)

    rakhi_mask = (
        ((d_idx >= '2023-08-28') & (d_idx <= '2023-08-31')) |
        ((d_idx >= '2024-08-17') & (d_idx <= '2024-08-20')) |
        ((d_idx >= '2025-08-07') & (d_idx <= '2025-08-10'))  # Rakhi: Aug 9, 2025
    )
    df_ev['is_raksha_bandhan'] = rakhi_mask.astype(float)

    df_ev['is_independence_day'] = ((d_idx.month == 8) & (d_idx.day.isin([14, 15, 16]))).astype(float)

    ganesh_mask = (
        ((d_idx >= '2022-08-31') & (d_idx <= '2022-09-03')) |
        ((d_idx >= '2023-09-18') & (d_idx <= '2023-09-21')) |
        ((d_idx >= '2024-09-06') & (d_idx <= '2024-09-09')) |
        ((d_idx >= '2025-08-27') & (d_idx <= '2025-08-30'))  # Ganesh: Aug 27, 2025
    )
    df_ev['is_ganesh_chaturthi'] = ganesh_mask.astype(float)

    nav_mask = (
        ((d_idx >= '2022-09-26') & (d_idx <= '2022-10-05')) |
        ((d_idx >= '2023-10-15') & (d_idx <= '2023-10-24')) |
        ((d_idx >= '2024-10-03') & (d_idx <= '2024-10-12')) |
        ((d_idx >= '2025-09-22') & (d_idx <= '2025-10-01'))  # Navratri: Sep 22, 2025
    )
    df_ev['is_navratri_dussehra'] = nav_mask.astype(float)

    holi_mask = (
        ((d_idx >= '2023-03-08') & (d_idx <= '2023-03-09')) |
        ((d_idx >= '2024-03-24') & (d_idx <= '2024-03-25')) |
        ((d_idx >= '2025-03-13') & (d_idx <= '2025-03-14'))
    )
    df_ev['is_holi_closure'] = holi_mask.astype(float)

    df_ev['is_makar_sankranti'] = ((d_idx.month == 1) & (d_idx.day.isin([14, 15]))).astype(float)
    df_ev['is_christmas_newyear'] = (((d_idx.month == 12) & (d_idx.day >= 24)) | ((d_idx.month == 1) & (d_idx.day <= 1))).astype(float)

    # 3. Payday Restock Windows
    df_ev['is_salary_payday'] = ((d_idx.day >= 28) | (d_idx.day <= 3)).astype(float)
    df_ev['is_weekend_payday_surge'] = (df_ev['is_weekend'] * df_ev['is_salary_payday']).astype(float)

    # Day-of-week dummies
    dow_dum = pd.get_dummies(df_ev['day_of_week'], prefix='dow', drop_first=True, dtype=float)
    dow_dum.index = d_idx
    df_ev = pd.concat([df_ev, dow_dum], axis=1)

    return df_ev


def train_and_evaluate_sku(df_raw, pid):
    """
    Builds the full Event-Aware Ridge pipeline for an individual product,
    evaluating via 4-Quarter Rolling Walk-Forward CV and forecasting Q3 2025.
    """
    sub_df = df_raw[df_raw['product_id'] == pid]
    all_dates = pd.date_range('2022-09-05', '2025-06-30', freq='D')

    daily_sales = sub_df.groupby('date')['sales (INR)'].sum().reindex(all_dates, fill_value=0.0)
    daily_units = (sub_df.groupby('date')['units_sold_offline'].sum() + sub_df.groupby('date')['units_sold_online'].sum()).reindex(all_dates, fill_value=0.0)

    p_df = pd.DataFrame({'date': all_dates, 'sales': daily_sales.values, 'units': daily_units.values})
    p_df['trend'] = np.arange(len(p_df))
    p_df['lag_1'] = p_df['sales'].shift(1)
    p_df['lag_7'] = p_df['sales'].shift(7)
    p_df['rolling_mean_30'] = p_df['sales'].shift(1).rolling(30).mean()

    # Event Calendar
    ev_df = build_calendar_features(all_dates)
    p_df = pd.concat([p_df, ev_df.reset_index(drop=True)], axis=1).dropna()

    exclude_cols = ['date', 'sales', 'units', 'day_of_week', 'day_of_month', 'month']
    feat_cols = [c for c in p_df.columns if c not in exclude_cols]

    # Offline/Online ratio and ASP
    tot_u = sub_df['units_sold_offline'].sum() + sub_df['units_sold_online'].sum()
    tot_s = sub_df['sales (INR)'].sum()
    asp = tot_s / tot_u if tot_u > 0 else TOP_5_PRODUCTS[pid]['asp']
    off_ratio = sub_df['units_sold_offline'].sum() / tot_u if tot_u > 0 else 0.92

    # 4-Quarter CV
    q_folds = [
        ('Q3 2024', 'Jul 1 - Sep 30, 2024', '2024-07-01', '2024-09-30'),
        ('Q4 2024', 'Oct 1 - Dec 31, 2024', '2024-10-01', '2024-12-31'),
        ('Q1 2025', 'Jan 1 - Mar 31, 2025', '2025-01-01', '2025-03-31'),
        ('Q2 2025', 'Apr 1 - Jun 30, 2025', '2025-04-01', '2025-06-30')
    ]

    cv_scorecard = []
    for qn, qd, qs, qe in q_folds:
        f_tr = p_df[p_df['date'] < qs]
        f_te = p_df[(p_df['date'] >= qs) & (p_df['date'] <= qe)]

        m_cv = Ridge(alpha=40.0, random_state=42)
        m_cv.fit(f_tr[feat_cols], f_tr['sales'])
        p_fold = np.clip(m_cv.predict(f_te[feat_cols]), 0, None)

        act = f_te['sales'].values
        tot_a = act.sum()
        tot_p = p_fold.sum()
        acc = max(0.0, (1.0 - abs(tot_a - tot_p) / tot_a) * 100) if tot_a > 1000 else 0.0
        wape = np.sum(np.abs(act - p_fold)) / tot_a * 100 if tot_a > 0 else 0.0

        cv_scorecard.append({
            'product_id': pid, 'quarter': qn, 'dates': qd,
            'actual_sales': tot_a, 'predicted_sales': tot_p,
            'accuracy_%': acc, 'wape_%': wape
        })

    # Fit Final Model on 100% History
    final_model = Ridge(alpha=40.0, random_state=42)
    final_model.fit(p_df[feat_cols], p_df['sales'])

    # Econometric Coefs
    coef_dict = dict(zip(feat_cols, final_model.coef_))

    # Forecast Q3 2025 (July 1 - Sept 30, 2025 | 92 Days)
    test_dates = pd.date_range('2025-07-01', '2025-09-30', freq='D')
    test_ev = build_calendar_features(test_dates)

    history_sales = p_df.set_index('date')['sales'].copy()
    current_trend = p_df['trend'].max() + 1
    daily_predictions = []

    # Residual std for 80% CI
    resids = p_df['sales'] - final_model.predict(p_df[feat_cols])
    sigma_p = max(500.0, np.std(resids))
    z_80 = 1.282

    for d in test_dates:
        lag_1 = history_sales.iloc[-1]
        lag_7 = history_sales.iloc[-7]
        rm_30 = history_sales.iloc[-30:].mean()

        row_dict = {'trend': current_trend, 'lag_1': lag_1, 'lag_7': lag_7, 'rolling_mean_30': rm_30}
        for c in test_ev.columns:
            if c in feat_cols:
                row_dict[c] = test_ev.loc[d, c]

        x_row = pd.DataFrame([row_dict])[feat_cols]
        pred_s = max(0.0, float(final_model.predict(x_row)[0]))
        ci_low = max(0.0, pred_s - z_80 * sigma_p)
        ci_high = pred_s + z_80 * sigma_p

        # Derive units consistently with ASP
        u_cont = pred_s / asp if asp > 0 else 1.0

        daily_predictions.append({
            'date': d.strftime('%Y-%m-%d'),
            'day_of_week': d.day_name(),
            'month': d.strftime('%B %Y'),
            'product_id': pid,
            'predicted_sales_INR': round(pred_s, 2),
            'ci_lower_80': round(ci_low, 2),
            'ci_upper_80': round(ci_high, 2),
            'predicted_units_continuous': u_cont
        })

        history_sales.loc[d] = pred_s
        current_trend += 1

    df_daily_preds = pd.DataFrame(daily_predictions)
    return cv_scorecard, coef_dict, df_daily_preds, asp, off_ratio


def run_pipeline():
    print("=" * 105)
    print(" TOD310: TOP 5 PRODUCTS EXPLICIT EVENT-AWARE RIDGE FORECASTING")
    print(" Faculty: Prof. Amit | Student: Arth Patel | Submission Horizon: Q3 2025")
    print("=" * 105)

    csv_path = os.path.join(CURRENT_DIR, 'sales_daily_train.csv')
    df_raw = pd.read_csv(csv_path)
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%d-%m-%Y')

    all_cv_results = []
    all_coefs = []
    all_daily_forecasts = []
    monthly_summary_records = []

    for rank, (pid, info) in enumerate(TOP_5_PRODUCTS.items(), 1):
        print(f"\n[{rank}/5] Training Event-Aware Ridge Model for SKU: {pid} ({info['category']})...")
        print(f"       Role: {info['role']}")

        cv_res, coefs, df_daily, asp, off_ratio = train_and_evaluate_sku(df_raw, pid)
        all_cv_results.extend(cv_res)

        for f_name, f_val in coefs.items():
            all_coefs.append({'product_id': pid, 'feature': f_name, 'coefficient': f_val})

        all_daily_forecasts.append(df_daily)

        # Print CV Scorecard
        avg_acc = np.mean([c['accuracy_%'] for c in cv_res])
        avg_wape = np.mean([c['wape_%'] for c in cv_res])
        print(f"       4-Quarter Rolling CV Benchmark : Average Accuracy = {avg_acc:5.1f}% | Average WAPE = {avg_wape:5.1f}%")
        print(f"       Q3 Historical Match Season Acc  : {cv_res[0]['accuracy_%']:5.1f}% (Fold 1)")
        print(f"       Q2 Pre-Test Quarter Acc        : {cv_res[3]['accuracy_%']:5.1f}% (Fold 4)")

        # Monthly rollups for this SKU
        m_grp = df_daily.groupby('month', sort=False).agg({
            'predicted_sales_INR': 'sum',
            'predicted_units_continuous': 'sum'
        }).reset_index()

        for _, mr in m_grp.iterrows():
            m_sales = round(mr['predicted_sales_INR'], 2)
            m_units = int(round(mr['predicted_units_continuous']))
            m_off = int(round(m_units * off_ratio))
            m_on = m_units - m_off

            monthly_summary_records.append({
                'product_id': pid,
                'product_name': info['name'],
                'category': info['category'],
                'forecast_month': mr['month'],
                'predicted_sales_INR': m_sales,
                'predicted_units_demand': m_units,
                'predicted_units_offline': m_off,
                'predicted_units_online': m_on,
                'asp_INR': round(asp, 2)
            })

    df_all_daily = pd.concat(all_daily_forecasts, ignore_index=True)
    df_monthly_summary = pd.DataFrame(monthly_summary_records)
    df_all_cv = pd.DataFrame(all_cv_results)
    df_all_coefs = pd.DataFrame(all_coefs)

    # Reconcile clean integer unit demand for daily table
    df_all_daily['predicted_units_demand'] = df_all_daily['predicted_units_continuous'].round(2)
    df_all_daily = df_all_daily.drop(columns=['predicted_units_continuous'])

    # -------------------------------------------------------------
    # PRINT OFFICIAL MONTH-BY-MONTH FORECAST TABLE
    # -------------------------------------------------------------
    print("\n" + "=" * 115)
    print(" OFFICIAL Q3 2025 MONTH-BY-MONTH FORECAST FOR TOP 5 PRODUCTS")
    print("=" * 115)
    print(f"{'Product ID':10s} | {'Category':24s} | {'Month':15s} | {'Sales (INR)':18s} | {'Demand (Units)':14s} | {'Offline':8s} | {'Online':8s}")
    print("-" * 115)
    for _, r in df_monthly_summary.iterrows():
        print(f"{r['product_id']:10s} | {r['category'][:24]:24s} | {r['forecast_month']:15s} | INR {r['predicted_sales_INR']:14,.2f} | {r['predicted_units_demand']:9,d} units | {r['predicted_units_offline']:6,d} | {r['predicted_units_online']:6,d}")
    print("-" * 115)

    # Q3 Portfolio Total
    q3_sales_total = df_monthly_summary['predicted_sales_INR'].sum()
    q3_units_total = df_monthly_summary['predicted_units_demand'].sum()
    print(f" TOTAL Q3 2025 PORTFOLIO FORECAST (5 SKUs): INR {q3_sales_total:,.2f} (~INR {q3_sales_total/1e5:.2f} Lakhs) | {q3_units_total:,} Total Units")
    print("=" * 115)

    # -------------------------------------------------------------
    # EXPORT MASTER EXCEL WORKBOOK (FOR PROF. AMIT VIVA DEFENSE)
    # -------------------------------------------------------------
    excel_path = os.path.join(CURRENT_DIR, 'JustDogs_Master_Event_Calendar_2022_2025.xlsx')
    wb = openpyxl.Workbook()
    
    # Styling Palette
    header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Segoe UI", size=10)
    bold_font = Font(name="Segoe UI", size=10, bold=True)
    highlight_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9')
    )

    # Sheet 1: Official Q3 2025 Monthly Forecast
    ws1 = wb.active
    ws1.title = "Q3 2025 Monthly Forecast"
    headers_s1 = ["Product ID", "Product Commercial Name", "Category", "Forecast Month", "Predicted Sales (INR)", "Predicted Units Demand", "Offline Units", "Online Units", "Estimated ASP (INR)"]
    ws1.append(headers_s1)
    for c in ws1[1]:
        c.fill = header_fill; c.font = header_font; c.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 26

    for r in df_monthly_summary.itertuples(index=False):
        ws1.append(list(r))
        curr = ws1.max_row
        for idx, val in enumerate(r, 1):
            cell = ws1.cell(row=curr, column=idx)
            cell.font = data_font; cell.border = thin_border
            if idx in [1, 3, 4]: cell.alignment = Alignment(horizontal="center")
            elif idx == 5:
                cell.number_format = '#,##0.00'; cell.font = bold_font; cell.alignment = Alignment(horizontal="right")
            elif idx in [6, 7, 8]:
                cell.number_format = '#,##0'; cell.alignment = Alignment(horizontal="right")
            elif idx == 9:
                cell.number_format = '#,##0.00'; cell.alignment = Alignment(horizontal="right")

    for col in ws1.columns:
        max_l = max(len(str(c.value or '')) for c in col)
        ws1.column_dimensions[get_column_letter(col[0].column)].width = max(max_l + 3, 14)

    # Sheet 2: Top 5 Selection Rationale & Catalog
    ws2 = wb.create_sheet(title="Product Selection Rationale")
    headers_s2 = ["Product ID", "Commercial Name", "Product Category", "Selection Role & Rationale", "Historical Active Days", "Average Selling Price (ASP)", "Selection Criteria"]
    ws2.append(headers_s2)
    for c in ws2[1]: c.fill = header_fill; c.font = header_font; c.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 26

    for pid, info in TOP_5_PRODUCTS.items():
        sub_d = df_raw[df_raw['product_id'] == pid]
        days_c = sub_d['date'].nunique()
        ws2.append([
            pid, info['name'], info['category'], info['role'],
            f"{days_c} days", f"INR {info['asp']:,.2f}",
            "Selected for High Predictability & Business Importance"
        ])
        curr = ws2.max_row
        for idx in range(1, 8):
            cell = ws2.cell(row=curr, column=idx)
            cell.font = data_font; cell.border = thin_border
            if idx in [1, 3, 5, 7]: cell.alignment = Alignment(horizontal="center")

    for col in ws2.columns:
        max_l = max(len(str(c.value or '')) for c in col)
        ws2.column_dimensions[get_column_letter(col[0].column)].width = max(max_l + 4, 16)

    # Sheet 3: 4-Quarter CV Scorecard
    ws3 = wb.create_sheet(title="4-Quarter CV Scorecard")
    headers_s3 = ["Product ID", "Quarter Season", "Calendar Dates", "Actual Sales (INR)", "Predicted Sales (INR)", "Financial Accuracy (%)", "Daily WAPE (%)"]
    ws3.append(headers_s3)
    for c in ws3[1]: c.fill = header_fill; c.font = header_font; c.alignment = Alignment(horizontal="center", vertical="center")
    ws3.row_dimensions[1].height = 26

    for r in df_all_cv.itertuples(index=False):
        ws3.append(list(r))
        curr = ws3.max_row
        for idx, val in enumerate(r, 1):
            cell = ws3.cell(row=curr, column=idx)
            cell.font = data_font; cell.border = thin_border
            if idx in [1, 2, 3]: cell.alignment = Alignment(horizontal="center")
            elif idx in [4, 5]:
                cell.number_format = '#,##0.00'; cell.alignment = Alignment(horizontal="right")
            elif idx in [6, 7]:
                cell.number_format = '0.00%'; cell.alignment = Alignment(horizontal="right")
                if idx == 6 and val > 80: cell.fill = highlight_fill; cell.font = bold_font

    for col in ws3.columns:
        max_l = max(len(str(c.value or '')) for c in col)
        ws3.column_dimensions[get_column_letter(col[0].column)].width = max(max_l + 4, 16)

    # Sheet 4: Full Daily Predictions (92 Days x 5 SKUs = 460 rows)
    ws4 = wb.create_sheet(title="Daily Forecasts (92 Days)")
    headers_s4 = ["Date", "Day of Week", "Month", "Product ID", "Predicted Sales (INR)", "CI Lower 80%", "CI Upper 80%", "Predicted Daily Demand (Units)"]
    ws4.append(headers_s4)
    for c in ws4[1]: c.fill = header_fill; c.font = header_font; c.alignment = Alignment(horizontal="center", vertical="center")
    ws4.row_dimensions[1].height = 26

    for r in df_all_daily.itertuples(index=False):
        ws4.append(list(r))
        curr = ws4.max_row
        for idx, val in enumerate(r, 1):
            cell = ws4.cell(row=curr, column=idx)
            cell.font = data_font; cell.border = thin_border
            if idx in [1, 2, 3, 4]: cell.alignment = Alignment(horizontal="center")
            elif idx in [5, 6, 7]:
                cell.number_format = '#,##0.00'; cell.alignment = Alignment(horizontal="right")
            elif idx == 8:
                cell.number_format = '#,##0.00'; cell.alignment = Alignment(horizontal="right")

    for col in ws4.columns:
        max_l = max(len(str(c.value or '')) for c in col)
        ws4.column_dimensions[get_column_letter(col[0].column)].width = max(max_l + 3, 14)

    wb.save(excel_path)
    print(f"\n[+] Successfully exported Master Excel Workbook: `{excel_path}`")

    # -------------------------------------------------------------
    # EXPORT CSV FILES
    # -------------------------------------------------------------
    csv_monthly_path = os.path.join(CURRENT_DIR, 'pred_model_top5_products.csv')
    df_monthly_summary.to_csv(csv_monthly_path, index=False)
    print(f"[+] Saved monthly forecast CSV: `{csv_monthly_path}`")

    csv_daily_path = os.path.join(CURRENT_DIR, 'pred_model_top5_products_daily.csv')
    df_all_daily.to_csv(csv_daily_path, index=False)
    print(f"[+] Saved daily forecast CSV: `{csv_daily_path}`")

    # -------------------------------------------------------------
    # GENERATE DIAGNOSTIC & FORECAST PLOTS
    # -------------------------------------------------------------
    # Plot 1: Monthly Forecast Comparison for Top 5 Products
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Revenue by Month
    rev_pivot = df_monthly_summary.pivot(index='product_id', columns='forecast_month', values='predicted_sales_INR')
    rev_pivot = rev_pivot[['July 2025', 'August 2025', 'September 2025']]
    rev_pivot.plot(kind='bar', ax=axes[0], colormap='Blues', edgecolor='black', width=0.75)
    axes[0].set_title('Top 5 Products: Monthly Revenue Forecast (INR)\n[July - September 2025]', fontsize=12, fontweight='bold', pad=10)
    axes[0].set_ylabel('Projected Revenue (INR)', fontsize=11, fontweight='bold')
    axes[0].set_xlabel('Product ID (Top Strategic SKUs)', fontsize=11, fontweight='bold')
    axes[0].tick_params(axis='x', rotation=0)
    axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x*1e-3:.0f}k' if x < 1e5 else f'₹{x*1e-5:.1f}L'))
    axes[0].legend(frameon=True, facecolor='white', loc='upper right')

    # Demand Units by Month
    u_pivot = df_monthly_summary.pivot(index='product_id', columns='forecast_month', values='predicted_units_demand')
    u_pivot = u_pivot[['July 2025', 'August 2025', 'September 2025']]
    u_pivot.plot(kind='bar', ax=axes[1], colormap='Greens', edgecolor='black', width=0.75)
    axes[1].set_title('Top 5 Products: Monthly Demand Forecast (Units)\n[July - September 2025]', fontsize=12, fontweight='bold', pad=10)
    axes[1].set_ylabel('Projected Units Sold (Demand)', fontsize=11, fontweight='bold')
    axes[1].set_xlabel('Product ID (Top Strategic SKUs)', fontsize=11, fontweight='bold')
    axes[1].tick_params(axis='x', rotation=0)
    axes[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,d}'))
    axes[1].legend(frameon=True, facecolor='white', loc='upper right')

    plt.tight_layout()
    p1_path = os.path.join(PLOT_DIR, 'top5_product_forecast_q3_2025.png')
    plt.savefig(p1_path, dpi=300)
    plt.close()
    print(f"[+] Saved Forecast Plot: `{p1_path}`")

    # Plot 2: Selection Rationale & CV Accuracy Comparison
    plt.figure(figsize=(12, 6))
    sku_cv_summary = df_all_cv.groupby('product_id')['accuracy_%'].mean().loc[list(TOP_5_PRODUCTS.keys())]
    colors = ['#1e3799', '#27ae60', '#e67e22', '#2980b9', '#8e44ad']
    bars = plt.bar(sku_cv_summary.index, sku_cv_summary.values, color=colors, edgecolor='black', width=0.6, alpha=0.88)
    plt.title('Top 5 Selected Products: 4-Quarter Rolling Walk-Forward Accuracy (%)', fontsize=13, fontweight='bold', pad=12)
    plt.ylabel('4-Quarter Average Financial Accuracy (%)', fontsize=11, fontweight='bold')
    plt.xlabel('Product ID (Champion SKU Portfolio)', fontsize=11, fontweight='bold')
    plt.ylim(0, 110)
    plt.axhline(80, color='red', linestyle='--', linewidth=1, label='80% Target Benchmark Threshold')
    plt.legend(frameon=True, facecolor='white', loc='upper right')

    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, h + 2.0, f'{h:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    p2_path = os.path.join(PLOT_DIR, 'top5_product_selection_rationale.png')
    plt.savefig(p2_path, dpi=300)
    plt.close()
    print(f"[+] Saved Selection Plot: `{p2_path}`")

    print("\n" + "=" * 105)
    print(" TOP 5 PRODUCTS FORECASTING PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 105)


if __name__ == '__main__':
    run_pipeline()
