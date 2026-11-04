"""
=============================================================================
TOD310 - Predictive Analytics for Business
Human-in-the-Loop Stream: Top-5 Product Sales & Demand Forecasting (Q3 2025)
=============================================================================
Author: Arth Patel (Human Steering) + AI Execution
Description:
    Forecasting daily and monthly demand (units) and revenue (sales in INR)
    for the Top 5 Products of JustDogs for July 1 to September 30, 2025.

    Covers BOTH definitions:
      1. Top 5 Products by Revenue (Sales in INR - High-Ticket Nutrition & Equipment)
      2. Top 5 Products by Volume Demand (Units Sold - Fast-Moving Treats & Essentials)

    Methodology:
      - Bottom-up SKU daily time-series feature engineering with the verified
        Event-Aware Calendar (festivals, animal days, salary restock cycles).
      - Autoregressive lag modeling with regularized Ridge regression.
      - Hierarchical reconciliation with store-level macro run-rate.
      - Offline vs. Online channel unit breakdown.
      - Exports predictions to CSV, updates the Master Excel workbook, and plots.
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
from sklearn.metrics import mean_absolute_error, r2_score

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PLOT_DIR = os.path.join(CURRENT_DIR, 'plots')
os.makedirs(PLOT_DIR, exist_ok=True)


def load_and_identify_top_products():
    csv_path = os.path.join(CURRENT_DIR, 'sales_daily_train.csv')
    df_raw = pd.read_csv(csv_path)
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%d-%m-%Y')
    df_raw['total_units'] = df_raw['units_sold_offline'] + df_raw['units_sold_online']

    # Focus on active products over the last 12 months (July 2024 - June 2025)
    recent_mask = df_raw['date'] >= '2024-07-01'
    df_recent = df_raw[recent_mask]

    # Top 5 by Revenue
    top_revenue_pids = df_recent.groupby('product_id')['sales (INR)'].sum().nlargest(5).index.tolist()

    # Top 5 by Unit Demand
    top_volume_pids = df_recent.groupby('product_id')['total_units'].sum().nlargest(5).index.tolist()

    return df_raw, top_revenue_pids, top_volume_pids


def build_event_features(dates):
    d_idx = pd.DatetimeIndex(dates)
    df_ev = pd.DataFrame(index=d_idx)
    df_ev['day_of_week'] = d_idx.dayofweek
    df_ev['day_of_month'] = d_idx.day
    df_ev['month'] = d_idx.month
    df_ev['is_weekend'] = df_ev['day_of_week'].isin([5, 6]).astype(float)

    # Day of week dummies
    dow_dum = pd.get_dummies(df_ev['day_of_week'], prefix='dow', drop_first=True, dtype=float)
    dow_dum.index = d_idx
    df_ev = pd.concat([df_ev, dow_dum], axis=1)

    # Key Events
    df_ev['is_dog_day'] = ((d_idx.month == 8) & (d_idx.day >= 24) & (d_idx.day <= 27)).astype(float)
    df_ev['is_payday'] = ((d_idx.day >= 28) | (d_idx.day <= 3)).astype(float)
    df_ev['weekend_x_payday'] = df_ev['is_weekend'] * df_ev['is_payday']

    # Festivals
    rakhi_mask = (
        ((d_idx >= '2023-08-28') & (d_idx <= '2023-08-31')) |
        ((d_idx >= '2024-08-17') & (d_idx <= '2024-08-20')) |
        ((d_idx >= '2025-08-07') & (d_idx <= '2025-08-10'))
    )
    df_ev['is_rakhi'] = rakhi_mask.astype(float)

    ganesh_mask = (
        ((d_idx >= '2022-08-31') & (d_idx <= '2022-09-03')) |
        ((d_idx >= '2023-09-18') & (d_idx <= '2023-09-21')) |
        ((d_idx >= '2024-09-06') & (d_idx <= '2024-09-09')) |
        ((d_idx >= '2025-08-27') & (d_idx <= '2025-08-30'))
    )
    df_ev['is_ganesh'] = ganesh_mask.astype(float)

    nav_mask = (
        ((d_idx >= '2022-09-26') & (d_idx <= '2022-10-05')) |
        ((d_idx >= '2023-10-15') & (d_idx <= '2023-10-24')) |
        ((d_idx >= '2024-10-03') & (d_idx <= '2024-10-12')) |
        ((d_idx >= '2025-09-22') & (d_idx <= '2025-10-01'))
    )
    df_ev['is_navratri'] = nav_mask.astype(float)

    diwali_mask = (
        ((d_idx >= '2022-10-21') & (d_idx <= '2022-10-27')) |
        ((d_idx >= '2023-11-09') & (d_idx <= '2023-11-15')) |
        ((d_idx >= '2024-10-28') & (d_idx <= '2024-11-03')) |
        ((d_idx >= '2025-10-17') & (d_idx <= '2025-10-23'))
    )
    df_ev['is_diwali'] = diwali_mask.astype(float)

    return df_ev


def forecast_sku(df_raw, pid, metric_col='sales (INR)'):
    """
    Builds a bottom-up time series model for an individual SKU.
    metric_col can be 'sales (INR)' or 'total_units'.
    """
    # Extract SKU historical series
    sku_df = df_raw[df_raw['product_id'] == pid].groupby('date')[metric_col].sum()
    all_dates = pd.date_range('2022-09-05', '2025-06-30', freq='D')
    sku_daily = sku_df.reindex(all_dates, fill_value=0.0).to_frame(name=metric_col)

    sku_daily['trend'] = np.arange(len(sku_daily))
    sku_daily['lag_1'] = sku_daily[metric_col].shift(1)
    sku_daily['lag_7'] = sku_daily[metric_col].shift(7)
    sku_daily['rolling_mean_30'] = sku_daily[metric_col].shift(1).rolling(30).mean()

    # Calendar & Event features
    ev_feats = build_event_features(sku_daily.index)
    full_train = pd.concat([sku_daily, ev_feats], axis=1).dropna()

    feat_cols = [c for c in full_train.columns if c != metric_col]

    # Fit Ridge
    m = Ridge(alpha=40.0, random_state=42)
    m.fit(full_train[feat_cols], full_train[metric_col])

    # Out-of-sample Forecast (July 1 - Sept 30, 2025)
    test_dates = pd.date_range('2025-07-01', '2025-09-30', freq='D')
    test_ev = build_event_features(test_dates)

    history = full_train[metric_col].copy()
    curr_trend = full_train['trend'].max() + 1
    forecast_values = []

    for d in test_dates:
        lag_1 = history.iloc[-1]
        lag_7 = history.iloc[-7]
        rm_30 = history.iloc[-30:].mean()

        row_dict = {
            'trend': curr_trend,
            'lag_1': lag_1,
            'lag_7': lag_7,
            'rolling_mean_30': rm_30
        }
        for c in test_ev.columns:
            row_dict[c] = test_ev.loc[d, c]

        x_row = pd.DataFrame([row_dict])[feat_cols]
        pred = max(0.0, float(m.predict(x_row)[0]))
        forecast_values.append(pred)

        history.loc[d] = pred
        curr_trend += 1

    df_res = pd.DataFrame({
        'date': test_dates,
        'product_id': pid,
        metric_col: forecast_values
    })
    return df_res


def run_top_products_pipeline():
    print("=" * 100)
    print(" TOD310: TOP-5 PRODUCT SALES & DEMAND FORECASTING (Q3 2025)")
    print("=" * 100)

    df_raw, top_rev_pids, top_vol_pids = load_and_identify_top_products()

    print(f"\n[1] Identified Top 5 Products by REVENUE (Sales in INR):")
    for rank, pid in enumerate(top_rev_pids, 1):
        recent_s = df_raw[(df_raw['product_id'] == pid) & (df_raw['date'] >= '2024-07-01')]['sales (INR)'].sum()
        recent_u = df_raw[(df_raw['product_id'] == pid) & (df_raw['date'] >= '2024-07-01')]['total_units'].sum()
        asp = recent_s / recent_u if recent_u else 0
        print(f"    Rank {rank}: {pid:7s} | Last 12m Sales: INR {recent_s:12,.2f} | Units: {recent_u:5,d} | ASP: INR {asp:8,.2f}")

    print(f"\n[2] Identified Top 5 Products by VOLUME DEMAND (Units Sold):")
    for rank, pid in enumerate(top_vol_pids, 1):
        recent_s = df_raw[(df_raw['product_id'] == pid) & (df_raw['date'] >= '2024-07-01')]['sales (INR)'].sum()
        recent_u = df_raw[(df_raw['product_id'] == pid) & (df_raw['date'] >= '2024-07-01')]['total_units'].sum()
        asp = recent_s / recent_u if recent_u else 0
        print(f"    Rank {rank}: {pid:7s} | Last 12m Demand: {recent_u:6,d} units | Sales: INR {recent_s:10,.2f} | ASP: INR {asp:6,.2f}")

    # Combine unique list of top products to forecast
    target_pids = list(dict.fromkeys(top_rev_pids + top_vol_pids))

    # Calculate channel ratios and ASP per SKU
    sku_ratios = {}
    for pid in target_pids:
        sub = df_raw[(df_raw['product_id'] == pid) & (df_raw['date'] >= '2024-07-01')]
        if len(sub) == 0:
            sub = df_raw[df_raw['product_id'] == pid]
        tot_u = sub['total_units'].sum()
        tot_s = sub['sales (INR)'].sum()
        asp = tot_s / tot_u if tot_u > 0 else 100.0
        off_ratio = sub['units_sold_offline'].sum() / tot_u if tot_u > 0 else 0.90
        sku_ratios[pid] = {'asp': asp, 'off_ratio': off_ratio}

    print("\n[3] Fitting Bottom-Up Event-Aware Time Series Models for Top SKUs...")
    all_daily_records = []

    for pid in target_pids:
        # Forecast Sales
        df_pred_sales = forecast_sku(df_raw, pid, metric_col='sales (INR)')
        # Forecast Units
        df_pred_units = forecast_sku(df_raw, pid, metric_col='total_units')

        asp = sku_ratios[pid]['asp']
        off_ratio = sku_ratios[pid]['off_ratio']

        for i in range(len(df_pred_sales)):
            dt = df_pred_sales['date'].iloc[i]
            s_val = round(df_pred_sales['sales (INR)'].iloc[i], 2)
            u_raw = df_pred_units['total_units'].iloc[i]

            # For volume SKUs (ASP < 200), demand model is direct;
            # for high-ticket SKUs (ASP >= 200), reconcile unit rate with revenue
            if asp < 200:
                u_day = max(0.0, u_raw)
            else:
                u_day = s_val / asp if asp > 0 else u_raw

            category = "Top Revenue SKU" if pid in top_rev_pids else "Top Volume Demand SKU"

            all_daily_records.append({
                'date': dt.strftime('%Y-%m-%d'),
                'month': dt.strftime('%B %Y'),
                'product_id': pid,
                'sku_category': category,
                'predicted_sales_INR': s_val,
                'predicted_units_continuous': u_day,
                'estimated_asp_INR': round(asp, 2),
                'off_ratio': off_ratio
            })

    df_top_daily = pd.DataFrame(all_daily_records)

    # 4. Monthly Rollup
    df_monthly = df_top_daily.groupby(['product_id', 'sku_category', 'month'], sort=False).agg({
        'predicted_sales_INR': 'sum',
        'predicted_units_continuous': 'sum',
        'estimated_asp_INR': 'mean',
        'off_ratio': 'mean'
    }).reset_index()

    # Calculate clean integer unit demand and channel splits
    df_monthly['predicted_total_units'] = df_monthly['predicted_units_continuous'].round().astype(int)
    df_monthly['predicted_units_offline'] = (df_monthly['predicted_total_units'] * df_monthly['off_ratio']).round().astype(int)
    df_monthly['predicted_units_online'] = df_monthly['predicted_total_units'] - df_monthly['predicted_units_offline']
    df_monthly = df_monthly.drop(columns=['predicted_units_continuous', 'off_ratio'])

    # Daily integer distribution
    df_top_daily['predicted_total_units'] = df_top_daily['predicted_units_continuous'].round(2)
    df_top_daily['predicted_units_offline'] = (df_top_daily['predicted_total_units'] * df_top_daily['off_ratio']).round(2)
    df_top_daily['predicted_units_online'] = (df_top_daily['predicted_total_units'] - df_top_daily['predicted_units_offline']).round(2)
    df_top_daily = df_top_daily.drop(columns=['predicted_units_continuous', 'off_ratio'])

    # Reorder months
    month_order = ['July 2025', 'August 2025', 'September 2025']
    df_monthly['month_cat'] = pd.Categorical(df_monthly['month'], categories=month_order, ordered=True)
    df_monthly = df_monthly.sort_values(['sku_category', 'product_id', 'month_cat']).drop(columns=['month_cat'])

    # Q3 Totals per SKU
    df_q3_totals = df_top_daily.groupby(['product_id', 'sku_category'], sort=False).agg({
        'predicted_sales_INR': 'sum',
        'predicted_total_units': 'sum',
        'predicted_units_offline': 'sum',
        'predicted_units_online': 'sum',
        'estimated_asp_INR': 'mean'
    }).reset_index()

    print("\n" + "=" * 105)
    print(" TOP 5 REVENUE SKUs: OFFICIAL Q3 2025 MONTH-BY-MONTH FORECAST")
    print("=" * 105)
    print(f"{'Product ID':12s} | {'Month':16s} | {'Predicted Sales (INR)':24s} | {'Demand (Units)':15s} | {'Offline':8s} | {'Online':8s}")
    print("-" * 105)
    for _, r in df_monthly[df_monthly['sku_category'] == 'Top Revenue SKU'].iterrows():
        print(f"{r['product_id']:12s} | {r['month']:16s} | INR {r['predicted_sales_INR']:18,.2f} | {r['predicted_total_units']:10,d} units | {r['predicted_units_offline']:6,d} | {r['predicted_units_online']:6,d}")
    print("-" * 105)

    print("\n" + "=" * 105)
    print(" TOP 5 VOLUME DEMAND SKUs: OFFICIAL Q3 2025 MONTH-BY-MONTH FORECAST")
    print("=" * 105)
    print(f"{'Product ID':12s} | {'Month':16s} | {'Predicted Sales (INR)':24s} | {'Demand (Units)':15s} | {'Offline':8s} | {'Online':8s}")
    print("-" * 105)
    for _, r in df_monthly[df_monthly['sku_category'] == 'Top Volume Demand SKU'].iterrows():
        print(f"{r['product_id']:12s} | {r['month']:16s} | INR {r['predicted_sales_INR']:18,.2f} | {r['predicted_total_units']:10,d} units | {r['predicted_units_offline']:6,d} | {r['predicted_units_online']:6,d}")
    print("=" * 105)

    # 5. Export CSV
    csv_out = os.path.join(CURRENT_DIR, 'pred_top_products_q3_2025.csv')
    df_monthly.to_csv(csv_out, index=False)
    print(f"\n[+] Saved monthly product forecast CSV: `{csv_out}`")

    daily_csv_out = os.path.join(CURRENT_DIR, 'pred_top_products_daily_q3_2025.csv')
    df_top_daily.to_csv(daily_csv_out, index=False)
    print(f"[+] Saved daily product forecast CSV: `{daily_csv_out}`")

    # 6. Update Master Excel Workbook (Add 'Top Products Forecast' sheet)
    excel_path = os.path.join(CURRENT_DIR, 'JustDogs_Master_Event_Calendar_2022_2025.xlsx')
    if os.path.exists(excel_path):
        wb = openpyxl.load_workbook(excel_path)
        if "Top Products Forecast" in wb.sheetnames:
            del wb["Top Products Forecast"]

        ws_prod = wb.create_sheet(title="Top Products Forecast")

        # Styling
        header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        data_font = Font(name="Segoe UI", size=10)
        bold_font = Font(name="Segoe UI", size=10, bold=True)
        thin_border = Border(
            left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9')
        )

        headers = ["Product ID", "Category", "Forecast Month", "Predicted Sales (INR)", "Total Demand (Units)", "Offline Units", "Online Units", "ASP (INR)"]
        ws_prod.append(headers)
        for cell in ws_prod[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        ws_prod.row_dimensions[1].height = 26

        for r in df_monthly.itertuples(index=False):
            ws_prod.append(list(r))
            curr_row = ws_prod.max_row
            for c_idx, val in enumerate(r, 1):
                cell = ws_prod.cell(row=curr_row, column=c_idx)
                cell.font = data_font
                cell.border = thin_border
                if c_idx in [1, 2, 3]:
                    cell.alignment = Alignment(horizontal="center")
                elif c_idx == 4:
                    cell.number_format = '#,##0.00'
                    cell.alignment = Alignment(horizontal="right")
                    cell.font = bold_font
                elif c_idx in [5, 6, 7]:
                    cell.number_format = '#,##0'
                    cell.alignment = Alignment(horizontal="right")
                elif c_idx == 8:
                    cell.number_format = '#,##0.00'
                    cell.alignment = Alignment(horizontal="right")

        for col in ws_prod.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws_prod.column_dimensions[col_letter].width = max(max_len + 4, 15)

        wb.save(excel_path)
        print(f"[+] Updated Master Excel Workbook with 'Top Products Forecast' sheet: `{excel_path}`")

    # 7. Generate Plot: Top Products Monthly Sales & Demand
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Panel 1: Revenue SKUs by Month
    rev_pivot = df_monthly[df_monthly['sku_category'] == 'Top Revenue SKU'].pivot(index='product_id', columns='month', values='predicted_sales_INR')
    rev_pivot = rev_pivot[['July 2025', 'August 2025', 'September 2025']]
    rev_pivot.plot(kind='bar', ax=axes[0], colormap='Blues', edgecolor='black', width=0.75)
    axes[0].set_title('Top 5 Products by Revenue: Monthly Forecast (INR)', fontsize=12, fontweight='bold', pad=10)
    axes[0].set_ylabel('Projected Revenue (INR)', fontsize=11, fontweight='bold')
    axes[0].set_xlabel('Product ID (High-Value Nutrition & Supplies)', fontsize=11, fontweight='bold')
    axes[0].tick_params(axis='x', rotation=0)
    axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x*1e-3:.0f}k' if x < 1e5 else f'₹{x*1e-5:.1f}L'))
    axes[0].legend(frameon=True, facecolor='white', loc='upper right')

    # Panel 2: Volume Demand SKUs by Month
    vol_pivot = df_monthly[df_monthly['sku_category'] == 'Top Volume Demand SKU'].pivot(index='product_id', columns='month', values='predicted_total_units')
    vol_pivot = vol_pivot[['July 2025', 'August 2025', 'September 2025']]
    vol_pivot.plot(kind='bar', ax=axes[1], colormap='Greens', edgecolor='black', width=0.75)
    axes[1].set_title('Top 5 Products by Demand Volume: Monthly Forecast (Units)', fontsize=12, fontweight='bold', pad=10)
    axes[1].set_ylabel('Projected Units Sold', fontsize=11, fontweight='bold')
    axes[1].set_xlabel('Product ID (Fast-Moving Treats & Biscuits)', fontsize=11, fontweight='bold')
    axes[1].tick_params(axis='x', rotation=0)
    axes[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,d}'))
    axes[1].legend(frameon=True, facecolor='white', loc='upper right')

    plt.tight_layout()
    p_prod = os.path.join(PLOT_DIR, 'top_products_sales_demand_forecast.png')
    plt.savefig(p_prod, dpi=300)
    plt.close()
    print(f"[+] Saved Top Products Forecast Plot: `{p_prod}`")

    # Also copy to Arth's folder in TOD310_JustDogs_Forecasting_Project
    arth_dir = os.path.join(os.path.dirname(CURRENT_DIR), 'TOD310_JustDogs_Forecasting_Project', 'Arth')
    if os.path.exists(arth_dir):
        import shutil
        shutil.copy(csv_out, os.path.join(arth_dir, 'pred_top_products_q3_2025.csv'))
        shutil.copy(daily_csv_out, os.path.join(arth_dir, 'pred_top_products_daily_q3_2025.csv'))
        shutil.copy(excel_path, os.path.join(arth_dir, 'JustDogs_Master_Event_Calendar_2022_2025.xlsx'))
        shutil.copy(p_prod, os.path.join(arth_dir, 'plots', 'top_products_sales_demand_forecast.png'))
        print(f"[+] Synced product forecasts & Excel to Arth's GitHub folder: `{arth_dir}`")


if __name__ == '__main__':
    run_top_products_pipeline()
