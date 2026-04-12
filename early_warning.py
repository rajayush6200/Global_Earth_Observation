"""
early_warning.py
================
Early Warning System for Climate Change Detection
--------------------------------------------------
Adds novelty features to the project:
  1. Moving Average   – smooths the trend signal (5-year rolling window)
  2. First Difference  – rate of change (ΔT per year)
  3. Second Difference – acceleration of change (Δ²T per year²)
  4. Warning Indicator – flags years where acceleration > mean + 1.5σ

These features are used both:
  • As standalone static charts saved to the 'outputs/' folder, and
  • As an interactive Plotly tab inside the Dash app (app.py imports this module).
"""

import os
import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

# ── Path helpers ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "Dataset")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def dp(filename: str) -> str:
    """Return absolute path for a Dataset file."""
    return os.path.join(DATASET_DIR, filename)


# ── 1. Load & Prepare Data ───────────────────────────────────────────────────
def load_global_temperature() -> pd.DataFrame:
    """
    Load GlobalTemperatures_extended.csv (preferred) or fall back to
    GlobalTemperatures.csv, compute yearly average land temperature.

    Returns a DataFrame with columns: ['Year', 'LandAverageTemperature', 'source']
    """
    # Try the extended file first (includes 2016–2025 synthetic data)
    for fname in ("GlobalTemperatures_extended.csv", "GlobalTemperatures.csv"):
        try:
            df = pd.read_csv(dp(fname))
            df["dt"] = pd.to_datetime(df["dt"], errors="coerce")
            df = df.dropna(subset=["dt"])
            df["Year"] = df["dt"].dt.year
            source_col = df.get("source", pd.Series("historical", index=df.index))
            df["source"] = source_col
            yearly = (
                df.dropna(subset=["LandAverageTemperature"])
                .groupby("Year")
                .agg(
                    LandAverageTemperature=("LandAverageTemperature", "mean"),
                    source=("source", "last"),
                )
                .reset_index()
            )
            print(f"[early_warning] Loaded {fname}: {len(yearly)} yearly rows "
                  f"({int(yearly['Year'].min())}–{int(yearly['Year'].max())})")
            return yearly
        except Exception as exc:
            print(f"[early_warning] Could not load {fname}: {exc}")
    # Final fallback: avg_dataset
    df2 = pd.read_csv(dp("avg_dataset.csv"))
    col = [c for c in df2.columns if "Land_Temperature" in c and "Ocean" not in c][0]
    df2 = df2.rename(columns={col: "LandAverageTemperature"}).dropna(
        subset=["LandAverageTemperature"]
    )
    df2["source"] = "historical"
    return df2[["Year", "LandAverageTemperature", "source"]].reset_index(drop=True)


# ── 2. Compute Signal Features ───────────────────────────────────────────────
def compute_features(df: pd.DataFrame, window: int = 5, var_window: int = 10) -> pd.DataFrame:
    """
    Given a yearly temperature DataFrame, compute:
      • moving_avg      – rolling mean (smoothed trend, 5-year centred)
      • first_diff      – ΔT per year (rate of warming)
      • second_diff     – Δ²T per year² (acceleration of warming)
      • rolling_var     – rolling variance (10-year, climate instability signal)
      • is_warning      – True where acceleration > mean + 1.5σ
      • is_high_var     – True where rolling_var > median + 1σ (instability alert)
    """
    df = df.copy().sort_values("Year").reset_index(drop=True)

    # 5-year centred moving average
    df["moving_avg"] = (
        df["LandAverageTemperature"].rolling(window=window, center=True).mean()
    )

    # First difference: rate of change
    df["first_diff"] = df["moving_avg"].diff()

    # Second difference: acceleration
    df["second_diff"] = df["first_diff"].diff()

    # Rolling variance (10-year window) — instability / volatility signal
    df["rolling_var"] = (
        df["LandAverageTemperature"].rolling(window=var_window, center=False).var()
    )

    # Acceleration warning: Δ²T > mean + 1.5σ
    mu = df["second_diff"].mean()
    sigma = df["second_diff"].std()
    threshold = mu + 1.5 * sigma
    df["is_warning"] = df["second_diff"] > threshold
    df["threshold"] = threshold

    # High-variance warning: rolling_var > median + 1σ
    var_med = df["rolling_var"].median()
    var_std = df["rolling_var"].std()
    df["is_high_var"] = df["rolling_var"] > (var_med + var_std)

    return df


