"""
generate_synthetic_data.py
==========================
Generates realistic synthetic climate data for 2021–2025 and
saves three extended CSV files into the Dataset/ folder.

Scientific basis:
  • Temperature  : ~0.020°C/yr warming trend (IPCC AR6 aligned), Gaussian noise σ=0.12
  • CO₂ Emissions: ~1.8% annual growth post-2020 (post-COVID rebound), plateauing 2024-25
  • Sea Level    : ~4.0 mm/yr rise (accelerating from 3.7 mm/yr in 2010s)
  • Monthly temps: seasonal sine-wave fitted from 1980-2015 observations

Synthetic rows are tagged  source = 'synthetic'  in each file.
The original files are NEVER modified.

Run:  python generate_synthetic_data.py
"""

import os
import numpy as np
import pandas as pd

np.random.seed(42)   # reproducible

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "Dataset")

def dp(f):
    return os.path.join(DATASET_DIR, f)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Extend avg_dataset.csv  →  avg_dataset_extended.csv
#    Columns: Year, Avg Land Temp, Avg LandOcean Temp, Avg Emissions, Avg Sea Level
# ─────────────────────────────────────────────────────────────────────────────
def extend_avg_dataset():
    df = pd.read_csv(dp("avg_dataset.csv"))
    df.columns = [c.strip() for c in df.columns]

    # Normalise column names to simple tokens
    col_land  = [c for c in df.columns if "Land_Temperature" in c and "Ocean" not in c][0]
    col_ocean = [c for c in df.columns if "Ocean" in c or ("Land" in c and "Ocean" in c)][0]
    col_emit  = [c for c in df.columns if "Emission" in c][0]
    col_sea   = [c for c in df.columns if "Sea" in c or "sea" in c][0]

    df["source"] = "historical"

    # --- fit trends from last 10 years of real data ---
    hist = df[df["Year"] >= 2010].copy()

    # Land temperature trend: linear fit
    land_fit   = np.polyfit(hist["Year"], hist[col_land].ffill(), 1)
    # LandOcean temperature: use last available + trend
    ocean_last = df[col_ocean].dropna().iloc[-1]
    ocean_year_last = df.dropna(subset=[col_ocean])["Year"].iloc[-1]
    ocean_trend = 0.021   # °C/yr

    # Emissions trend from last 5 real years
    emit_hist  = hist[hist[col_emit].notna()]
    emit_fit   = np.polyfit(emit_hist["Year"].tail(5), emit_hist[col_emit].tail(5), 1)

    # Sea level: last value + ~4.0 mm/yr
    sea_last   = df[col_sea].iloc[-1]
    sea_trend  = 4.2     # mm/yr

    synth_rows = []
    for i, yr in enumerate(range(2021, 2026)):
        # Land temp
        land_base  = np.polyval(land_fit, yr)
        land_temp  = land_base + np.random.normal(0, 0.10)
        # Slight additional jump for 2023 (record year matching real observations)
        if yr == 2023:
            land_temp += 0.18
        if yr == 2024:
            land_temp += 0.22

        # LandOcean temp
        ocean_temp = ocean_last + ocean_trend * (yr - ocean_year_last) + np.random.normal(0, 0.08)
        if yr == 2023:
            ocean_temp += 0.25   # 2023 was record-breaking globally
        if yr == 2024:
            ocean_temp += 0.30

        # CO₂ Emissions (MtCO₂e) — growth slowing after 2023 due to renewables
        growth = 0.018 if yr <= 2022 else 0.010
        emit_base = np.polyval(emit_fit, yr)
        emissions = max(emit_base, 37000) * (1 + growth * i) + np.random.normal(0, 200)

        # Sea Level
        sea_level = sea_last + sea_trend * (yr - 2020) + np.random.normal(0, 1.5)

        synth_rows.append({
            "Year":          yr,
            col_land:        round(land_temp,  4),
            col_ocean:       round(ocean_temp, 4),
            col_emit:        round(emissions,  2),
            col_sea:         round(sea_level,  5),
            "source":        "synthetic",
        })

    synth_df = pd.DataFrame(synth_rows)
    extended = pd.concat([df, synth_df], ignore_index=True)
    extended = extended.sort_values("Year").reset_index(drop=True)

    out_path = dp("avg_dataset_extended.csv")
    extended.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[1] avg_dataset_extended.csv  →  {len(extended)} rows  ({extended['Year'].min()}–{extended['Year'].max()})")
    return extended


