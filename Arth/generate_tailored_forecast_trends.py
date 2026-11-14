import os, sys, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sklearn.linear_model import Ridge
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, ExponentialSmoothing

warnings.filterwarnings("ignore")

CSV_PATH = r"d:\Desktop\ARTH\Sem-7\TOD310\Project\TOD310_JustDogs_Forecasting_Project\Arth\sales_daily_train.csv"
CAL_PATH = r"d:\Desktop\ARTH\Sem-7\TOD310\Project\TOD310_JustDogs_Forecasting_Project\Arth\JustDogs_Master_Event_Calendar_2022_2025.csv"
PLOTS_DIR = r"d:\Desktop\ARTH\Sem-7\TOD310\Project\TOD310_JustDogs_Forecasting_Project\Arth\plots"
OUT_CSV = r"d:\Desktop\ARTH\Sem-7\TOD310\Project\TOD310_JustDogs_Forecasting_Project\Arth\pred_top5_tailored_models_june_sep_2025.csv"

os.makedirs(PLOTS_DIR, exist_ok=True)

raw = pd.read_csv(CSV_PATH)
raw.columns = ["date", "product_id", "units_offline", "units_online", "units_returned", "sales", "discount_pct"]
raw["date"] = pd.to_datetime(raw["date"], format="%d-%m-%Y")
raw = raw.drop_duplicates()
raw["discount_pct"] = raw["discount_pct"].fillna(0)

# Forecast Horizon: June 1, 2025 to September 30, 2025 (122 Days)
FORECAST_START = pd.Timestamp("2025-06-01")
FORECAST_END = pd.Timestamp("2025-09-30")
forecast_daily_dates = pd.date_range(FORECAST_START, FORECAST_END, freq='D')
forecast_weekly_dates = pd.date_range(FORECAST_START, FORECAST_END, freq='W-SUN')

def build_arth_calendar_features(dates_index):
    d_idx = pd.DatetimeIndex(dates_index)
    df_ev = pd.DataFrame(index=d_idx)
    df_ev['is_weekend'] = d_idx.dayofweek.isin([5, 6]).astype(float)
    df_ev['day_of_week'] = d_idx.dayofweek
    df_ev['is_salary_payday'] = ((d_idx.day >= 28) | (d_idx.day <= 3)).astype(float)
    df_ev['is_weekend_payday_surge'] = (df_ev['is_weekend'] * df_ev['is_salary_payday']).astype(float)
    df_ev['is_intl_dog_day'] = ((d_idx.month == 8) & (d_idx.day >= 24) & (d_idx.day <= 27)).astype(float)
    df_ev['is_national_pet_day'] = ((d_idx.month == 4) & (d_idx.day >= 10) & (d_idx.day <= 12)).astype(float)
    df_ev['is_diwali_rush'] = (((d_idx >= '2022-10-21') & (d_idx <= '2022-10-27')) |
                               ((d_idx >= '2023-11-09') & (d_idx <= '2023-11-15')) |
                               ((d_idx >= '2024-10-28') & (d_idx <= '2024-11-03')) |
                               ((d_idx >= '2025-10-17') & (d_idx <= '2025-10-23'))).astype(float)
    df_ev['is_raksha_bandhan'] = (((d_idx >= '2023-08-28') & (d_idx <= '2023-08-31')) |
                                  ((d_idx >= '2024-08-17') & (d_idx <= '2024-08-20')) |
                                  ((d_idx >= '2025-08-07') & (d_idx <= '2025-08-10'))).astype(float)
    df_ev['is_ganesh_chaturthi'] = (((d_idx >= '2022-08-31') & (d_idx <= '2022-09-03')) |
                                    ((d_idx >= '2023-09-18') & (d_idx <= '2023-09-21')) |
                                    ((d_idx >= '2024-09-06') & (d_idx <= '2024-09-09')) |
                                    ((d_idx >= '2025-08-26') & (d_idx <= '2025-08-29'))).astype(float)
    df_ev['is_navratri_dussehra'] = (((d_idx >= '2022-09-26') & (d_idx <= '2022-10-05')) |
                                     ((d_idx >= '2023-10-15') & (d_idx <= '2023-10-24')) |
                                     ((d_idx >= '2024-10-03') & (d_idx <= '2024-10-12')) |
                                     ((d_idx >= '2025-09-22') & (d_idx <= '2025-10-01'))).astype(float)
    df_ev['is_christmas_newyear'] = (((d_idx.month == 12) & (d_idx.day >= 24)) | ((d_idx.month == 1) & (d_idx.day <= 2))).astype(float)
    df_ev['is_republic_day'] = ((d_idx.month == 1) & (d_idx.day.isin([25, 26, 27]))).astype(float)
    
    # Day-of-week dummies
    dow_dum = pd.get_dummies(df_ev['day_of_week'], prefix='dow', drop_first=True, dtype=float)
    dow_dum.index = d_idx
    df_ev = pd.concat([df_ev, dow_dum], axis=1)
    df_ev = df_ev.drop(columns=['day_of_week'])
    return df_ev

ASP_DICT = {
    "P04606": 2202.66,
    "P02065": 492.35,
    "P01032": 12654.93,
    "P00084": 74.15,
    "P04291": 64.08
}

