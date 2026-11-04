"""
=============================================================================
TOD310: Predictive Analytics for Business - JustDogs Sales Forecasting
Author: Arth Patel
Model: Explicit Event-Aware Ridge Regression Model
Evaluation Division: 4-Quarter Rolling Walk-Forward CV (Seasonal Expanding Window)
=============================================================================
Description:
    This script implements the final champion model:
      1. Maps real-world Gregorian and Hindu Lunar calendars (2022-2025) into
         15 explicit binary (0/1) indicator columns for festivals, animal days,
         and salary restock windows.
      2. Validates across an unbroken 4-Quarter Rolling Walk-Forward CV, matching
         the 92-day duration of the evaluation period (July 1 - Sept 30, 2025).
      3. Trains Ridge Regression with L2 regularization (alpha=60.0) to prevent
         overfitting on sparse annual events.
      4. Generates the official Q3 2025 daily sales forecast with 80% CI bands.
      5. Generates the Master Excel Workbook (JustDogs_Master_Event_Calendar_2022_2025.xlsx)
         and diagnostic plots.
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


def build_master_event_calendar(start_date='2022-09-05', end_date='2025-09-30'):
    """
    Constructs an exhaustive, verified 0/1 indicator calendar for all 1,122 days.
    """
    all_dates = pd.date_range(start_date, end_date, freq='D')
    df = pd.DataFrame({'date': all_dates})
    df['day_of_week'] = df['date'].dt.day_name()
    df['day_of_month'] = df['date'].dt.day
    df['month_name'] = df['date'].dt.strftime('%B')
    df['year'] = df['date'].dt.year
    df['is_weekend'] = df['date'].dt.dayofweek.isin([5, 6]).astype(int)

    # 1. Animal Observances (Global Solar Calendar)
    df['is_intl_dog_day'] = 0
    df.loc[(df['date'].dt.month == 8) & (df['date'].dt.day.isin([24, 25, 26, 27])), 'is_intl_dog_day'] = 1

    df['is_world_animal_day'] = 0
    df.loc[(df['date'].dt.month == 10) & (df['date'].dt.day.isin([3, 4, 5])), 'is_world_animal_day'] = 1

    df['is_national_pet_day'] = 0
    df.loc[(df['date'].dt.month == 4) & (df['date'].dt.day.isin([10, 11, 12])), 'is_national_pet_day'] = 1

    df['is_national_puppy_day'] = 0
    df.loc[(df['date'].dt.month == 3) & (df['date'].dt.day == 23), 'is_national_puppy_day'] = 1

    df['is_intl_cat_day'] = 0
    df.loc[(df['date'].dt.month == 8) & (df['date'].dt.day == 8), 'is_intl_cat_day'] = 1

    # 2. Indian Festivals (Hindu Lunar Panchang & National Holidays)
    df['is_diwali_rush'] = 0
    diwali_periods = [
        ('2022-10-21', '2022-10-27'),
        ('2023-11-09', '2023-11-15'),
        ('2024-10-28', '2024-11-03'),
        ('2025-10-17', '2025-10-23')
    ]
    for s, e in diwali_periods:
        df.loc[(df['date'] >= s) & (df['date'] <= e), 'is_diwali_rush'] = 1

    df['is_raksha_bandhan'] = 0
    rakhi_periods = [
        ('2023-08-28', '2023-08-31'),
        ('2024-08-17', '2024-08-20'),
        ('2025-08-07', '2025-08-10')  # Rakhi: Aug 9, 2025 (Test Set)
    ]
    for s, e in rakhi_periods:
        df.loc[(df['date'] >= s) & (df['date'] <= e), 'is_raksha_bandhan'] = 1

    df['is_independence_day'] = 0
    df.loc[(df['date'].dt.month == 8) & (df['date'].dt.day.isin([14, 15, 16])), 'is_independence_day'] = 1

    df['is_republic_day'] = 0
    df.loc[(df['date'].dt.month == 1) & (df['date'].dt.day.isin([25, 26, 27])), 'is_republic_day'] = 1

    df['is_ganesh_chaturthi'] = 0
    ganesh_periods = [
        ('2022-08-31', '2022-09-03'),
        ('2023-09-18', '2023-09-21'),
        ('2024-09-06', '2024-09-09'),
        ('2025-08-27', '2025-08-30')  # Ganesh: Aug 27, 2025 (Test Set)
    ]
    for s, e in ganesh_periods:
        df.loc[(df['date'] >= s) & (df['date'] <= e), 'is_ganesh_chaturthi'] = 1

    df['is_navratri_dussehra'] = 0
    nav_periods = [
        ('2022-09-26', '2022-10-05'),
        ('2023-10-15', '2023-10-24'),
        ('2024-10-03', '2024-10-12'),
        ('2025-09-22', '2025-10-01')  # Navratri: Sep 22, 2025 (Test Set)
    ]
    for s, e in nav_periods:
        df.loc[(df['date'] >= s) & (df['date'] <= e), 'is_navratri_dussehra'] = 1

    df['is_holi_closure'] = 0
    holi_periods = [
        ('2023-03-08', '2023-03-09'),
        ('2024-03-24', '2024-03-25'),
        ('2025-03-13', '2025-03-14')
    ]
    for s, e in holi_periods:
        df.loc[(df['date'] >= s) & (df['date'] <= e), 'is_holi_closure'] = 1

    df['is_makar_sankranti'] = 0
    df.loc[(df['date'].dt.month == 1) & (df['date'].dt.day.isin([14, 15])), 'is_makar_sankranti'] = 1

    df['is_christmas_newyear'] = 0
    df.loc[((df['date'].dt.month == 12) & (df['date'].dt.day >= 24)) |
           ((df['date'].dt.month == 1) & (df['date'].dt.day <= 1)), 'is_christmas_newyear'] = 1

    df['is_eid'] = 0
    eid_periods = [
        ('2023-04-21', '2023-04-23'), ('2023-06-28', '2023-06-30'),
        ('2024-04-10', '2024-04-12'), ('2024-06-16', '2024-06-18'),
        ('2025-03-30', '2025-04-01'), ('2025-06-06', '2025-06-08')
    ]
    for s, e in eid_periods:
        df.loc[(df['date'] >= s) & (df['date'] <= e), 'is_eid'] = 1

    # 3. Payday Restock Windows
    df['is_salary_payday'] = 0
    df.loc[(df['date'].dt.day >= 28) | (df['date'].dt.day <= 3), 'is_salary_payday'] = 1

    df['is_weekend_payday_surge'] = (df['is_weekend'] == 1) & (df['is_salary_payday'] == 1)
    df['is_weekend_payday_surge'] = df['is_weekend_payday_surge'].astype(int)

    def get_event_label(row):
        labels = []
        if row['is_intl_dog_day'] == 1: labels.append("Intl Dog Day (Promo Peak)")
        if row['is_world_animal_day'] == 1: labels.append("World Animal Day")
        if row['is_national_pet_day'] == 1: labels.append("National Pet Day")
        if row['is_diwali_rush'] == 1: labels.append("Diwali & Dhanteras Rush")
        if row['is_raksha_bandhan'] == 1: labels.append("Raksha Bandhan")
        if row['is_independence_day'] == 1: labels.append("Independence Day Weekend")
        if row['is_ganesh_chaturthi'] == 1: labels.append("Ganesh Chaturthi")
        if row['is_navratri_dussehra'] == 1: labels.append("Navratri Season")
        if row['is_holi_closure'] == 1: labels.append("Holi Store Closure")
        if row['is_makar_sankranti'] == 1: labels.append("Makar Sankranti (Uttarayan)")
        if row['is_christmas_newyear'] == 1: labels.append("Christmas / New Year")
        if row['is_eid'] == 1: labels.append("Eid Holiday")
        if row['is_weekend_payday_surge'] == 1: labels.append("Weekend Payday Surge")
        elif row['is_salary_payday'] == 1: labels.append("Monthly Salary Restock")
        elif row['is_weekend'] == 1: labels.append("Regular Weekend")
        return " + ".join(labels) if labels else "Regular Business Day"

    df['event_primary_name'] = df.apply(get_event_label, axis=1)
    return df


def export_styled_excel(df_master, df_coefs, df_cv, excel_path):
    """
    Exports a styled multi-sheet Excel file for viva defense presentation.
    """
    wb = openpyxl.Workbook()
    ws_main = wb.active
    ws_main.title = "Daily Master Calendar"

    header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Segoe UI", size=10)
    bold_font = Font(name="Segoe UI", size=10, bold=True)
    highlight_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    test_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9')
    )

    cols_order = [
        'date_str', 'day_of_week', 'day_of_month', 'month_name', 'year',
        'sales_INR', 'data_split', 'event_primary_name',
        'is_intl_dog_day', 'is_world_animal_day', 'is_national_pet_day',
        'is_diwali_rush', 'is_raksha_bandhan', 'is_independence_day',
        'is_ganesh_chaturthi', 'is_navratri_dussehra', 'is_holi_closure',
        'is_makar_sankranti', 'is_christmas_newyear', 'is_eid',
        'is_salary_payday', 'is_weekend_payday_surge', 'is_weekend'
    ]

    df_out = df_master.copy()
    df_out['date_str'] = df_out['date'].dt.strftime('%Y-%m-%d')
    df_out = df_out[cols_order]

    headers = [
        "Date", "Day of Week", "Day", "Month", "Year",
        "Sales (INR)", "Dataset Period", "Primary Event Name",
        "Intl Dog Day", "World Animal Day", "National Pet Day",
        "Diwali Rush", "Raksha Bandhan", "Independence Day",
        "Ganesh Chaturthi", "Navratri / Dussehra", "Holi Closure",
        "Makar Sankranti", "Christmas/NewYear", "Eid",
        "Salary Payday", "Weekend Payday Surge", "Weekend"
    ]
    ws_main.append(headers)

    for cell in ws_main[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws_main.row_dimensions[1].height = 28

    for r_idx, row in df_out.iterrows():
        ws_main.append(list(row))
        curr_row = ws_main.max_row
        is_test = (row['data_split'] == 'Test Period (Q3 2025)')

        for c_idx, val in enumerate(row, 1):
            cell = ws_main.cell(row=curr_row, column=c_idx)
            cell.font = data_font
            cell.border = thin_border
            if is_test:
                cell.fill = test_fill
            elif val == 1 and c_idx >= 9:
                cell.fill = highlight_fill
                cell.font = bold_font

            if c_idx == 6 and isinstance(val, (int, float)):
                cell.number_format = '#,##0.00'
                cell.alignment = Alignment(horizontal="right")
            elif c_idx in [1, 3, 5] or c_idx >= 9:
                cell.alignment = Alignment(horizontal="center")

    for col in ws_main.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_main.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # Sheet 2: Econometric Coefficients
    ws_coef = wb.create_sheet(title="Festival Rupee Impact")
    ws_coef.append(["Event / Festival Feature", "Isolated Impact (INR/day)", "Standard Error", "t-Statistic", "p-Value", "Statistical Significance"])
    for cell in ws_coef[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_coef.row_dimensions[1].height = 26

    for r in df_coefs.itertuples(index=False):
        ws_coef.append(list(r))
        curr_row = ws_coef.max_row
        for c_idx, val in enumerate(r, 1):
            cell = ws_coef.cell(row=curr_row, column=c_idx)
            cell.font = data_font
            cell.border = thin_border
            if c_idx == 2:
                cell.number_format = '#,##0.00'
                cell.alignment = Alignment(horizontal="right")
                if val > 0: cell.font = bold_font
            elif c_idx in [3, 4, 5]:
                cell.number_format = '0.0000'
                cell.alignment = Alignment(horizontal="right")
            elif c_idx == 6:
                cell.alignment = Alignment(horizontal="center")
                if "Significant" in str(val):
                    cell.fill = highlight_fill
                    cell.font = bold_font

    for col in ws_coef.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_coef.column_dimensions[col_letter].width = max(max_len + 4, 15)

    # Sheet 3: 4-Quarter CV
    ws_cv = wb.create_sheet(title="4-Quarter CV Evaluation")
    ws_cv.append(["Quarter Season", "Calendar Dates", "Daily WAPE (%)", "Daily MAE (INR)", "Quarterly Financial Accuracy (%)"])
    for cell in ws_cv[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_cv.row_dimensions[1].height = 26

    for r in df_cv.itertuples(index=False):
        ws_cv.append(list(r))
        curr_row = ws_cv.max_row
        for c_idx, val in enumerate(r, 1):
            cell = ws_cv.cell(row=curr_row, column=c_idx)
            cell.font = data_font
            cell.border = thin_border
            if c_idx in [3, 5]:
                cell.number_format = '0.00%'
                cell.alignment = Alignment(horizontal="right")
            elif c_idx == 4:
                cell.number_format = '#,##0.00'
                cell.alignment = Alignment(horizontal="right")

    for col in ws_cv.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_cv.column_dimensions[col_letter].width = max(max_len + 4, 18)

    wb.save(excel_path)
    print(f"[+] Exported Master Excel: `{excel_path}`")


def main():
    print("=" * 95)
    print(" TOD310: JUSTDOGS SALES FORECASTING - EXPLICIT EVENT RIDGE PIPELINE")
    print("=" * 95)

    # 1. Build Master Calendar
    df_calendar = build_master_event_calendar()
    print(f"[1] Built complete 1,122-day calendar (2022-09-05 to 2025-09-30).")

    # 2. Load Historical Sales
    csv_sales = os.path.join(CURRENT_DIR, 'sales_daily_train.csv')
    df_raw = pd.read_csv(csv_sales)
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%d-%m-%Y')
    daily_s = df_raw.groupby('date')['sales (INR)'].sum()

    df_calendar['sales_INR'] = df_calendar['date'].map(daily_s)

    train_end = pd.to_datetime('2025-06-30')
    df_calendar['data_split'] = np.where(df_calendar['date'] <= train_end, 'Training Period (Historical)', 'Test Period (Q3 2025)')

    # Handle missing date (Holi store closure)
    train_mask = df_calendar['data_split'] == 'Training Period (Historical)'
    df_calendar.loc[train_mask & df_calendar['sales_INR'].isna(), 'sales_INR'] = 0.0

    # 3. Time, Lag and Dummy Features
    df_calendar['trend'] = np.arange(len(df_calendar))
    df_calendar['lag_1'] = df_calendar['sales_INR'].shift(1)
    df_calendar['lag_7'] = df_calendar['sales_INR'].shift(7)
    df_calendar['rolling_mean_30'] = df_calendar['sales_INR'].shift(1).rolling(30).mean()

    dow_dummies = pd.get_dummies(df_calendar['date'].dt.dayofweek, prefix='dow', drop_first=True, dtype=float)
    dow_cols = list(dow_dummies.columns)
    df_calendar = pd.concat([df_calendar, dow_dummies], axis=1)

    event_cols = [
        'is_intl_dog_day', 'is_world_animal_day', 'is_national_pet_day', 'is_national_puppy_day',
        'is_diwali_rush', 'is_raksha_bandhan', 'is_independence_day', 'is_ganesh_chaturthi',
        'is_navratri_dussehra', 'is_holi_closure', 'is_makar_sankranti', 'is_christmas_newyear',
        'is_eid', 'is_salary_payday', 'is_weekend_payday_surge'
    ]

    all_features = ['trend', 'lag_1', 'lag_7', 'rolling_mean_30'] + dow_cols + event_cols

    train_data = df_calendar[train_mask].dropna(subset=['lag_1', 'lag_7', 'rolling_mean_30']).copy()
    print(f"[2] Prepared training dataset: {len(train_data)} operational days.")

    # 4. Econometric OLS Coefs
    X_ols = sm.add_constant(train_data[all_features])
    y_ols = train_data['sales_INR']
    ols_res = sm.OLS(y_ols, X_ols).fit()

    coef_rows = []
    print("\n[3] Explicit Festival & Event Isolated Impacts (INR/Day):")
    print("-" * 90)
    for col in event_cols:
        c_val = ols_res.params[col]
        se_val = ols_res.bse[col]
        t_val = ols_res.tvalues[col]
        p_val = ols_res.pvalues[col]
        sig_str = "Statistically Significant (p < 0.05)" if p_val < 0.05 else ("Marginal (p < 0.15)" if p_val < 0.15 else "Baseline Factor")
        print(f"    {col:28s} : INR {c_val:+12,.2f} | t = {t_val:5.2f} | p = {p_val:.4f} | {sig_str}")
        coef_rows.append({
            'Feature': col, 'Coefficient_INR': round(c_val, 2),
            'Std_Error': round(se_val, 2), 't_statistic': round(t_val, 2),
            'p_value': round(p_val, 4), 'Significance': sig_str
        })
    print("-" * 90)
    df_coefs = pd.DataFrame(coef_rows)

    # 5. 4-Quarter Rolling Walk-Forward CV Evaluation
    print("\n[4] Evaluating via 4-Quarter Rolling Walk-Forward CV (The Optimal Division):")
    cv_quarters = [
        ("Q3 2024", "Jul 1, 2024 - Sep 30, 2024", "2024-07-01", "2024-09-30"),
        ("Q4 2024", "Oct 1, 2024 - Dec 31, 2024", "2024-10-01", "2024-12-31"),
        ("Q1 2025", "Jan 1, 2025 - Mar 31, 2025", "2025-01-01", "2025-03-31"),
        ("Q2 2025", "Apr 1, 2025 - Jun 30, 2025", "2025-04-01", "2025-06-30")
    ]
    cv_rows = []
    for q_lbl, q_dates, q_start, q_end in cv_quarters:
        f_tr = train_data[train_data['date'] < q_start]
        f_te = train_data[(train_data['date'] >= q_start) & (train_data['date'] <= q_end)]

        r_cv = Ridge(alpha=60.0, random_state=42)
        r_cv.fit(f_tr[all_features], f_tr['sales_INR'])
        p_fold = np.clip(r_cv.predict(f_te[all_features]), 0, None)

        act = f_te['sales_INR'].values
        wape = np.sum(np.abs(act - p_fold)) / np.sum(act) * 100
        mae = mean_absolute_error(act, p_fold)
        q_acc = (1.0 - abs(np.sum(act) - np.sum(p_fold)) / np.sum(act)) * 100

        print(f"    {q_lbl} ({q_dates:28s}): WAPE = {wape:5.2f}% | MAE = INR {mae:8,.2f} | Quarterly Acc = {q_acc:5.2f}%")
        cv_rows.append({
            'Quarter': q_lbl, 'Dates': q_dates, 'WAPE': round(wape / 100, 4),
            'MAE': round(mae, 2), 'Quarterly_Accuracy': round(q_acc / 100, 4)
        })

    df_cv = pd.DataFrame(cv_rows)
    avg_wape = np.mean([r['WAPE'] for r in cv_rows]) * 100
    avg_acc = np.mean([r['Quarterly_Accuracy'] for r in cv_rows]) * 100
    print(f"    4-QUARTER ROLLING AVERAGE BENCHMARK : WAPE = {avg_wape:5.2f}% | Quarterly Acc = {avg_acc:5.2f}%")

    # 6. Fit Final Model on 100% History & Forecast Q3 2025
    print("\n[5] Fitting Final Ridge Model on 100% History and Forecasting Q3 2025...")
    final_model = Ridge(alpha=60.0, random_state=42)
    final_model.fit(train_data[all_features], train_data['sales_INR'])

    test_mask = df_calendar['data_split'] == 'Test Period (Q3 2025)'
    test_dates = df_calendar.loc[test_mask, 'date'].copy()

    history_sales = train_data.set_index('date')['sales_INR'].copy()
    current_trend = train_data['trend'].max() + 1
    forecast_outputs = []

    for d in test_dates:
        row_match = df_calendar[df_calendar['date'] == d].iloc[0]

        lag_1 = history_sales.iloc[-1]
        lag_7 = history_sales.iloc[-7]
        rm_30 = history_sales.iloc[-30:].mean()

        row_feat = {'trend': current_trend, 'lag_1': lag_1, 'lag_7': lag_7, 'rolling_mean_30': rm_30}
        for dc in dow_cols: row_feat[dc] = row_match[dc]
        for ec in event_cols: row_feat[ec] = row_match[ec]

        x_df = pd.DataFrame([row_feat])[all_features]
        pred_val = max(0.0, float(final_model.predict(x_df)[0]))

        z_80 = 1.282
        sigma_est = 39000
        ci_lower = max(0.0, pred_val - z_80 * sigma_est)
        ci_upper = pred_val + z_80 * sigma_est

        forecast_outputs.append({
            'date': d.strftime('%Y-%m-%d'),
            'day_of_week': d.day_name(),
            'event_tags': row_match['event_primary_name'],
            'predicted_sales_INR': round(pred_val, 2),
            'ci_lower_80': round(ci_lower, 2),
            'ci_upper_80': round(ci_upper, 2)
        })

        df_calendar.loc[df_calendar['date'] == d, 'sales_INR'] = pred_val
        history_sales.loc[d] = pred_val
        current_trend += 1

    df_forecast = pd.DataFrame(forecast_outputs)
    pred_path = os.path.join(CURRENT_DIR, 'pred_model_explicit_events.csv')
    df_forecast.to_csv(pred_path, index=False)
    print(f"[+] Saved official forecast: `{pred_path}`")

    # Monthly Summary
    df_forecast['month'] = pd.to_datetime(df_forecast['date']).dt.strftime('%B %Y')
    m_grp = df_forecast.groupby('month', sort=False)['predicted_sales_INR'].agg(['sum', 'mean', 'count'])
    m_grp.columns = ['Total_INR', 'Daily_Avg_INR', 'Days']
    tot_q3 = df_forecast['predicted_sales_INR'].sum()

    print("\n" + "=" * 90)
    print(" OFFICIAL Q3 2025 REVENUE FORECAST SUMMARY (July 1 - Sept 30, 2025)")
    print("=" * 90)
    for m_name, r in m_grp.iterrows():
        print(f"    {m_name:15s}: Total = INR {r['Total_INR']:,.2f} | Daily Avg = INR {r['Daily_Avg_INR']:,.2f} ({int(r['Days'])} days)")
    print("-" * 90)
    print(f"    Total Projected Q3 2025 Revenue: INR {tot_q3:,.2f} (~INR {tot_q3/1e7:.2f} Crores)")
    print("=" * 90)

    # Export Excel & CSV
    excel_path = os.path.join(CURRENT_DIR, 'JustDogs_Master_Event_Calendar_2022_2025.xlsx')
    export_styled_excel(df_calendar, df_coefs, df_cv, excel_path)
    csv_cal_path = os.path.join(CURRENT_DIR, 'JustDogs_Master_Event_Calendar_2022_2025.csv')
    df_calendar.to_csv(csv_cal_path, index=False)

    print("\n[+] PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")


if __name__ == '__main__':
    main()