# ─────────────────────────────────────────────────────────────────────────────
# 2. Extend Global_sea_level_rise.csv  →  Global_sea_level_rise_extended.csv
# ─────────────────────────────────────────────────────────────────────────────
def extend_sea_level():
    df = pd.read_csv(dp("Global_sea_level_rise.csv"))
    df.columns = [c.strip() for c in df.columns]
    df["Sea Level"] = pd.to_numeric(df["Sea Level"].astype(str).str.strip(), errors="coerce")
    df["source"] = "historical"

    last_year  = int(df["Year"].max())
    last_level = df[df["Year"] == last_year]["Sea Level"].values[0]

    # Fit linear rise from 2010 onwards
    recent = df[df["Year"] >= 2010].dropna(subset=["Sea Level"])
    slope, intercept = np.polyfit(recent["Year"], recent["Sea Level"], 1)
    # Average recent slope should be ~3.7 mm/yr; extend with slight acceleration
    rise_per_year = max(slope, 3.7)

    synth_rows = []
    for i, yr in enumerate(range(last_year + 1, 2026)):
        level = last_level + rise_per_year * (i + 1) + (i * 0.08) + np.random.normal(0, 1.2)
        synth_rows.append({
            "Year":      yr,
            "date":      f"7/15/{yr}",
            "Sea Level": round(level, 5),
            "source":    "synthetic",
        })

    synth_df = pd.DataFrame(synth_rows)
    extended = pd.concat([df, synth_df], ignore_index=True)
    extended = extended.sort_values("Year").reset_index(drop=True)

    out_path = dp("Global_sea_level_rise_extended.csv")
    extended.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[2] Global_sea_level_rise_extended.csv  →  {len(extended)} rows  ({extended['Year'].min()}–{extended['Year'].max()})")
    return extended


# ─────────────────────────────────────────────────────────────────────────────
# 3. Extend GlobalTemperatures.csv  →  GlobalTemperatures_extended.csv
#    Monthly data: Jan 2016 → Dec 2025
# ─────────────────────────────────────────────────────────────────────────────
def extend_global_temperatures():
    df = pd.read_csv(dp("GlobalTemperatures.csv"))
    df.columns = [c.strip() for c in df.columns]
    df["dt"] = pd.to_datetime(df["dt"])
    df["source"] = "historical"

    # Fit seasonal profile from 1980–2015
    train = df[(df["dt"].dt.year >= 1980) & (df["dt"].dt.year <= 2015)].copy()
    train["month"] = train["dt"].dt.month
    monthly_profile = train.groupby("month")["LandAverageTemperature"].mean()   # seasonal baseline

    # Overall warming trend from yearly means
    train_yearly = (
        train.dropna(subset=["LandAverageTemperature"])
        .groupby(train["dt"].dt.year)["LandAverageTemperature"]
        .mean()
    )
    trend_fit = np.polyfit(train_yearly.index, train_yearly.values, 1)   # linear trend
    # Slope is ~0.008°C/month-year → per year

    last_dt    = df["dt"].max()
    last_year  = last_dt.year
    last_month = last_dt.month

    # Baseline temperature at last known point
    base_temp = train_yearly.iloc[-1]

    synth_rows = []
    months_added = 0
    for yr in range(last_year, 2026):
        start_month = last_month + 1 if yr == last_year else 1
        for mo in range(start_month, 13):
            months_added += 1
            years_elapsed = months_added / 12.0

            # Seasonal component (deviation from mean)
            seasonal = monthly_profile[mo] - monthly_profile.mean()

            # Long-term warming trend
            trend_increment = 0.020 * years_elapsed   # 0.020°C/yr

            # Bonus warming for 2023–2024 (El Niño / record years)
            bonus = 0.0
            if yr == 2023 and mo >= 6:
                bonus = 0.20
            elif yr == 2024:
                bonus = 0.28
            elif yr == 2025:
                bonus = 0.18

            land_temp = base_temp + trend_increment + seasonal + bonus + np.random.normal(0, 0.12)

            # LandOcean is systematically warmer by ~6°C
            ocean_temp = land_temp + 6.0 + np.random.normal(0, 0.06)

            synth_rows.append({
                "dt":                             f"{yr}-{mo:02d}-01",
                "LandAverageTemperature":         round(land_temp, 4),
                "LandAverageTemperatureUncertainty": round(np.random.uniform(0.05, 0.15), 3),
                "LandAndOceanAverageTemperature": round(ocean_temp, 4),
                "LandAndOceanAverageTemperatureUncertainty": round(np.random.uniform(0.03, 0.10), 3),
                "source": "synthetic",
            })

    synth_df = pd.DataFrame(synth_rows)
    # Keep only matching columns
    keep_cols = [c for c in df.columns if c != "source"] + ["source"]
    # Fill missing synth cols with NaN
    for col in keep_cols:
        if col not in synth_df.columns:
            synth_df[col] = np.nan

    extended = pd.concat([df[keep_cols], synth_df[keep_cols]], ignore_index=True)
    extended["dt"] = pd.to_datetime(extended["dt"], errors="coerce")
    extended = extended.sort_values("dt").reset_index(drop=True)
    extended["dt"] = extended["dt"].dt.strftime("%Y-%m-%d")

    out_path = dp("GlobalTemperatures_extended.csv")
    extended.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[3] GlobalTemperatures_extended.csv  →  {len(extended)} rows  ({extended['dt'].iloc[0]} to {extended['dt'].iloc[-1]})")
    return extended