# ── 3. Individual Plotly Figures ─────────────────────────────────────────────
def fig_moving_average(df: pd.DataFrame) -> go.Figure:
    """Moving Average overlay on raw temperature."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["Year"],
            y=df["LandAverageTemperature"],
            mode="lines",
            name="Annual Average",
            line=dict(color="#a8d8ea", width=1.5),
            opacity=0.7,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["Year"],
            y=df["moving_avg"],
            mode="lines",
            name="5-Year Moving Average",
            line=dict(color="#ff6b6b", width=3),
        )
    )
    fig.update_layout(
        title="🌡️ Global Land Temperature with 5-Year Moving Average",
        xaxis_title="Year",
        yaxis_title="Temperature (°C)",
        template="plotly_dark",
        legend=dict(orientation="h", y=-0.15),
        title_font=dict(size=20),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#16213e",
    )
    return fig


def fig_first_difference(df: pd.DataFrame) -> go.Figure:
    """First difference (rate of warming)."""
    colors = ["#e74c3c" if v > 0 else "#3498db" for v in df["first_diff"].fillna(0)]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["Year"],
            y=df["first_diff"],
            marker_color=colors,
            name="ΔT (Rate of Change)",
            hovertemplate="Year: %{x}<br>ΔT: %{y:.4f}°C<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
    fig.update_layout(
        title="📈 First Difference – Rate of Temperature Change (°C/year)",
        xaxis_title="Year",
        yaxis_title="ΔT (°C / year)",
        template="plotly_dark",
        title_font=dict(size=20),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#16213e",
    )
    return fig


def fig_second_difference(df: pd.DataFrame) -> go.Figure:
    """Second difference (acceleration of warming) with warning threshold."""
    threshold = df["threshold"].iloc[-1] if "threshold" in df.columns else None
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["Year"],
            y=df["second_diff"],
            mode="lines+markers",
            name="Δ²T (Acceleration)",
            line=dict(color="#f39c12", width=2),
            marker=dict(size=4),
            hovertemplate="Year: %{x}<br>Δ²T: %{y:.5f}°C/yr²<extra></extra>",
        )
    )
    if threshold is not None:
        fig.add_hline(
            y=threshold,
            line_dash="dot",
            line_color="#e74c3c",
            annotation_text=f"Warning threshold ({threshold:.4f}°C/yr²)",
            annotation_position="top left",
            annotation_font=dict(color="#e74c3c"),
        )
    fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
    fig.update_layout(
        title="⚡ Second Difference – Acceleration of Temperature Change",
        xaxis_title="Year",
        yaxis_title="Δ²T (°C / year²)",
        template="plotly_dark",
        title_font=dict(size=20),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#16213e",
    )
    return fig


def fig_early_warning(df: pd.DataFrame) -> go.Figure:
    """
    Early warning indicator: highlights years where acceleration crosses
    the 1.5σ threshold — potential early signs of accelerating climate change.
    """
    warnings_df = df[df["is_warning"] == True]
    normal_df = df[df["is_warning"] == False]

    fig = go.Figure()

    # Background temperature trend
    fig.add_trace(
        go.Scatter(
            x=df["Year"],
            y=df["moving_avg"],
            mode="lines",
            name="5-Year Moving Average",
            line=dict(color="#74b9ff", width=2),
            opacity=0.7,
        )
    )

    # Normal years
    fig.add_trace(
        go.Scatter(
            x=normal_df["Year"],
            y=normal_df["moving_avg"],
            mode="markers",
            name="Normal Year",
            marker=dict(color="#00b894", size=7, symbol="circle"),
            hovertemplate="Year: %{x}<br>Temp: %{y:.2f}°C<extra>Normal</extra>",
        )
    )

    # Warning years
    fig.add_trace(
        go.Scatter(
            x=warnings_df["Year"],
            y=warnings_df["moving_avg"],
            mode="markers",
            name="⚠️ Warning Year",
            marker=dict(
                color="#d63031",
                size=14,
                symbol="triangle-up",
                line=dict(color="white", width=1),
            ),
            hovertemplate="Year: %{x}<br>Temp: %{y:.2f}°C<br><b>ACCELERATION WARNING</b><extra></extra>",
        )
    )

    n_warnings = len(warnings_df)
    fig.update_layout(
        title=f"🚨 Early Warning Indicator – {n_warnings} Acceleration Events Detected",
        xaxis_title="Year",
        yaxis_title="Temperature (°C) – 5-Year Moving Average",
        template="plotly_dark",
        title_font=dict(size=20),
        legend=dict(orientation="h", y=-0.15),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#16213e",
        annotations=[
            dict(
                text=(
                    f"Red triangles = years where temperature acceleration exceeded "
                    f"mean + 1.5σ threshold.<br>"
                    f"These are potential early signals of accelerating climate change."
                ),
                xref="paper",
                yref="paper",
                x=0.5,
                y=-0.30,
                showarrow=False,
                font=dict(size=12, color="#b2bec3"),
                align="center",
            )
        ],
    )
    return fig


def fig_rolling_variance(df: pd.DataFrame) -> go.Figure:
    """
    Rolling variance chart — detects increasing climate instability/volatility.
    High variance = more erratic year-to-year temperature swings.
    Shows a secondary axis for the moving average for context.
    A vertical dashed line separates historical from synthetic data.
    """
    from plotly.subplots import make_subplots

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Rolling variance bars
    high_var = df["is_high_var"] == True
    colors = ["#fdcb6e" if v else "#636e72" for v in high_var]

    fig.add_trace(
        go.Bar(
            x=df["Year"],
            y=df["rolling_var"],
            name="10-Year Rolling Variance",
            marker_color=colors,
            opacity=0.8,
            hovertemplate="Year: %{x}<br>Variance: %{y:.4f}°C²<extra></extra>",
        ),
        secondary_y=False,
    )

    # Moving average overlay (right axis)
    fig.add_trace(
        go.Scatter(
            x=df["Year"],
            y=df["moving_avg"],
            name="5-Year Moving Avg Temp",
            mode="lines",
            line=dict(color="#ff6b6b", width=2.5),
            hovertemplate="Year: %{x}<br>Temp: %{y:.2f}°C<extra></extra>",
        ),
        secondary_y=True,
    )

    # Vertical dashed line at 2020 — real data ends here
    fig.add_vline(
        x=2020,
        line_dash="dot",
        line_color="#a29bfe",
        annotation_text="◀ Historical | Synthetic ▶",
        annotation_position="top",
        annotation_font=dict(color="#a29bfe", size=12),
    )

    # High-variance threshold line
    var_threshold = df["rolling_var"].median() + df["rolling_var"].std()
    fig.add_hline(
        y=var_threshold,
        line_dash="dash",
        line_color="#fdcb6e",
        annotation_text=f"High-variance threshold ({var_threshold:.4f}°C²)",
        annotation_position="bottom right",
        annotation_font=dict(color="#fdcb6e", size=11),
        secondary_y=False,
    )

    n_high = high_var.sum()
    fig.update_layout(
        title=f"📊 Rolling Variance (Instability Indicator) – {n_high} High-Variance Years",
        xaxis_title="Year",
        template="plotly_dark",
        title_font=dict(size=20),
        legend=dict(orientation="h", y=-0.15),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#16213e",
        barmode="overlay",
    )
    fig.update_yaxes(title_text="Variance (°C²)", secondary_y=False)
    fig.update_yaxes(title_text="Temperature (°C)", secondary_y=True)
    return fig


# ── 4. Dashboard Panel (composite) ───────────────────────────────────────────
def build_early_warning_panel() -> dict:
    """
    Returns a dict of five Plotly figures for the Dash Early Warning tab.
    Now includes rolling variance (instability) chart and uses extended dataset.
    Called by app.py.
    """
    try:
        df = load_global_temperature()
        df = compute_features(df)
        synthetic_start = int(df[df.get("source", "historical") == "synthetic"]["Year"].min()) \
            if "source" in df.columns and (df["source"] == "synthetic").any() else None
        return {
            "moving_avg":      fig_moving_average(df),
            "first_diff":      fig_first_difference(df),
            "second_diff":     fig_second_difference(df),
            "warning":         fig_early_warning(df),
            "rolling_var":     fig_rolling_variance(df),
            "warning_years":   df[df["is_warning"] == True]["Year"].tolist(),
            "high_var_years":  df[df["is_high_var"] == True]["Year"].tolist(),
            "total_years":     len(df),
            "synthetic_start": synthetic_start,
        }
    except Exception as exc:
        print(f"[early_warning] Error building panel: {exc}")
        return {}


# ── 5. Save Static Outputs ───────────────────────────────────────────────────
def save_static_outputs():
    """
    Save all four early-warning charts as PNG images to outputs/ folder.
    Useful for reports and academic submissions.
    """
    print("[early_warning] Loading data …")
    df = load_global_temperature()
    df = compute_features(df)

    charts = {
        "01_moving_average.png": fig_moving_average(df),
        "02_first_difference.png": fig_first_difference(df),
        "03_second_difference.png": fig_second_difference(df),
        "04_early_warning_indicator.png": fig_early_warning(df),
    }

    for fname, fig in charts.items():
        path = os.path.join(OUTPUT_DIR, fname)
        try:
            fig.write_image(path, width=1200, height=600, scale=2)
            print(f"  ✅ Saved: {path}")
        except Exception as exc:
            # kaleido may not be installed – save as HTML instead
            html_path = path.replace(".png", ".html")
            fig.write_html(html_path)
            print(f"  ⚠️  PNG failed ({exc}); saved HTML: {html_path}")

    # Summary stats
    n_warn = (df["is_warning"] == True).sum()
    print(f"\n[early_warning] Summary:")
    print(f"  Years analysed  : {len(df)}")
    print(f"  Warning events  : {n_warn}")
    print(f"  Threshold (Δ²T) : {df['threshold'].iloc[-1]:.5f} °C/yr²")
    warn_years = df[df["is_warning"] == True]["Year"].tolist()
    if warn_years:
        print(f"  Warning years   : {warn_years}")


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    save_static_outputs()
