"""
tableau_export.py  –  Tableau Data Export Pipeline
====================================================
Reads all project datasets and exports clean, enriched, Tableau-ready CSVs
into the 'tableau_data/' folder.

Outputs:
  1. tableau_global_temperatures.csv   – Yearly global temps with moving avg & warning flags
  2. tableau_carbon_emissions.csv      – Country-level CO₂ emissions with region mapping
  3. tableau_sea_level.csv             – Sea level rise time series with trend
  4. tableau_correlation_matrix.csv    – Combined dataset (temp + CO₂ + sea level)
  5. tableau_country_temperatures.csv  – Country-level yearly avg temperatures
  6. tableau_summary.csv               – Metadata about each exported dataset

Run:
  python tableau_export.py
"""

import os
import warnings
import numpy as np
import pandas as pd
import sys

# Ensure stdout can handle utf-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

warnings.filterwarnings("ignore")

# ── Path Helpers ──────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "Dataset")
OUTPUT_DIR  = os.path.join(BASE_DIR, "tableau_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def dp(f):
    """Return absolute path for a Dataset file."""
    return os.path.join(DATASET_DIR, f)


def prefer_extended(base_name):
    """Return filename with '_extended' suffix if it exists, else base."""
    name, ext = os.path.splitext(base_name)
    extended = f"{name}_extended{ext}"
    if os.path.exists(dp(extended)):
        return extended
    return base_name


def save(df, filename, description):
    """Save DataFrame to tableau_data/ and return summary row."""
    path = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    rows, cols = df.shape
    size_kb = os.path.getsize(path) / 1024
    print(f"  ✅ {filename:45s}  {rows:>7,} rows × {cols:>3} cols  ({size_kb:>8.1f} KB)")
    return {
        "Dataset": filename,
        "Description": description,
        "Rows": rows,
        "Columns": cols,
        "Size_KB": round(size_kb, 1),
        "Column_Names": ", ".join(df.columns.tolist()),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 1. GLOBAL TEMPERATURES
# ═══════════════════════════════════════════════════════════════════════════════
def export_global_temperatures():
    """
    Export yearly global temperature stats with moving averages,
    first/second differences, and early warning flags.
    """
    fname = prefer_extended("GlobalTemperatures.csv")
    df = pd.read_csv(dp(fname))
    df["dt"] = pd.to_datetime(df["dt"], errors="coerce")
    df = df.dropna(subset=["dt"])
    df["Year"] = df["dt"].dt.year
    df["Month"] = df["dt"].dt.month

    # Source tag
    if "source" not in df.columns:
        df["source"] = "historical"

    # Yearly aggregation
    agg_cols = {
        "LandAverageTemperature": "mean",
        "LandAverageTemperatureUncertainty": "mean",
    }
    # Include optional columns if present
    for col in ["LandMaxTemperature", "LandMinTemperature",
                "LandAndOceanAverageTemperature"]:
        if col in df.columns:
            agg_cols[col] = "mean"

    yearly = df.groupby("Year").agg(agg_cols).reset_index()

    # Add source tag (last entry per year)
    source_yearly = df.groupby("Year")["source"].last().reset_index()
    yearly = yearly.merge(source_yearly, on="Year", how="left")

    # ── Early Warning Features ────────────────────────────────────────────
    yearly = yearly.sort_values("Year").reset_index(drop=True)
    yearly["Moving_Avg_5yr"] = yearly["LandAverageTemperature"].rolling(
        window=5, center=True).mean()
    yearly["First_Diff_DeltaT"] = yearly["Moving_Avg_5yr"].diff()
    yearly["Second_Diff_Accel"] = yearly["First_Diff_DeltaT"].diff()
    yearly["Rolling_Variance_10yr"] = yearly["LandAverageTemperature"].rolling(
        window=10, center=False).var()

    # Warning flags
    mu = yearly["Second_Diff_Accel"].mean()
    sigma = yearly["Second_Diff_Accel"].std()
    threshold = mu + 1.5 * sigma
    yearly["Accel_Warning"] = yearly["Second_Diff_Accel"] > threshold
    yearly["Accel_Warning_Threshold"] = threshold

    var_med = yearly["Rolling_Variance_10yr"].median()
    var_std = yearly["Rolling_Variance_10yr"].std()
    yearly["High_Variance_Flag"] = yearly["Rolling_Variance_10yr"] > (var_med + var_std)

    # Decade column for Tableau grouping
    yearly["Decade"] = (yearly["Year"] // 10) * 10
    yearly["Decade_Label"] = yearly["Decade"].astype(str) + "s"

    # Temperature anomaly (relative to 1951-1980 baseline)
    baseline = yearly[(yearly["Year"] >= 1951) & (yearly["Year"] <= 1980)]["LandAverageTemperature"].mean()
    yearly["Temp_Anomaly"] = yearly["LandAverageTemperature"] - baseline

    # Round floats for cleaner Tableau display
    float_cols = yearly.select_dtypes(include=[np.floating]).columns
    yearly[float_cols] = yearly[float_cols].round(4)

    return save(yearly, "tableau_global_temperatures.csv",
                "Yearly global land temperature with moving averages, "
                "early warning flags, and anomalies (1750–2025)")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CARBON EMISSIONS
# ═══════════════════════════════════════════════════════════════════════════════
def export_carbon_emissions():
    """
    Export country-level CO₂ emissions enriched with regions,
    cumulative totals, and ranking.
    """
    df = pd.read_csv(dp("historical_emissions.csv"))
    df.columns = [c.strip() for c in df.columns]

    # Standardize column name
    co2_col = [c for c in df.columns if "CO2" in c or "Emission" in c][0]
    df = df.rename(columns={co2_col: "CO2_Emissions_MtCO2e"})

    # Add region mapping
    region_map = {
        "United States": "North America", "Canada": "North America",
        "Mexico": "North America",
        "China": "Asia", "India": "Asia", "Japan": "Asia",
        "South Korea": "Asia", "Indonesia": "Asia", "Iran": "Middle East",
        "Saudi Arabia": "Middle East",
        "Russia": "Europe", "Germany": "Europe",
        "United Kingdom": "Europe", "France": "Europe",
        "Italy": "Europe", "Spain": "Europe", "Poland": "Europe",
        "Turkey": "Europe", "Ukraine": "Europe",
        "Brazil": "South America", "Argentina": "South America",
        "Colombia": "South America",
        "South Africa": "Africa", "Nigeria": "Africa", "Egypt": "Africa",
        "Australia": "Oceania", "New Zealand": "Oceania",
    }
    # Also map EU entries
    for key in list(df["Country"].unique()):
        if "European Union" in key:
            region_map[key] = "Europe"

    df["Region"] = df["Country"].map(region_map).fillna("Other")

    # Cumulative emissions per country
    df = df.sort_values(["Country", "Year"])
    df["Cumulative_CO2"] = df.groupby("Country")["CO2_Emissions_MtCO2e"].cumsum()

    # Yearly global rank (1 = highest emitter)
    df["Yearly_Rank"] = df.groupby("Year")["CO2_Emissions_MtCO2e"].rank(
        ascending=False, method="min").fillna(-1).astype(int)

    # Year-over-year change
    df["YoY_Change"] = df.groupby("Country")["CO2_Emissions_MtCO2e"].diff()
    df["YoY_Change_Pct"] = df.groupby("Country")["CO2_Emissions_MtCO2e"].pct_change() * 100

    # Global share
    yearly_total = df.groupby("Year")["CO2_Emissions_MtCO2e"].transform("sum")
    df["Global_Share_Pct"] = (df["CO2_Emissions_MtCO2e"] / yearly_total * 100).round(2)

    # Decade
    df["Decade"] = (df["Year"] // 10) * 10

    float_cols = df.select_dtypes(include=[np.floating]).columns
    df[float_cols] = df[float_cols].round(4)

    return save(df, "tableau_carbon_emissions.csv",
                "Country-level CO₂ emissions with regions, ranks, "
                "cumulative totals, and global share (1990–2018)")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SEA LEVEL RISE
# ═══════════════════════════════════════════════════════════════════════════════
def export_sea_level():
    """
    Export sea level rise data with trend lines and rate of change.
    """
    fname = prefer_extended("Global_sea_level_rise.csv")
    df = pd.read_csv(dp(fname))
    df.columns = [c.strip() for c in df.columns]

    if "source" not in df.columns:
        df["source"] = "historical"

    df = df.sort_values("Year").reset_index(drop=True)

    # Trend line (linear regression)
    valid = df.dropna(subset=["Sea Level"])
    if len(valid) > 2:
        coeffs = np.polyfit(valid["Year"], valid["Sea Level"], 1)
        df["Linear_Trend"] = np.polyval(coeffs, df["Year"])
        df["Trend_Rate_mm_per_yr"] = coeffs[0]
    else:
        df["Linear_Trend"] = np.nan
        df["Trend_Rate_mm_per_yr"] = np.nan

    # Rate of change
    df["YoY_Change_mm"] = df["Sea Level"].diff()
    df["Moving_Avg_10yr"] = df["Sea Level"].rolling(window=10, center=True).mean()

    # Decade
    df["Decade"] = (df["Year"] // 10) * 10

    # Normalize to 1880 baseline
    baseline_val = df.loc[df["Year"] == df["Year"].min(), "Sea Level"].values
    if len(baseline_val) > 0:
        df["Sea_Level_Relative"] = df["Sea Level"] - baseline_val[0]

    float_cols = df.select_dtypes(include=[np.floating]).columns
    df[float_cols] = df[float_cols].round(4)

    return save(df, "tableau_sea_level.csv",
                "Global sea level rise with trend lines, rate of change, "
                "and 10-year moving average (1880–2025)")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CORRELATION MATRIX
# ═══════════════════════════════════════════════════════════════════════════════
def export_correlation():
    """
    Export the combined correlation dataset linking temperature,
    emissions, and sea level – perfect for Tableau dual-axis charts.
    """
    fname = prefer_extended("avg_dataset.csv")
    df = pd.read_csv(dp(fname))
    df.columns = [c.strip() for c in df.columns]

    # Rename columns to clean Tableau-friendly names
    rename_map = {}
    for c in df.columns:
        if "Land_Temperature" in c and "Ocean" not in c:
            rename_map[c] = "Avg_Land_Temperature_C"
        elif "LandOcean" in c or "Land_Ocean" in c or ("Land" in c and "Ocean" in c and "Temperature" in c):
            rename_map[c] = "Avg_LandOcean_Temperature_C"
        elif "Emission" in c or "Emit" in c:
            rename_map[c] = "Avg_Emissions_MtCO2e"
        elif "Sealevel" in c or "Sea" in c:
            rename_map[c] = "Avg_Sea_Level_mm"
    df = df.rename(columns=rename_map)

    if "source" not in df.columns:
        df["source"] = "historical"

    # Normalized values (0-1 scale) for overlay charts
    for col in ["Avg_Land_Temperature_C", "Avg_LandOcean_Temperature_C",
                "Avg_Emissions_MtCO2e", "Avg_Sea_Level_mm"]:
        if col in df.columns:
            mn, mx = df[col].min(), df[col].max()
            if mx > mn:
                df[f"{col}_Normalized"] = ((df[col] - mn) / (mx - mn)).round(4)

    # Decade
    df["Decade"] = (df["Year"] // 10) * 10

    float_cols = df.select_dtypes(include=[np.floating]).columns
    df[float_cols] = df[float_cols].round(4)

    return save(df, "tableau_correlation_matrix.csv",
                "Combined yearly dataset correlating temperature, CO₂ emissions, "
                "and sea level with normalized values (1990–2025)")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. COUNTRY-LEVEL TEMPERATURES
# ═══════════════════════════════════════════════════════════════════════════════
def export_country_temperatures():
    """
    Export country-level yearly average temperatures for choropleth maps.
    """
    fname = prefer_extended("GlobalLandTemperaturesByCountry.csv")
    df = pd.read_csv(dp(fname))
    df.columns = [c.strip() for c in df.columns]

    date_col = [c for c in df.columns if c.lower() in ("dt", "date")][0]
    df["dt_parsed"] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=["dt_parsed", "AverageTemperature"])
    df["Year"] = df["dt_parsed"].dt.year

    country_col = [c for c in df.columns if c.lower() == "country"][0]

    # Yearly average per country
    yearly = df.groupby([country_col, "Year"]).agg(
        Avg_Temperature=("AverageTemperature", "mean"),
        Avg_Uncertainty=("AverageTemperatureUncertainty", "mean"),
    ).reset_index()
    yearly = yearly.rename(columns={country_col: "Country"})

    # Add region via continents2 mapping
    try:
        cont = pd.read_csv(dp("continents2.csv.xls"))
        cont = cont.rename(columns={"name": "Country", "region": "Continent"})
        cont = cont[["Country", "Continent", "alpha-2", "alpha-3"]].drop_duplicates("Country")
        yearly = yearly.merge(cont, on="Country", how="left")
    except Exception:
        yearly["Continent"] = "Unknown"

    # Decade
    yearly["Decade"] = (yearly["Year"] // 10) * 10

    # Temperature anomaly per country (relative to 1951-1980 baseline)
    baseline = yearly[(yearly["Year"] >= 1951) & (yearly["Year"] <= 1980)]
    baseline_avg = baseline.groupby("Country")["Avg_Temperature"].mean().reset_index()
    baseline_avg = baseline_avg.rename(columns={"Avg_Temperature": "Baseline_1951_1980"})
    yearly = yearly.merge(baseline_avg, on="Country", how="left")
    yearly["Temp_Anomaly"] = yearly["Avg_Temperature"] - yearly["Baseline_1951_1980"]

    float_cols = yearly.select_dtypes(include=[np.floating]).columns
    yearly[float_cols] = yearly[float_cols].round(4)

    return save(yearly, "tableau_country_temperatures.csv",
                "Country-level yearly average temperatures with continent "
                "mapping and anomalies (1750–2025)")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    print("\n" + "=" * 65)
    print("  📊  Tableau Data Export Pipeline")
    print("  Output: tableau_data/")
    print("=" * 65 + "\n")

    summaries = []

    print("1️⃣  Global Temperatures …")
    summaries.append(export_global_temperatures())

    print("2️⃣  Carbon Emissions …")
    summaries.append(export_carbon_emissions())

    print("3️⃣  Sea Level Rise …")
    summaries.append(export_sea_level())

    print("4️⃣  Correlation Matrix …")
    summaries.append(export_correlation())

    print("5️⃣  Country Temperatures …")
    summaries.append(export_country_temperatures())

    # Save summary metadata
    summary_df = pd.DataFrame(summaries)
    summary_path = os.path.join(OUTPUT_DIR, "tableau_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"\n  📋 Summary → {summary_path}")

    print("\n" + "=" * 65)
    print("  ✅  All Tableau datasets exported successfully!")
    print(f"  📂  Location: {OUTPUT_DIR}")
    print("  📊  Open these CSVs in Tableau Desktop or Tableau Public")
    print("  📄  Or open tableau_workbook.twb for pre-configured views")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