# ─────────────────────────────────────────────────────────────────────────────
# 4. Extend UpdatedMajorCity_temperatures.csv  (ends 2013)  →  _extended.csv
#    Keeps same schema; generates one row per existing city × month × year 2014-2025
# ─────────────────────────────────────────────────────────────────────────────
def extend_city_temperatures():
    df = pd.read_csv(dp("UpdatedMajorCity_temperatures.csv"))
    df.columns = [c.strip() for c in df.columns]
    df["dt_parsed"] = pd.to_datetime(df["dt"], errors="coerce")
    df["Year"] = df["dt_parsed"].dt.year
    df["Month"] = df["dt_parsed"].dt.month

    # Identify last real year in data
    last_year = int(df["Year"].max())   # 2013

    # Build seasonal profile per City from last 10 real years
    recent = df[df["Year"] >= last_year - 10].dropna(subset=["AverageTemperature"])
    city_month_mean = (
        recent.groupby(["City", "Month"])["AverageTemperature"].mean().reset_index()
    )
    # Also get one row per city to copy fixed attributes (Country, Lat, Lon, etc.)
    city_meta = df.sort_values("dt_parsed").groupby("City").last().reset_index()
    # Identify cols for lat, lon
    lat_col = next((c for c in df.columns if "lat" in c.lower() and "float" in c.lower()), None) or \
              next((c for c in df.columns if "lat" in c.lower()), None)
    lon_col = next((c for c in df.columns if "lon" in c.lower() and "float" in c.lower()), None) or \
              next((c for c in df.columns if "lon" in c.lower()), None)
    country_col = "Country" if "Country" in df.columns else None

    # Warming trend: global baseline +0.020°C/yr after 2013
    WARMING = 0.020

    synth_rows = []
    for _, meta_row in city_meta.iterrows():
        city = meta_row["City"]
        country = meta_row.get(country_col, "") if country_col else ""
        lat = meta_row.get(lat_col, None) if lat_col else None
        lon = meta_row.get(lon_col, None) if lon_col else None

        for yr in range(last_year + 1, 2026):
            yrs_past = yr - last_year
            for mo in range(1, 13):
                # Get seasonal baseline for this city+month
                match = city_month_mean[
                    (city_month_mean["City"] == city) &
                    (city_month_mean["Month"] == mo)
                ]
                if match.empty:
                    continue
                base_temp = match["AverageTemperature"].values[0]

                # Apply warming trend + small random noise
                bonus = 0.0
                if yr == 2023 and mo >= 6: bonus = 0.20
                elif yr == 2024: bonus = 0.28
                elif yr == 2025: bonus = 0.18

                synth_temp = base_temp + WARMING * yrs_past + bonus + np.random.normal(0, 0.15)
                synth_uncertainty = round(np.random.uniform(0.10, 0.40), 3)

                row = {
                    "dt":                               f"{yr}-{mo:02d}-01",
                    "AverageTemperature":               round(synth_temp, 4),
                    "AverageTemperatureUncertainty":    synth_uncertainty,
                    "City":                             city,
                    "source":                           "synthetic",
                }
                if country_col:
                    row[country_col] = country
                if lat_col:
                    row[lat_col] = lat
                if lon_col:
                    row[lon_col] = lon
                synth_rows.append(row)

    synth_df = pd.DataFrame(synth_rows)
    # Align columns
    for col in df.columns:
        if col not in synth_df.columns:
            synth_df[col] = np.nan
    df["source"] = "historical"
    extended = pd.concat([df[list(df.columns)], synth_df[list(df.columns)]], ignore_index=True)
    extended["dt_parsed"] = pd.to_datetime(extended["dt"], errors="coerce")
    extended = extended.sort_values(["dt_parsed","City"]).reset_index(drop=True)
    extended = extended.drop(columns=["dt_parsed","Year","Month"], errors="ignore")

    out_path = dp("UpdatedMajorCity_temperatures_extended.csv")
    extended.to_csv(out_path, index=False, encoding="utf-8")
    max_yr = pd.to_datetime(extended["dt"], errors="coerce").dt.year.max()
    print(f"[4] UpdatedMajorCity_temperatures_extended.csv  →  {len(extended)} rows  (max year={max_yr})")
    return extended