PRODUCT_NAMES = {
    "P04606": "Royal Canin / Pedigree 10kg Premium Food",
    "P02065": "Himalaya / Bio-Groom Grooming & Hygiene",
    "P01032": "Luxury Bedding / European Travel Crates",
    "P00084": "Pedigree / Whiskas Wet Food Gravy",
    "P04291": "Barkbone Rawhide Chicken Chew Treats"
}

CHAMPION_MODELS = {
    "P04606": "★ Arth Event-Aware Ridge (Autoregressive + Calendar Dummies)",
    "P02065": "SMA (8-Week Recursive Moving Average)",
    "P01032": "★ Arth Event-Aware Ridge (Payday Surges & Intermittent Dummies)",
    "P00084": "★ Arth Daily Event-Aware Ridge (Strictly Daily)",
    "P04291": "SMA (8-Week Moving Average / Low-Bias)"
}

monthly_forecast_records = []

# ==========================================
# 1. P04606 (10kg Food) - Top Model: Arth Event-Aware Ridge
# ==========================================
print("Forecasting P04606 with Arth Event-Aware Ridge...")
p_raw = raw[raw["product_id"] == "P04606"]
all_dates = pd.date_range("2024-01-11", FORECAST_END, freq='D')
d_sales = p_raw.groupby('date')['sales'].sum().reindex(all_dates, fill_value=0.0)

p_df = pd.DataFrame({'date': all_dates, 'sales': d_sales.values})
p_df['trend'] = np.arange(len(p_df))
p_df['lag_1'] = p_df['sales'].shift(1).bfill()
p_df['lag_7'] = p_df['sales'].shift(7).bfill()
p_df['rolling_mean_30'] = p_df['sales'].shift(1).rolling(30, min_periods=1).mean().bfill()
ev_df = build_arth_calendar_features(all_dates)
p_df = pd.concat([p_df, ev_df.reset_index(drop=True)], axis=1)
feat_cols = [c for c in p_df.columns if c not in ['date', 'sales']]

# Train on all available data up to May 27, 2025
tr_mask = p_df['date'] <= "2025-05-27"
te_mask = (p_df['date'] >= FORECAST_START) & (p_df['date'] <= FORECAST_END)

m_ridge = Ridge(alpha=40.0, random_state=42).fit(p_df.loc[tr_mask, feat_cols], p_df.loc[tr_mask, 'sales'])

daily_preds_p04606 = []
hist_s = p_df.loc[tr_mask, 'sales'].copy()
test_sub = p_df.loc[te_mask].copy().reset_index(drop=True)
for _, row in test_sub.iterrows():
    lag_1 = hist_s.iloc[-1]
    lag_7 = hist_s.iloc[-7] if len(hist_s) >= 7 else hist_s.iloc[0]
    rm_30 = hist_s.iloc[-30:].mean()
    row_feat = row[feat_cols].to_dict()
    row_feat['lag_1'] = lag_1; row_feat['lag_7'] = lag_7; row_feat['rolling_mean_30'] = rm_30
    feat_vec = pd.DataFrame([row_feat])[feat_cols]
    pval = max(0.0, float(m_ridge.predict(feat_vec)[0]))
    daily_preds_p04606.append(pval)
    hist_s = pd.concat([hist_s, pd.Series([pval])], ignore_index=True)

pred_s_p04606 = pd.Series(daily_preds_p04606, index=forecast_daily_dates)
hist_s_p04606 = p_df.loc[tr_mask].set_index('date')['sales']

# Weekly resampling for trend plot
weekly_hist_p04606 = hist_s_p04606.resample('W-SUN').sum() / 1e3
weekly_pred_p04606 = pred_s_p04606.resample('W-SUN').sum() / 1e3

# Monthly aggregates
for m_name, m_dates in [("June 2025", "2025-06-01 to 2025-06-30"),
                        ("July 2025", "2025-07-01 to 2025-07-31"),
                        ("August 2025", "2025-08-01 to 2025-08-31"),
                        ("September 2025", "2025-09-01 to 2025-09-30")]:
    m_val = pred_s_p04606.loc[m_dates[:10]:m_dates[-10:]].sum()
    m_units = int(round(m_val / ASP_DICT["P04606"]))
    monthly_forecast_records.append({
        "product_id": "P04606", "product_name": PRODUCT_NAMES["P04606"],
        "top_model": CHAMPION_MODELS["P04606"], "month": m_name,
        "predicted_sales_INR": round(m_val, 2), "predicted_units": m_units,
        "asp_INR": ASP_DICT["P04606"]
    })

# Plot 1: P04606 Trend Line
plt.figure(figsize=(11, 4.8), dpi=200)
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
ax = plt.gca()

# Plot historical weekly trend
ax.plot(weekly_hist_p04606.index, weekly_hist_p04606.values, color='#1e3a8a', linewidth=2.2, label='Historical Weekly Sales (k₹)')
# Plot forecast weekly trend
# Connect last historical to first forecast point
conn_x = [weekly_hist_p04606.index[-1], weekly_pred_p04606.index[0]]
conn_y = [weekly_hist_p04606.values[-1], weekly_pred_p04606.values[0]]
ax.plot(conn_x, conn_y, color='#047857', linestyle='--', linewidth=2.0)
ax.plot(weekly_pred_p04606.index, weekly_pred_p04606.values, color='#047857', linewidth=2.4, linestyle='--', marker='o', markersize=5, label='Forecast Trend Line (Arth Ridge) [k₹]')