# ─────────────────────────────────────────────────────────────────────────────
# 5. Extend GlobalLandTemperaturesByCountry.csv  (ends ~2013)  →  _extended.csv
# ─────────────────────────────────────────────────────────────────────────────
def extend_land_by_country():
    df = pd.read_csv(dp("GlobalLandTemperaturesByCountry.csv"))
    df.columns = [c.strip() for c in df.columns]
    date_col = [c for c in df.columns if c.lower() in ("dt", "date")][0]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df["Year"] = df[date_col].dt.year
    df["Month"] = df[date_col].dt.month
    last_year = int(df["Year"].max())

    temp_col = [c for c in df.columns if "AverageTemperature" in c and "Uncertainty" not in c][0]
    country_col = [c for c in df.columns if c.lower() == "country"][0]

    # Seasonal mean per country × month
    recent = df[df["Year"] >= last_year - 10].dropna(subset=[temp_col])
    profile = recent.groupby([country_col, "Month"])[temp_col].mean().reset_index()

    WARMING = 0.020
    synth_rows = []
    for country in df[country_col].unique():
        for yr in range(last_year + 1, 2026):
            yrs_past = yr - last_year
            for mo in range(1, 13):
                match = profile[(profile[country_col] == country) & (profile["Month"] == mo)]
                if match.empty:
                    continue
                base = match[temp_col].values[0]
                bonus = 0.18 if yr == 2023 else (0.26 if yr == 2024 else 0.15 if yr == 2025 else 0.0)
                synth_temp = base + WARMING * yrs_past + bonus + np.random.normal(0, 0.18)
                synth_rows.append({
                    date_col: f"{yr}-{mo:02d}-01",
                    temp_col: round(synth_temp, 4),
                    "AverageTemperatureUncertainty": round(np.random.uniform(0.05, 0.30), 3),
                    country_col: country,
                    "source": "synthetic",
                })

    synth_df = pd.DataFrame(synth_rows)
    df["source"] = "historical"
    keep = [c for c in df.columns] + ["source"] if "source" not in df.columns else list(df.columns)
    for col in keep:
        if col not in synth_df.columns:
            synth_df[col] = np.nan
    extended = pd.concat([df[keep], synth_df[keep]], ignore_index=True)
    extended[date_col] = pd.to_datetime(extended[date_col], errors="coerce")
    extended = extended.sort_values([date_col, country_col]).reset_index(drop=True)
    extended[date_col] = extended[date_col].dt.strftime("%Y-%m-%d")
    extended = extended.drop(columns=["Year", "Month"], errors="ignore")

    out_path = dp("GlobalLandTemperaturesByCountry_extended.csv")
    extended.to_csv(out_path, index=False, encoding="utf-8")
    max_yr = pd.to_datetime(extended[date_col], errors="coerce").dt.year.max()
    print(f"[5] GlobalLandTemperaturesByCountry_extended.csv  →  {len(extended)} rows  (max year={max_yr})")
    return extended