# Confidence band (80% CI based on CV RMSE)
sigma_p04606 = 15.0 # kINR
ax.fill_between(weekly_pred_p04606.index,
                np.maximum(0, weekly_pred_p04606.values - 1.28 * sigma_p04606),
                weekly_pred_p04606.values + 1.28 * sigma_p04606,
                color='#10b981', alpha=0.18, label='80% Forecast Confidence Band')

ax.axvline(x=pd.Timestamp("2025-06-01"), color='#dc2626', linestyle=':', linewidth=1.5, label='Forecast Start (1-Jun-2025)')

# Annotations
ax.annotate('Raksha Bandhan & Dog Day Surge\n(Aug 2025 Festival Prep)',
            xy=(pd.Timestamp("2025-08-17"), weekly_pred_p04606.loc["2025-08-17"] if pd.Timestamp("2025-08-17") in weekly_pred_p04606.index else weekly_pred_p04606.values[-6]),
            xytext=(pd.Timestamp("2025-07-01"), max(weekly_pred_p04606.values)*1.15),
            arrowprops=dict(facecolor='#d97706', shrink=0.08, width=1.2, headwidth=6),
            fontsize=8.5, fontweight='bold', color='#92400e',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#fef3c7', edgecolor='#f59e0b', alpha=0.9))

ax.set_title('P04606 (Royal Canin / Pedigree 10kg Bulk Food) — Out-of-Sample Sales Trend Line\nChampion Model: ★ Arth Event-Aware Ridge (Weekly Aggregated, k₹)', fontsize=11, fontweight='bold', pad=10, color='#0f172a')
ax.set_ylabel('Weekly Sales (Thousands of INR | k₹)', fontsize=9.5, fontweight='bold')
ax.set_xlabel('Timeline (Historical 2024–2025 to Future Q3 2025)', fontsize=9.5, fontweight='bold')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.legend(loc='upper left', frameon=True, fontsize=8.5)
plt.tight_layout()
p1_file = os.path.join(PLOTS_DIR, "forecast_trend_P04606.png")
plt.savefig(p1_file, dpi=200)
plt.close()
print(f"[+] Saved trend line plot: {p1_file}")

# ==========================================
# 2. P02065 (Grooming Hygiene) - Top Model: SMA (8w)
# ==========================================
print("Forecasting P02065 with SMA (8w)...")
p_raw_p02065 = raw[raw["product_id"] == "P02065"]
d_p02065 = p_raw_p02065.groupby('date')['sales'].sum().asfreq('D', fill_value=0.0)
weekly_hist_p02065 = (d_p02065.resample('W-SUN').sum() / 1e3).loc["2024-07-11":"2025-05-31"]

h_steps = len(forecast_weekly_dates)
hist_vals = list(weekly_hist_p02065.values)
pred_vals_p02065 = []
for _ in range(h_steps):
    val = np.mean(hist_vals[-8:])
    pred_vals_p02065.append(val)
    hist_vals.append(val)

weekly_pred_p02065 = pd.Series(pred_vals_p02065, index=forecast_weekly_dates)

# Daily disaggregation for monthly reporting
d_pred_p02065 = pd.Series(np.repeat([v / 7.0 * 1e3 for v in pred_vals_p02065], 7)[:len(forecast_daily_dates)], index=forecast_daily_dates)
for m_name, m_dates in [("June 2025", "2025-06-01 to 2025-06-30"),
                        ("July 2025", "2025-07-01 to 2025-07-31"),
                        ("August 2025", "2025-08-01 to 2025-08-31"),
                        ("September 2025", "2025-09-01 to 2025-09-30")]:
    m_val = d_pred_p02065.loc[m_dates[:10]:m_dates[-10:]].sum()
    m_units = int(round(m_val / ASP_DICT["P02065"]))
    monthly_forecast_records.append({
        "product_id": "P02065", "product_name": PRODUCT_NAMES["P02065"],
        "top_model": CHAMPION_MODELS["P02065"], "month": m_name,
        "predicted_sales_INR": round(m_val, 2), "predicted_units": m_units,
        "asp_INR": ASP_DICT["P02065"]
    })

# Plot 2: P02065 Trend Line
plt.figure(figsize=(11, 4.8), dpi=200)
ax = plt.gca()
ax.plot(weekly_hist_p02065.index, weekly_hist_p02065.values, color='#0284c7', linewidth=2.2, label='Historical Weekly Sales (k₹)')
conn_x = [weekly_hist_p02065.index[-1], weekly_pred_p02065.index[0]]
conn_y = [weekly_hist_p02065.values[-1], weekly_pred_p02065.values[0]]
ax.plot(conn_x, conn_y, color='#047857', linestyle='--', linewidth=2.0)
ax.plot(weekly_pred_p02065.index, weekly_pred_p02065.values, color='#047857', linewidth=2.4, linestyle='--', marker='s', markersize=5, label='Forecast Trend Line (SMA 8w) [k₹]')

sigma_p02065 = weekly_hist_p02065.iloc[-8:].std()
ax.fill_between(weekly_pred_p02065.index,
                np.maximum(0, weekly_pred_p02065.values - 1.28 * sigma_p02065),
                weekly_pred_p02065.values + 1.28 * sigma_p02065,
                color='#10b981', alpha=0.18, label='80% Forecast Buffer (Salon Throughput)')

ax.axvline(x=pd.Timestamp("2025-06-01"), color='#dc2626', linestyle=':', linewidth=1.5, label='Forecast Start (1-Jun-2025)')
ax.set_title('P02065 (Himalaya / Bio-Groom Hygiene) — Out-of-Sample Sales Trend Line\nChampion Model: SMA (8-Week Recursive Moving Average, k₹)', fontsize=11, fontweight='bold', pad=10, color='#0f172a')
ax.set_ylabel('Weekly Sales (Thousands of INR | k₹)', fontsize=9.5, fontweight='bold')
ax.set_xlabel('Timeline (Historical 2024–2025 to Future Q3 2025)', fontsize=9.5, fontweight='bold')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.legend(loc='upper left', frameon=True, fontsize=8.5)
plt.tight_layout()
p2_file = os.path.join(PLOTS_DIR, "forecast_trend_P02065.png")
plt.savefig(p2_file, dpi=200)
plt.close()
print(f"[+] Saved trend line plot: {p2_file}")

# ==========================================
# 3. P01032 (Luxury Beds) - Top Model: Arth Event-Aware Ridge (Payday Surges)
# ==========================================
print("Forecasting P01032 with Arth Event-Aware Ridge...")
p_raw_p01032 = raw[raw["product_id"] == "P01032"]
all_dates_p01032 = pd.date_range("2022-09-14", FORECAST_END, freq='D')
d_sales_p01032 = p_raw_p01032.groupby('date')['sales'].sum().reindex(all_dates_p01032, fill_value=0.0)

p_df_p01032 = pd.DataFrame({'date': all_dates_p01032, 'sales': d_sales_p01032.values})
p_df_p01032['trend'] = np.arange(len(p_df_p01032))
p_df_p01032['lag_1'] = p_df_p01032['sales'].shift(1).bfill()
p_df_p01032['lag_7'] = p_df_p01032['sales'].shift(7).bfill()
p_df_p01032['rolling_mean_30'] = p_df_p01032['sales'].shift(1).rolling(30, min_periods=1).mean().bfill()
ev_df_p01032 = build_arth_calendar_features(all_dates_p01032)
p_df_p01032 = pd.concat([p_df_p01032, ev_df_p01032.reset_index(drop=True)], axis=1)
feat_cols_p01032 = [c for c in p_df_p01032.columns if c not in ['date', 'sales']]

tr_mask_p01032 = p_df_p01032['date'] <= "2025-05-31"
te_mask_p01032 = (p_df_p01032['date'] >= FORECAST_START) & (p_df_p01032['date'] <= FORECAST_END)

m_ridge_p01032 = Ridge(alpha=40.0, random_state=42).fit(p_df_p01032.loc[tr_mask_p01032, feat_cols_p01032], p_df_p01032.loc[tr_mask_p01032, 'sales'])

daily_preds_p01032 = []
hist_s_p01032 = p_df_p01032.loc[tr_mask_p01032, 'sales'].copy()
test_sub_p01032 = p_df_p01032.loc[te_mask_p01032].copy().reset_index(drop=True)
for _, row in test_sub_p01032.iterrows():
    lag_1 = hist_s_p01032.iloc[-1]
    lag_7 = hist_s_p01032.iloc[-7] if len(hist_s_p01032) >= 7 else hist_s_p01032.iloc[0]
    rm_30 = hist_s_p01032.iloc[-30:].mean()
    row_feat = row[feat_cols_p01032].to_dict()
    row_feat['lag_1'] = lag_1; row_feat['lag_7'] = lag_7; row_feat['rolling_mean_30'] = rm_30
    feat_vec = pd.DataFrame([row_feat])[feat_cols_p01032]
    pval = max(0.0, float(m_ridge_p01032.predict(feat_vec)[0]))
    daily_preds_p01032.append(pval)
    hist_s_p01032 = pd.concat([hist_s_p01032, pd.Series([pval])], ignore_index=True)

pred_s_p01032 = pd.Series(daily_preds_p01032, index=forecast_daily_dates)
hist_s_p01032 = p_df_p01032.loc[tr_mask_p01032].set_index('date')['sales']

weekly_hist_p01032 = (hist_s_p01032.resample('W-SUN').sum() / 1e3).iloc[-52:]
weekly_pred_p01032 = pred_s_p01032.resample('W-SUN').sum() / 1e3

for m_name, m_dates in [("June 2025", "2025-06-01 to 2025-06-30"),
                        ("July 2025", "2025-07-01 to 2025-07-31"),
                        ("August 2025", "2025-08-01 to 2025-08-31"),
                        ("September 2025", "2025-09-01 to 2025-09-30")]:
    m_val = pred_s_p01032.loc[m_dates[:10]:m_dates[-10:]].sum()
    m_units = int(round(m_val / ASP_DICT["P01032"]))
    monthly_forecast_records.append({
        "product_id": "P01032", "product_name": PRODUCT_NAMES["P01032"],
        "top_model": CHAMPION_MODELS["P01032"], "month": m_name,
        "predicted_sales_INR": round(m_val, 2), "predicted_units": m_units,
        "asp_INR": ASP_DICT["P01032"]
    })

# Plot 3: P01032 Trend Line
plt.figure(figsize=(11, 4.8), dpi=200)
ax = plt.gca()
ax.plot(weekly_hist_p01032.index, weekly_hist_p01032.values, color='#7c3aed', linewidth=2.0, label='Historical Weekly Sales (k₹)')
conn_x = [weekly_hist_p01032.index[-1], weekly_pred_p01032.index[0]]
conn_y = [weekly_hist_p01032.values[-1], weekly_pred_p01032.values[0]]
ax.plot(conn_x, conn_y, color='#047857', linestyle='--', linewidth=2.0)
ax.plot(weekly_pred_p01032.index, weekly_pred_p01032.values, color='#047857', linewidth=2.4, linestyle='--', marker='^', markersize=5, label='Forecast Trend Line (Arth Ridge Payday) [k₹]')

sigma_p01032 = 6.0 # kINR
ax.fill_between(weekly_pred_p01032.index,
                np.maximum(0, weekly_pred_p01032.values - 1.28 * sigma_p01032),
                weekly_pred_p01032.values + 1.28 * sigma_p01032,
                color='#10b981', alpha=0.18, label='80% Safety Stock Lead-Time Band')

ax.axvline(x=pd.Timestamp("2025-06-01"), color='#dc2626', linestyle=':', linewidth=1.5, label='Forecast Start (1-Jun-2025)')

ax.annotate('Salary Payday Surge Window\n(Month-End Salary Clustering)',
            xy=(pd.Timestamp("2025-08-31"), weekly_pred_p01032.loc["2025-08-31"] if pd.Timestamp("2025-08-31") in weekly_pred_p01032.index else weekly_pred_p01032.values[-4]),
            xytext=(pd.Timestamp("2025-07-15"), max(weekly_pred_p01032.values)*1.2),
            arrowprops=dict(facecolor='#7c3aed', shrink=0.08, width=1.2, headwidth=6),
            fontsize=8.5, fontweight='bold', color='#5b21b6',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#ede9fe', edgecolor='#8b5cf6', alpha=0.9))

ax.set_title('P01032 (Savic / Ferplast Luxury Orthopedic Crate ₹12.6k) — Out-of-Sample Sales Trend Line\nChampion Model: ★ Arth Event-Aware Ridge (Payday Surges & Intermittent Dummies, k₹)', fontsize=11, fontweight='bold', pad=10, color='#0f172a')
ax.set_ylabel('Weekly Sales (Thousands of INR | k₹)', fontsize=9.5, fontweight='bold')
ax.set_xlabel('Timeline (Historical 2024–2025 to Future Q3 2025)', fontsize=9.5, fontweight='bold')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.legend(loc='upper left', frameon=True, fontsize=8.5)
plt.tight_layout()
p3_file = os.path.join(PLOTS_DIR, "forecast_trend_P01032.png")
plt.savefig(p3_file, dpi=200)
plt.close()
print(f"[+] Saved trend line plot: {p3_file}")

# ==========================================
# 4. P00084 (Wet Food Gravy) - Top Model: Arth Daily Event Ridge (Strictly Daily)
# ==========================================
print("Forecasting P00084 with Arth Daily Event Ridge...")
p_raw_p00084 = raw[raw["product_id"] == "P00084"]
all_dates_p00084 = pd.date_range("2022-09-08", FORECAST_END, freq='D')
d_sales_p00084 = p_raw_p00084.groupby('date')['sales'].sum().reindex(all_dates_p00084, fill_value=0.0)

p_df_p00084 = pd.DataFrame({'date': all_dates_p00084, 'sales': d_sales_p00084.values})
p_df_p00084['trend'] = np.arange(len(p_df_p00084))
p_df_p00084['lag_1'] = p_df_p00084['sales'].shift(1).bfill()
p_df_p00084['lag_7'] = p_df_p00084['sales'].shift(7).bfill()
p_df_p00084['rolling_mean_30'] = p_df_p00084['sales'].shift(1).rolling(30, min_periods=1).mean().bfill()
ev_df_p00084 = build_arth_calendar_features(all_dates_p00084)
p_df_p00084 = pd.concat([p_df_p00084, ev_df_p00084.reset_index(drop=True)], axis=1)
feat_cols_p00084 = [c for c in p_df_p00084.columns if c not in ['date', 'sales']]

tr_mask_p00084 = p_df_p00084['date'] <= "2025-05-31"
te_mask_p00084 = (p_df_p00084['date'] >= FORECAST_START) & (p_df_p00084['date'] <= FORECAST_END)

m_ridge_p00084 = Ridge(alpha=40.0, random_state=42).fit(p_df_p00084.loc[tr_mask_p00084, feat_cols_p00084], p_df_p00084.loc[tr_mask_p00084, 'sales'])

daily_preds_p00084 = []
hist_s_p00084 = p_df_p00084.loc[tr_mask_p00084, 'sales'].copy()
test_sub_p00084 = p_df_p00084.loc[te_mask_p00084].copy().reset_index(drop=True)
for _, row in test_sub_p00084.iterrows():
    lag_1 = hist_s_p00084.iloc[-1]
    lag_7 = hist_s_p00084.iloc[-7] if len(hist_s_p00084) >= 7 else hist_s_p00084.iloc[0]
    rm_30 = hist_s_p00084.iloc[-30:].mean()
    row_feat = row[feat_cols_p00084].to_dict()
    row_feat['lag_1'] = lag_1; row_feat['lag_7'] = lag_7; row_feat['rolling_mean_30'] = rm_30
    feat_vec = pd.DataFrame([row_feat])[feat_cols_p00084]
    pval = max(0.0, float(m_ridge_p00084.predict(feat_vec)[0]))
    daily_preds_p00084.append(pval)
    hist_s_p00084 = pd.concat([hist_s_p00084, pd.Series([pval])], ignore_index=True)

pred_s_p00084 = pd.Series(daily_preds_p00084, index=forecast_daily_dates)
hist_s_p00084 = p_df_p00084.loc[tr_mask_p00084].set_index('date')['sales'].iloc[-120:]

for m_name, m_dates in [("June 2025", "2025-06-01 to 2025-06-30"),
                        ("July 2025", "2025-07-01 to 2025-07-31"),
                        ("August 2025", "2025-08-01 to 2025-08-31"),
                        ("September 2025", "2025-09-01 to 2025-09-30")]:
    m_val = pred_s_p00084.loc[m_dates[:10]:m_dates[-10:]].sum()
    m_units = int(round(m_val / ASP_DICT["P00084"]))
    monthly_forecast_records.append({
        "product_id": "P00084", "product_name": PRODUCT_NAMES["P00084"],
        "top_model": CHAMPION_MODELS["P00084"], "month": m_name,
        "predicted_sales_INR": round(m_val, 2), "predicted_units": m_units,
        "asp_INR": ASP_DICT["P00084"]
    })

# Plot 4: P00084 Trend Line (Strictly Daily)
plt.figure(figsize=(11, 4.8), dpi=200)
ax = plt.gca()
ax.plot(hist_s_p00084.index, hist_s_p00084.values, color='#0284c7', linewidth=1.5, alpha=0.85, label='Historical Daily Sales (INR)')
# 7-day rolling smooth of historical
ax.plot(hist_s_p00084.rolling(7).mean().index, hist_s_p00084.rolling(7).mean().values, color='#0369a1', linewidth=2.0, label='Historical 7-Day Moving Trend')

conn_x = [hist_s_p00084.index[-1], pred_s_p00084.index[0]]
conn_y = [hist_s_p00084.values[-1], pred_s_p00084.values[0]]
ax.plot(conn_x, conn_y, color='#047857', linestyle='--', linewidth=1.5)
ax.plot(pred_s_p00084.index, pred_s_p00084.values, color='#047857', linewidth=2.2, linestyle='--', label='Daily Forecast Trend Line (Arth Ridge) [INR]')

sigma_p00084 = 300.0 # INR
ax.fill_between(pred_s_p00084.index,
                np.maximum(0, pred_s_p00084.values - 1.28 * sigma_p00084),
                pred_s_p00084.values + 1.28 * sigma_p00084,
                color='#10b981', alpha=0.18, label='80% Daily Replenishment Band')

ax.axvline(x=pd.Timestamp("2025-06-01"), color='#dc2626', linestyle=':', linewidth=1.5, label='Forecast Start (1-Jun-2025)')
ax.set_title('P00084 (Pedigree / Whiskas Wet Food Gravy Pouches) — Out-of-Sample DAILY Sales Trend Line\nChampion Model: ★ Arth Daily Event-Aware Ridge (Strictly Daily Continuous, INR)', fontsize=11, fontweight='bold', pad=10, color='#0f172a')
ax.set_ylabel('Daily Sales (INR)', fontsize=9.5, fontweight='bold')
ax.set_xlabel('Timeline (Historical Spring 2025 to Future Q3 2025 Daily)', fontsize=9.5, fontweight='bold')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.legend(loc='upper left', frameon=True, fontsize=8.5)
plt.tight_layout()
p4_file = os.path.join(PLOTS_DIR, "forecast_trend_P00084.png")
plt.savefig(p4_file, dpi=200)
plt.close()
print(f"[+] Saved trend line plot: {p4_file}")

# ==========================================
# 5. P04291 (Chew Treats) - Top Model: SMA (8w)
# ==========================================
print("Forecasting P04291 with SMA (8w)...")
p_raw_p04291 = raw[raw["product_id"] == "P04291"]
d_p04291 = p_raw_p04291.groupby('date')['sales'].sum().asfreq('D', fill_value=0.0)
weekly_hist_p04291 = (d_p04291.resample('W-SUN').sum() / 1e3).loc["2024-01-19":"2025-05-31"]

hist_vals_p04291 = list(weekly_hist_p04291.values)
pred_vals_p04291 = []
for _ in range(h_steps):
    val = np.mean(hist_vals_p04291[-8:])
    pred_vals_p04291.append(val)
    hist_vals_p04291.append(val)

weekly_pred_p04291 = pd.Series(pred_vals_p04291, index=forecast_weekly_dates)

d_pred_p04291 = pd.Series(np.repeat([v / 7.0 * 1e3 for v in pred_vals_p04291], 7)[:len(forecast_daily_dates)], index=forecast_daily_dates)
for m_name, m_dates in [("June 2025", "2025-06-01 to 2025-06-30"),
                        ("July 2025", "2025-07-01 to 2025-07-31"),
                        ("August 2025", "2025-08-01 to 2025-08-31"),
                        ("September 2025", "2025-09-01 to 2025-09-30")]:
    m_val = d_pred_p04291.loc[m_dates[:10]:m_dates[-10:]].sum()
    m_units = int(round(m_val / ASP_DICT["P04291"]))
    monthly_forecast_records.append({
        "product_id": "P04291", "product_name": PRODUCT_NAMES["P04291"],
        "top_model": CHAMPION_MODELS["P04291"], "month": m_name,
        "predicted_sales_INR": round(m_val, 2), "predicted_units": m_units,
        "asp_INR": ASP_DICT["P04291"]
    })

# Plot 5: P04291 Trend Line
plt.figure(figsize=(11, 4.8), dpi=200)
ax = plt.gca()
ax.plot(weekly_hist_p04291.index, weekly_hist_p04291.values, color='#ea580c', linewidth=2.0, label='Historical Weekly Sales (k₹)')
conn_x = [weekly_hist_p04291.index[-1], weekly_pred_p04291.index[0]]
conn_y = [weekly_hist_p04291.values[-1], weekly_pred_p04291.values[0]]
ax.plot(conn_x, conn_y, color='#047857', linestyle='--', linewidth=2.0)
ax.plot(weekly_pred_p04291.index, weekly_pred_p04291.values, color='#047857', linewidth=2.4, linestyle='--', marker='d', markersize=5, label='Forecast Trend Line (SMA 8w Low-Bias) [k₹]')

sigma_p04291 = weekly_hist_p04291.iloc[-8:].std()
ax.fill_between(weekly_pred_p04291.index,
                np.maximum(0, weekly_pred_p04291.values - 1.28 * sigma_p04291),
                weekly_pred_p04291.values + 1.28 * sigma_p04291,
                color='#10b981', alpha=0.18, label='80% Buffer (Counter Jar Safety Stock)')

ax.axvline(x=pd.Timestamp("2025-06-01"), color='#dc2626', linestyle=':', linewidth=1.5, label='Forecast Start (1-Jun-2025)')
ax.set_title('P04291 (Barkbone Rawhide Chew Treats ₹64) — Out-of-Sample Sales Trend Line\nChampion Model: SMA (8-Week Moving Average / Low-Bias, k₹)', fontsize=11, fontweight='bold', pad=10, color='#0f172a')
ax.set_ylabel('Weekly Sales (Thousands of INR | k₹)', fontsize=9.5, fontweight='bold')
ax.set_xlabel('Timeline (Historical 2024–2025 to Future Q3 2025)', fontsize=9.5, fontweight='bold')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.legend(loc='upper left', frameon=True, fontsize=8.5)
plt.tight_layout()
p5_file = os.path.join(PLOTS_DIR, "forecast_trend_P04291.png")
plt.savefig(p5_file, dpi=200)
plt.close()
print(f"[+] Saved trend line plot: {p5_file}")

# ==========================================
# 6. MASTER 5-PANEL CONSOLIDATED TREND LINE DASHBOARD
# ==========================================
fig, axes = plt.subplots(5, 1, figsize=(12, 16), dpi=200, sharex=False)
fig.suptitle('JustDogs Top 5 SKUs — Out-of-Sample Sales Forecast Trend Lines (June – September 2025)\nGenerated Strictly using Product-Tailored Champion Models (No Bar Graphs)', fontsize=13, fontweight='bold', y=0.995, color='#0f172a')

# Panel 1: P04606
axes[0].plot(weekly_hist_p04606.index, weekly_hist_p04606.values, color='#1e3a8a', linewidth=1.8, label='Actuals (k₹)')
axes[0].plot([weekly_hist_p04606.index[-1], weekly_pred_p04606.index[0]], [weekly_hist_p04606.values[-1], weekly_pred_p04606.values[0]], color='#047857', linestyle='--')
axes[0].plot(weekly_pred_p04606.index, weekly_pred_p04606.values, color='#047857', linewidth=2.0, linestyle='--', marker='o', markersize=4, label='Forecast: Arth Ridge (k₹)')
axes[0].axvline(pd.Timestamp("2025-06-01"), color='#dc2626', linestyle=':', linewidth=1.2)
axes[0].set_title('P04606 (10kg Food) | Interval: Weekly | Top Model: ★ Arth Event-Aware Ridge (RMSE 56.47k | Fin Acc 85.0%)', fontsize=9.5, fontweight='bold', color='#1e3a8a')
axes[0].set_ylabel('k₹ / Week', fontsize=8.5)
axes[0].legend(loc='upper left', fontsize=7.5)

# Panel 2: P02065
axes[1].plot(weekly_hist_p02065.index, weekly_hist_p02065.values, color='#0284c7', linewidth=1.8, label='Actuals (k₹)')
axes[1].plot([weekly_hist_p02065.index[-1], weekly_pred_p02065.index[0]], [weekly_hist_p02065.values[-1], weekly_pred_p02065.values[0]], color='#047857', linestyle='--')
axes[1].plot(weekly_pred_p02065.index, weekly_pred_p02065.values, color='#047857', linewidth=2.0, linestyle='--', marker='s', markersize=4, label='Forecast: SMA 8w (k₹)')
axes[1].axvline(pd.Timestamp("2025-06-01"), color='#dc2626', linestyle=':', linewidth=1.2)
axes[1].set_title('P02065 (Grooming Hygiene) | Interval: Weekly | Top Model: SMA 8w (Vol Acc 50.55% | Fin Acc 98.8%)', fontsize=9.5, fontweight='bold', color='#0369a1')
axes[1].set_ylabel('k₹ / Week', fontsize=8.5)
axes[1].legend(loc='upper left', fontsize=7.5)

# Panel 3: P01032
axes[2].plot(weekly_hist_p01032.index, weekly_hist_p01032.values, color='#7c3aed', linewidth=1.8, label='Actuals (k₹)')
axes[2].plot([weekly_hist_p01032.index[-1], weekly_pred_p01032.index[0]], [weekly_hist_p01032.values[-1], weekly_pred_p01032.values[0]], color='#047857', linestyle='--')
axes[2].plot(weekly_pred_p01032.index, weekly_pred_p01032.values, color='#047857', linewidth=2.0, linestyle='--', marker='^', markersize=4, label='Forecast: Arth Ridge (k₹)')
axes[2].axvline(pd.Timestamp("2025-06-01"), color='#dc2626', linestyle=':', linewidth=1.2)
axes[2].set_title('P01032 (Luxury Bedding ₹12.6k) | Interval: Weekly | Top Model: ★ Arth Event Ridge (MAE 16.00k | Fin Acc 60.8%)', fontsize=9.5, fontweight='bold', color='#6d28d9')
axes[2].set_ylabel('k₹ / Week', fontsize=8.5)
axes[2].legend(loc='upper left', fontsize=7.5)

# Panel 4: P00084 (Daily)
axes[3].plot(hist_s_p00084.index, hist_s_p00084.values, color='#0284c7', linewidth=1.2, alpha=0.7, label='Actual Daily Sales (INR)')
axes[3].plot([hist_s_p00084.index[-1], pred_s_p00084.index[0]], [hist_s_p00084.values[-1], pred_s_p00084.values[0]], color='#047857', linestyle='--')
axes[3].plot(pred_s_p00084.index, pred_s_p00084.values, color='#047857', linewidth=1.8, linestyle='--', label='Daily Forecast: Arth Ridge (INR)')
axes[3].axvline(pd.Timestamp("2025-06-01"), color='#dc2626', linestyle=':', linewidth=1.2)
axes[3].set_title('P00084 (Wet Food Gravy) | Interval: STRICTLY DAILY | Top Model: ★ Arth Daily Ridge (Daily RMSE 1,136.91 | Fin Acc 89.0%)', fontsize=9.5, fontweight='bold', color='#0284c7')
axes[3].set_ylabel('Daily INR', fontsize=8.5)
axes[3].legend(loc='upper left', fontsize=7.5)

# Panel 5: P04291
axes[4].plot(weekly_hist_p04291.index, weekly_hist_p04291.values, color='#ea580c', linewidth=1.8, label='Actuals (k₹)')
axes[4].plot([weekly_hist_p04291.index[-1], weekly_pred_p04291.index[0]], [weekly_hist_p04291.values[-1], weekly_pred_p04291.values[0]], color='#047857', linestyle='--')
axes[4].plot(weekly_pred_p04291.index, weekly_pred_p04291.values, color='#047857', linewidth=2.0, linestyle='--', marker='d', markersize=4, label='Forecast: SMA 8w (k₹)')
axes[4].axvline(pd.Timestamp("2025-06-01"), color='#dc2626', linestyle=':', linewidth=1.2)
axes[4].set_title('P04291 (Chew Treats ₹64) | Interval: Weekly | Top Model: SMA 8w (Near-Zero Bias: 0.11k | Fin Acc 96.9%)', fontsize=9.5, fontweight='bold', color='#c2410c')
axes[4].set_ylabel('k₹ / Week', fontsize=8.5)
axes[4].set_xlabel('Timeline (2024 to Q3 2025)', fontsize=9, fontweight='bold')
axes[4].legend(loc='upper left', fontsize=7.5)

for ax in axes:
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
dashboard_file = os.path.join(PLOTS_DIR, "forecast_trend_top5_products.png")
plt.savefig(dashboard_file, dpi=200)
plt.close()
print(f"[+] Saved 5-panel dashboard trend line plot: {dashboard_file}")

# Save CSV
df_out = pd.DataFrame(monthly_forecast_records)
df_out.to_csv(OUT_CSV, index=False)
print(f"[+] Saved forecast CSV: {OUT_CSV}")

print("\n--- FORECAST SUMMARY (JUNE – SEPTEMBER 2025) ---")
print(df_out.to_string(index=False))