# ─────────────────────────────────────────────────────────────────────────────
# 6. Extend GlobalLandTemperaturesByMajorCity.csv  (ends ~2013)  →  _extended.csv
# ─────────────────────────────────────────────────────────────────────────────
def extend_land_by_major_city():
    df = pd.read_csv(dp("GlobalLandTemperaturesByMajorCity.csv"))
    df.columns = [c.strip() for c in df.columns]
    date_col = [c for c in df.columns if c.lower() in ("dt", "date")][0]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df["Year"] = df[date_col].dt.year
    df["Month"] = df[date_col].dt.month
    last_year = int(df["Year"].max())

    temp_col = [c for c in df.columns if "AverageTemperature" in c and "Uncertainty" not in c][0]
    city_col = [c for c in df.columns if c.lower() == "city"][0]
    country_col = [c for c in df.columns if c.lower() == "country"][0]
    # Get lat/lon columns
    lat_col = next((c for c in df.columns if "lat" in c.lower()), None)
    lon_col = next((c for c in df.columns if "lon" in c.lower()), None)

    recent = df[df["Year"] >= last_year - 10].dropna(subset=[temp_col])
    profile = recent.groupby([city_col, "Month"])[temp_col].mean().reset_index()
    city_meta = df.sort_values(date_col).groupby(city_col).last().reset_index()

    WARMING = 0.020
    synth_rows = []
    for _, meta in city_meta.iterrows():
        city = meta[city_col]
        country = meta.get(country_col, "")
        lat = meta.get(lat_col, None) if lat_col else None
        lon = meta.get(lon_col, None) if lon_col else None
        for yr in range(last_year + 1, 2026):
            yrs_past = yr - last_year
            for mo in range(1, 13):
                match = profile[(profile[city_col] == city) & (profile["Month"] == mo)]
                if match.empty:
                    continue
                base = match[temp_col].values[0]
                bonus = 0.18 if yr == 2023 else (0.26 if yr == 2024 else 0.15 if yr == 2025 else 0.0)
                synth_temp = base + WARMING * yrs_past + bonus + np.random.normal(0, 0.15)
                row = {
                    date_col: f"{yr}-{mo:02d}-01",
                    temp_col: round(synth_temp, 4),
                    "AverageTemperatureUncertainty": round(np.random.uniform(0.05, 0.35), 3),
                    city_col: city,
                    country_col: country,
                    "source": "synthetic",
                }
                if lat_col: row[lat_col] = lat
                if lon_col: row[lon_col] = lon
                synth_rows.append(row)

    synth_df = pd.DataFrame(synth_rows)
    df["source"] = "historical"
    keep = [c for c in df.columns] + (["source"] if "source" not in df.columns else [])
    for col in keep:
        if col not in synth_df.columns:
            synth_df[col] = np.nan
    extended = pd.concat([df[keep], synth_df[keep]], ignore_index=True)
    extended[date_col] = pd.to_datetime(extended[date_col], errors="coerce")
    extended = extended.sort_values([date_col, city_col]).reset_index(drop=True)
    extended[date_col] = extended[date_col].dt.strftime("%Y-%m-%d")
    extended = extended.drop(columns=["Year", "Month"], errors="ignore")

    out_path = dp("GlobalLandTemperaturesByMajorCity_extended.csv")
    extended.to_csv(out_path, index=False, encoding="utf-8")
    max_yr = pd.to_datetime(extended[date_col], errors="coerce").dt.year.max()
    print(f"[6] GlobalLandTemperaturesByMajorCity_extended.csv  →  {len(extended)} rows  (max year={max_yr})")
    return extended


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating/updating all synthetic climate datasets …\n")
    extend_avg_dataset()
    extend_sea_level()
    extend_global_temperatures()
    print("\nExtending 2013-limited datasets …")
    extend_city_temperatures()
    extend_land_by_country()
    extend_land_by_major_city()
    print("\nDone. Six extended CSV files saved to Dataset/")
    print("Original files are unchanged.")

