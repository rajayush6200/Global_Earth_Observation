"""
app.py  –  Climate Change Data Visualization Dashboard
=======================================================
Converted from Integration_dash.ipynb with all bugs fixed:
  • Removed deprecated dash_core_components / dash_html_components imports
  • Fixed all dataset file paths (relative → absolute via Dataset/ subfolder)
  • Removed bokeh dependency (unused)
  • Fixed UpdatedCity_Temperatures → UpdatedMajorCity_temperatures.csv
  • Fixed city_temperature.csv / city_temperature_2.csv → same file
  • Fixed update_carbon_emissions_bar returning go.Frame instead of go.Figure
  • Fixed duplicate dropdown IDs across tabs (scoped per-tab)
  • Added Early Warning tab from early_warning.py

Run:  python app.py
Then open: http://127.0.0.1:8050
"""

import os, base64, json, warnings
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.graph_objs as gobj
from dash import Dash, dcc, html, Input, Output, State
import dash
import sys

from tableau_section import build_tableau_section

# Ensure stdout can handle utf-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

warnings.filterwarnings("ignore")

# ─── Path helpers ─────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "Dataset")

def dp(f):
    return os.path.join(DATASET_DIR, f)


# ─── 1. SEA LEVEL DATA & FIGURES ──────────────────────────────────────────────
try:
    _sea_file = "Global_sea_level_rise_extended.csv" if os.path.exists(dp("Global_sea_level_rise_extended.csv")) else "Global_sea_level_rise.csv"
    data_sea = pd.read_csv(dp(_sea_file))
    sea_ok = True
except Exception as e:
    print(f"[SEA] Load error: {e}")
    data_sea = pd.DataFrame({"Year": [], "Sea Level": []})
    sea_ok = False

fig_bar = go.Figure(
    data=[go.Bar(x=data_sea["Year"], y=data_sea["Sea Level"])],
    layout=go.Layout(
        title=go.layout.Title(text="Bar Chart – Sea Level Rise"),
        xaxis=go.layout.XAxis(title=go.layout.xaxis.Title(text="Year")),
        yaxis=go.layout.YAxis(title=go.layout.yaxis.Title(text="Sea Level (mm)")),
    )
)

area_fig = px.area(data_sea, x="Year", y="Sea Level", title="Area Chart – Sea Level Rise",
                   labels={"Sea Level": "Sea Level (mm)"},
                   color_discrete_sequence=["#3D9970"])
area_fig.update_traces(mode="lines", fillcolor="aqua",
                       line_color="darkblue", line_shape="spline",
                       line_smoothing=1.3, line_width=3, opacity=0.25)
area_fig.update_layout(font_family="Arial", title_font_size=22,
                       plot_bgcolor="white")

fig_box = go.Figure()
fig_box.add_trace(go.Box(
    y=data_sea["Sea Level"], name="Sea Level", boxmean=True,
    fillcolor="#d9b3ff", marker_color="blue", line_color="#00004d"))
fig_box.update_layout(title="Box & Whiskers – Sea Level", font_family="Arial",
                      title_font_size=22, plot_bgcolor="#f7f7f7")

scatter_fig = px.scatter(data_sea, x="Year", y="Sea Level",
                         title="Scatter Plot – Sea Level",
                         labels={"Sea Level": "Sea Level (mm)"},
                         color_discrete_sequence=["#3D9970"])
scatter_fig.update_layout(font_family="Arial", title_font_size=22, plot_bgcolor="white")

trace_m = go.Scatter(x=data_sea["Year"], y=data_sea["Sea Level"], mode="markers", name="")
trace_l = go.Scatter(x=data_sea["Year"], y=data_sea["Sea Level"], mode="lines",
                     name="Lines", line=dict(width=3, color="blue"))
fig_line = go.Figure(data=[trace_m, trace_l])
if sea_ok and len(data_sea) > 0:
    fig_line.update_xaxes(range=[data_sea["Year"].min(), data_sea["Year"].max()])
fig_line.update_layout(xaxis_title="Year", yaxis_title="Sea Level (mm)",
                       template="plotly_dark", title="Line Chart – Sea Level",
                       title_font=dict(size=22))

# ─── 2. CORRELATION DATA & FIGURES ────────────────────────────────────────────
try:
    # Prefer the extended dataset (covers 1990–2025 with synthetic 2021–2025)
    _corr_file = "avg_dataset_extended.csv" if os.path.exists(dp("avg_dataset_extended.csv")) else "avg_dataset.csv"
    data_temp = pd.read_csv(dp(_corr_file))
    # Normalise column names (handle unicode subscript characters)
    data_temp.columns = [c.strip() for c in data_temp.columns]
    col_land    = [c for c in data_temp.columns if "Land_Temperature" in c and "Ocean" not in c][0]
    col_ocean   = [c for c in data_temp.columns if "LandOcean" in c or "Land_Ocean" in c or ("Land" in c and "Ocean" in c)][0]
    col_emit    = [c for c in data_temp.columns if "Emission" in c or "Emit" in c][0]
    col_sea     = [c for c in data_temp.columns if "Sealevel" in c or "Sea" in c][0]

    years    = data_temp["Year"]
    temp     = data_temp[col_land]
    temp1    = data_temp[col_ocean]
    emissions = data_temp[col_emit]
    sea_corr  = data_temp[col_sea]
    corr_ok = True
except Exception as e:
    print(f"[CORR] Load error: {e}")
    years = temp = temp1 = emissions = sea_corr = pd.Series([])
    col_land = col_ocean = col_emit = col_sea = ""
    corr_ok = False

fig_corr1 = go.Figure()
if corr_ok:
    fig_corr1.add_trace(go.Scatter(x=years, y=temp, mode="lines+markers",
        name="Land Temperature", line=dict(color="red", width=2)))
    fig_corr1.add_trace(go.Scatter(x=years, y=emissions, mode="lines+markers",
        name="Carbon Emissions", line=dict(color="blue", width=2), yaxis="y2"))
    fig_corr1.add_trace(go.Scatter(x=years, y=sea_corr, mode="lines+markers",
        name="Sea Level", line=dict(color="green", width=2), yaxis="y3"))
    fig_corr1.update_layout(
        title="Correlation – Land Temp, CO2 Emissions & Sea Level (1990–2020)",
        xaxis=dict(title="Year"),
        yaxis=dict(title="Temp (°C)", color="red", title_font=dict(size=14)),
        yaxis2=dict(title="Carbon Emissions (MtCO2e)", overlaying="y", side="right",
                    color="blue", title_font=dict(size=14)),
        yaxis3=dict(title="Sea Level (mm)", overlaying="y", side="right",
                    position=0.94, color="green", title_font=dict(size=14)),
        legend=dict(orientation="h", y=-0.2),
    )

fig_corr3 = go.Figure()
if corr_ok:
    fig_corr3.add_trace(go.Scatter(x=years, y=temp1, mode="lines+markers",
        name="Land+Ocean Temp", line=dict(color="red", width=2, shape="spline")))
    fig_corr3.add_trace(go.Scatter(x=years, y=emissions, mode="lines+markers",
        name="Carbon Emissions", line=dict(color="blue", width=2, shape="spline"), yaxis="y2"))
    fig_corr3.add_trace(go.Scatter(x=years, y=sea_corr, mode="lines+markers",
        name="Sea Level", line=dict(color="green", width=2, shape="spline"), yaxis="y3"))
    fig_corr3.update_layout(
        title="Correlation – Land+Ocean Temp, CO2 & Sea Level (1990–2020)",
        xaxis=dict(title="Year"),
        yaxis=dict(title="Temp (°C)", color="red", title_font=dict(size=14)),
        yaxis2=dict(title="Carbon Emissions (MtCO2e)", overlaying="y", side="right",
                    color="blue", title_font=dict(size=14)),
        yaxis3=dict(title="Sea Level (mm)", overlaying="y", side="right",
                    position=0.94, color="green", title_font=dict(size=14)),
        legend=dict(orientation="h", y=-0.2),
    )

if corr_ok:
    subset = data_temp[["Year", col_land, col_emit, col_sea]]
    fig_corr2 = px.scatter(subset, x=col_emit, y=col_land, color="Year",
        size=col_emit, hover_data=["Year", col_land, col_emit, col_sea],
        title="Scatter – Emissions vs Land Temperature")
    fig_corr_temp = {
        "data": [
            {"x": data_temp["Year"].tolist(), "y": temp.tolist(),
             "type": "bar", "name": "Avg Land Temp", "marker": {"color": "green"}},
            {"x": data_temp["Year"].tolist(), "y": temp1.tolist(),
             "type": "bar", "name": "Avg Land+Ocean Temp", "marker": {"color": "pink"}},
        ],
        "layout": {"title": "Average Temperatures by Year",
                   "xaxis": {"title": "Year"}, "yaxis": {"title": "Temperature", "range": [8, 17]}},
    }
    fig_emissions = px.bar(data_temp, x="Year",
        y=[col_emit, col_land, col_ocean],
        title="Greenhouse Gas Emissions vs Temperature (Stacked)")
    fig_emissions.update_layout(barmode="stack", plot_bgcolor="white",
                                 title_font_size=20, font_family="Arial")
else:
    fig_corr2 = go.Figure()
    fig_corr_temp = {"data": [], "layout": {}}
    fig_emissions = go.Figure()

# ─── 3. TEMPERATURE DATA & FIGURES ────────────────────────────────────────────
print("[TEMP] Loading GeoJSON files …")
try:
    india_states = json.load(open(dp("states_india.geojson"), encoding="utf-8"))
    us_states    = json.load(open(dp("us-states.json"),        encoding="utf-8"))
    can_states   = json.load(open(dp("canada.geojson"),        encoding="utf-8"))
    china_states = json.load(open(dp("China_geo.json"),        encoding="utf-8"))
    rus_states   = json.load(open(dp("Russia_geo.json"),       encoding="utf-8"))
    brz_states   = json.load(open(dp("brazil_geo.json"),       encoding="utf-8"))
    geo_ok = True
    print("[TEMP] GeoJSON loaded.")
except Exception as e:
    print(f"[TEMP] GeoJSON error: {e}")
    geo_ok = False

state_id_map1 = {}  # brazil
state_id_map2 = {}  # russia
state_id_map3 = {}  # india
state_id_map4 = {}  # china
state_id_map5 = {}  # canada
state_id_map6 = {}  # us

if geo_ok:
    for feat in brz_states["features"]:
        state_id_map1[feat["properties"]["name"]] = feat["id"]
    for feat in rus_states["features"]:
        feat["id"] = feat["properties"]["ID_1"]
        state_id_map2[feat["properties"]["NAME_1"]] = feat["id"]
    for feat in india_states["features"]:
        feat["id"] = feat["properties"]["state_code"]
        state_id_map3[feat["properties"]["st_nm"]] = feat["id"]
    for feat in china_states["features"]:
        feat["id"] = feat["properties"]["HASC_1"]
        state_id_map4[feat["properties"]["NAME_1"]] = feat["id"]
    for feat in can_states["features"]:
        feat["id"] = feat["properties"]["cartodb_id"]
        state_id_map5[feat["properties"]["name"]] = feat["id"]
    for feat in us_states["features"]:
        state_id_map6[feat["properties"]["name"]] = feat["id"]

def safe_map_id(df, col, id_map):
    """Map state names to IDs, skip unknown entries."""
    df = df.copy()
    df["id"] = df[col].map(id_map)
    df = df.dropna(subset=["id"])
    return df

print("[TEMP] Loading country temperature CSVs …")
try:
    df1 = safe_map_id(pd.read_csv(dp("India_temperatures.csv")),   "State", state_id_map3)
    df2 = safe_map_id(pd.read_csv(dp("China_temperatures.csv")),   "State", state_id_map4)
    df3 = safe_map_id(pd.read_csv(dp("Canada_temperatures.csv")),  "State", state_id_map5)
    df4 = safe_map_id(pd.read_csv(dp("Brazil_temperatures.csv")),  "State", state_id_map1)
    df5 = safe_map_id(pd.read_csv(dp("Updated_Russia_temperatures.csv")), "State", state_id_map2)
    df6 = safe_map_id(pd.read_csv(dp("US_temperatures.csv")),      "State", state_id_map6)
    country_csv_ok = True
    print("[TEMP] Country CSVs loaded.")
except Exception as e:
    print(f"[TEMP] Country CSV error: {e}")
    country_csv_ok = False
    _empty = pd.DataFrame({"id": [], "State": [], "AverageTemperature": []})
    df1 = df2 = df3 = df4 = df5 = df6 = _empty

def make_choro(df, geojson, title, lat, lon, zoom):
    return px.choropleth_mapbox(
        df, locations="id", geojson=geojson,
        color="AverageTemperature", color_continuous_scale="Turbo",
        hover_name="State", hover_data=["AverageTemperature"],
        title=title, mapbox_style="carto-positron",
        center={"lat": lat, "lon": lon}, zoom=zoom, opacity=0.4,
        width=1380, height=750,
    )

if geo_ok and country_csv_ok:
    fig11 = make_choro(df1, india_states,  "Average Temperature – INDIA",  24, 78, 3.7)
    fig21 = make_choro(df2, china_states,  "Average Temperature – CHINA",  37, 104, 3)
    fig31 = make_choro(df3, can_states,    "Average Temperature – CANADA", 72, -99, 1.9)
    fig41 = make_choro(df4, brz_states,    "Average Temperature – BRAZIL", -12, -56, 3)
    fig51 = make_choro(df5, rus_states,    "Average Temperature – RUSSIA", 68, 101, 2.1)
    fig61 = make_choro(df6, us_states,     "Average Temperature – USA",    53, -113, 2.3)
else:
    fig11 = fig21 = fig31 = fig41 = fig51 = fig61 = go.Figure()

# Heatmap – city temperatures
print("[TEMP] Loading city heatmap data …")
try:
    # UpdatedMajorCity_temperatures.csv has: dt, AverageTemperature, ..., Latitude_Float, Longitude_Float, City
    _city_file = "UpdatedMajorCity_temperatures_extended.csv" if os.path.exists(dp("UpdatedMajorCity_temperatures_extended.csv")) else "UpdatedMajorCity_temperatures.csv"
    data_heatmap = pd.read_csv(dp(_city_file))
    data_heatmap = data_heatmap.dropna(subset=["AverageTemperature"])
    # Parse year for animation
    data_heatmap["dt_parsed"] = pd.to_datetime(data_heatmap["dt"], errors="coerce")
    data_heatmap["dt"] = data_heatmap["dt_parsed"].dt.strftime("%Y-%m").fillna("Unknown")
    fig_heat = px.density_mapbox(
        data_heatmap, lat="Latitude_Float", lon="Longitude_Float",
        z="AverageTemperature", hover_data=["City"],
        radius=8, zoom=1, mapbox_style="carto-positron",
        animation_frame="dt", opacity=0.5,
        title="Average Temperature Heatmap by Cities")
    print("[TEMP] City heatmap ready.")
except Exception as e:
    print(f"[TEMP] City heatmap error: {e}")
    fig_heat = go.Figure()

# Choropleth – countries
print("[TEMP] Loading country choropleth …")
try:
    _country_file = "GlobalLandTemperaturesByCountry_extended.csv" if os.path.exists(dp("GlobalLandTemperaturesByCountry_extended.csv")) else "GlobalLandTemperaturesByCountry.csv"
    df_choro = pd.read_csv(dp(_country_file))
    df_choro.columns = [c.strip() for c in df_choro.columns]
    date_col = [c for c in df_choro.columns if c.lower() in ("dt", "date")][0]
    df_choro = df_choro.dropna()
    df_choro["date_parsed"] = pd.to_datetime(df_choro[date_col], errors="coerce")
    df_choro["Year"] = df_choro["date_parsed"].dt.year
    country_col = [c for c in df_choro.columns if c.lower() == "country"][0]
    df_choro = df_choro.groupby([country_col, "Year"])["AverageTemperature"].mean().reset_index()
    df_choro.rename(columns={country_col: "Country"}, inplace=True)
    fig_choro = px.choropleth(df_choro, locations="Country",
                              locationmode="country names",
                              color="AverageTemperature",
                              color_continuous_scale="Turbo",
                              animation_frame="Year",
                              title="Choropleth – Average Temperatures by Country")
    print("[TEMP] Country choropleth ready.")
except Exception as e:
    print(f"[TEMP] Choropleth error: {e}")
    fig_choro = go.Figure()

# Globe (3-D orthographic) ─────────────────────────────────────────────────
print("[TEMP] Building globe …")
try:
    glob_df = pd.read_csv(dp("GlobalLandTemperaturesByCountry-2.csv"))
    glob_df.columns = [c.strip() for c in glob_df.columns]
    exclude = ["Denmark","Antarctica","France","Europe","Netherlands",
               "United Kingdom","Africa","South America"]
    glob_df = glob_df[~glob_df["Country"].isin(exclude)]
    replacements = {"Denmark (Europe)": "Denmark", "France (Europe)": "France",
                    "Netherlands (Europe)": "Netherlands",
                    "United Kingdom (Europe)": "United Kingdom"}
    glob_df["Country"] = glob_df["Country"].replace(replacements)
    countries_glob = np.unique(glob_df["Country"])
    mean_temp = [glob_df[glob_df["Country"] == c]["AverageTemperature"].mean()
                 for c in countries_glob]
    data_globe = [dict(type="choropleth", locations=countries_glob, z=mean_temp,
                       locationmode="country names", text=countries_glob,
                       marker=dict(line=dict(color="rgb(0,0,0)", width=1)),
                       colorbar=dict(title="Avg Temp °C"))]
    layout_globe = dict(
        title="3-D Globe – Average Land Temperature by Country",
        geo=dict(showframe=False, showocean=True, oceancolor="rgb(0,200,255)",
                 projection=dict(type="orthographic",
                                 rotation=dict(lon=60, lat=10))))
    fig_globe = dict(data=data_globe, layout=layout_globe)
    print("[TEMP] Globe ready.")
except Exception as e:
    print(f"[TEMP] Globe error: {e}")
    fig_globe = go.Figure()

# Earth temperature timeline ───────────────────────────────────────────────
try:
    _tl_file = "avg_dataset_extended.csv" if os.path.exists(dp("avg_dataset_extended.csv")) else "avg_dataset.csv"
    data_timeline = pd.read_csv(dp(_tl_file))
    col_lt = [c for c in data_timeline.columns if "Land_Temperature" in c and "Ocean" not in c][0]
    fig_timeline = px.line(data_timeline, x="Year", y=col_lt,
                           title="Earth Temperature Timeline",
                           labels={col_lt: "Avg Land Temperature (°C)"})
    fig_timeline.update_layout(title_font_size=22, font_family="Arial",
                                plot_bgcolor="white")
except Exception as e:
    print(f"[TEMP] Timeline error: {e}")
    fig_timeline = go.Figure()

# Globe-2D scatter geo – max vs mean temperature difference ───────────────
print("[TEMP] Building globe-2D scatter …")
try:
    _city2_file = "GlobalLandTemperaturesByMajorCity_extended.csv" if os.path.exists(dp("GlobalLandTemperaturesByMajorCity_extended.csv")) else "GlobalLandTemperaturesByMajorCity.csv"
    c2 = pd.read_csv(dp(_city2_file))
    c2["Date"] = pd.to_datetime(c2["dt"], errors="coerce")
    c2["year"] = c2["Date"].dt.year
    by_year2 = c2.groupby(["year","City","Country","Latitude","Longitude"]).mean().reset_index()
    cont_map = pd.read_csv(dp("continents2.csv.xls"))
    cont_map["Country"] = cont_map["name"]
    cont_map = cont_map[["Country","region","alpha-2","alpha-3"]]
    data_mm = pd.merge(by_year2, cont_map, on="Country", how="left")
    data_mm = data_mm[data_mm["year"] >= 1825]
    map_c = data_mm.dropna().groupby(["region","Country","year","alpha-3"])["AverageTemperature"].mean().reset_index()
    map_c["AverageTemperature"] += 6
    mean2  = map_c.groupby(["region","Country","alpha-3"])["AverageTemperature"].mean().reset_index()
    max2   = map_c.groupby(["region","Country","alpha-3"])["AverageTemperature"].max().reset_index()
    diff2  = pd.merge(mean2, max2, on=["region","Country","alpha-3"])
    diff2["diff"] = diff2["AverageTemperature_y"] - diff2["AverageTemperature_x"]
    diff2.rename(columns={"AverageTemperature_y": "Max Avg Temp",
                           "AverageTemperature_x": "Overall Avg Temp"}, inplace=True)
    fig_maxmin = px.scatter_geo(diff2, locations="alpha-3", color="Overall Avg Temp",
        hover_name="Country", size="diff", size_max=15,
        projection="natural earth", opacity=0.8,
        color_continuous_scale=("#283747","#2874A6","#3498DB","#F5B041","#E67E22","#A93226"),
        title="Globe Map – Temperature Difference (Max vs Mean) since 1825")
    fig_maxmin.update_layout(template="ggplot2")
    print("[TEMP] Globe-2D ready.")
except Exception as e:
    print(f"[TEMP] Globe-2D error: {e}")
    fig_maxmin = go.Figure()

# Horizontal bar – country rank by temperature increase ────────────────────
print("[TEMP] Building country rank bar …")
try:
    _city3_file = "GlobalLandTemperaturesByMajorCity_extended.csv" if os.path.exists(dp("GlobalLandTemperaturesByMajorCity_extended.csv")) else "GlobalLandTemperaturesByMajorCity.csv"
    c3 = pd.read_csv(dp(_city3_file))
    c3["Date"] = pd.to_datetime(c3["dt"], errors="coerce")
    c3["year"] = c3["Date"].dt.year
    by_year3 = c3.groupby(["year","City","Country"]).mean(numeric_only=True).reset_index()
    cont_map3 = pd.read_csv(dp("continents2.csv.xls"))
    cont_map3["Country"] = cont_map3["name"]
    cont_map3 = cont_map3[["Country","region","alpha-2","alpha-3"]]
    data_diff = pd.merge(by_year3, cont_map3, on="Country", how="left")
    data_diff = data_diff[data_diff["year"] >= 1825].dropna()
    countries_d = data_diff.groupby(["region","Country","year"])["AverageTemperature"].mean().reset_index()
    mean_d   = countries_d.groupby(["Country","region"])["AverageTemperature"].mean().reset_index()
    max_d    = countries_d.groupby(["Country","region"])["AverageTemperature"].max().reset_index()
    diff_d   = pd.merge(mean_d, max_d, on=["Country","region"])
    diff_d["diff"] = diff_d["AverageTemperature_y"] - diff_d["AverageTemperature_x"]
    sort_d   = diff_d[["Country","region","diff"]].sort_values("diff")
    fig_diff = px.bar(sort_d, x="diff", y="Country", orientation="h",
                     color="diff", color_continuous_scale="RdBu_r",
                     height=3000, width=900,
                     title="Countries Ranked – Temperature Increase since 1825")
    fig_diff.update_layout(template="ggplot2")
    print("[TEMP] Rank bar ready.")
except Exception as e:
    print(f"[TEMP] Rank bar error: {e}")
    fig_diff = go.Figure()

# Line chart – continents ──────────────────────────────────────────────────
print("[TEMP] Building continent lines …")
try:
    _dfcity_file = "UpdatedMajorCity_temperatures_extended.csv" if os.path.exists(dp("UpdatedMajorCity_temperatures_extended.csv")) else "UpdatedMajorCity_temperatures.csv"
    df_city = pd.read_csv(dp(_dfcity_file))
    df_city.columns = [c.strip() for c in df_city.columns]
    df_city["Date"] = pd.to_datetime(df_city["dt"], errors="coerce")
    df_city["Year"] = df_city["Date"].dt.year
    df_city["Month"] = df_city["Date"].dt.month
    df_city["Day"]   = 1
    df_city = df_city.rename(columns={"AverageTemperature": "AvgTemperature"})
    df_city = df_city.dropna(subset=["AvgTemperature"])
    # Add a dummy Region if missing
    if "Region" not in df_city.columns:
        cont_map4 = pd.read_csv(dp("continents2.csv.xls"))
        cont_map4 = cont_map4.rename(columns={"name": "Country", "region": "Region"})
        df_city = pd.merge(df_city, cont_map4[["Country","Region"]], on="Country", how="left")
    df_city = df_city.dropna(subset=["Region"])
    df_city = df_city[(df_city["Year"] > 1994) & (df_city["Year"] <= 2025)]
    df_city = df_city[df_city["AvgTemperature"] > -70]
    fig_lines = px.line(
        df_city.groupby(["Region","Year"])["AvgTemperature"].mean().reset_index(),
        x="Year", y="AvgTemperature", color="Region",
        title="Average Temperature per Continent (1995–2019)")
    fig_lines.update_traces(mode="markers+lines")
    fig_lines.update_layout(hovermode="x", plot_bgcolor="#FFFFFF")
    print("[TEMP] Continent lines ready.")
except Exception as e:
    print(f"[TEMP] Continent lines error: {e}")
    fig_lines = go.Figure()

# city_temperature_2 → calendar heatmap source (same file) ────────────────
try:
    _cc_file = "UpdatedMajorCity_temperatures_extended.csv" if os.path.exists(dp("UpdatedMajorCity_temperatures_extended.csv")) else "UpdatedMajorCity_temperatures.csv"
    fig_CC = pd.read_csv(dp(_cc_file))
    fig_CC.columns = [c.strip() for c in fig_CC.columns]
    fig_CC["Date"] = pd.to_datetime(fig_CC["dt"], errors="coerce")
    fig_CC["Year"]  = fig_CC["Date"].dt.year.fillna(2000).astype(int)
    fig_CC["Month"] = fig_CC["Date"].dt.month.fillna(1).astype(int)
    fig_CC["Day"]   = fig_CC["Date"].dt.day.fillna(1).astype(int)
    fig_CC = fig_CC.rename(columns={"AverageTemperature": "AvgTemperature"})
    if "Country" not in fig_CC.columns:
        fig_CC["Country"] = "Unknown"
    if "City" not in fig_CC.columns:
        fig_CC["City"] = "Unknown"
    fig_CC = fig_CC.dropna(subset=["AvgTemperature"])
    cal_ok = True
    print("[TEMP] Calendar source loaded.")
except Exception as e:
    print(f"[TEMP] Calendar source error: {e}")
    fig_CC = pd.DataFrame({"Country": ["India"], "City": ["Delhi"],
                            "Year": [2000], "Month": [1], "Day": [1],
                            "AvgTemperature": [25.0]})
    cal_ok = False

# ─── 4. CARBON EMISSIONS DATA & FIGURES ───────────────────────────────────────
print("[CO2] Loading emissions data …")
try:
    data_carbon_scatter = pd.read_csv(dp("historical_emissions.csv"))
    data_carbon_scatter.columns = [c.strip() for c in data_carbon_scatter.columns]
    data_carbon_bar     = data_carbon_scatter.copy()
    data_carbon_line    = data_carbon_scatter.copy()
    co2_col = [c for c in data_carbon_scatter.columns if "CO2" in c or "Emission" in c][0]
    data_carbon_scatter.rename(columns={co2_col: "CO2 Emissions"}, inplace=True)
    data_carbon_bar.rename(columns={co2_col: "CO2 Emissions"}, inplace=True)
    data_carbon_line.rename(columns={co2_col: "CO2 Emissions"}, inplace=True)

    top5 = data_carbon_bar.groupby("Country")["CO2 Emissions"].sum().nlargest(5).reset_index()
    top5_df = data_carbon_bar[data_carbon_bar["Country"].isin(top5["Country"])]
    bottom5 = data_carbon_bar.groupby("Country")["CO2 Emissions"].sum().nsmallest(5).reset_index()
    bottom5_df = data_carbon_bar[data_carbon_bar["Country"].isin(bottom5["Country"])]

    fig_top_5 = px.bar(top5_df, x="Country", y="CO2 Emissions", color="Year",
        barmode="group", title="Top 5 Countries – Carbon Emissions",
        labels={"CO2 Emissions": "CO2 Emissions (MtCO2e)"})
    fig_top_5.update_layout(height=400)

    fig_bottom_5 = px.bar(bottom5_df, x="Country", y="CO2 Emissions", color="Year",
        barmode="group", title="Bottom 5 Countries – Carbon Emissions",
        labels={"CO2 Emissions": "CO2 Emissions (MtCO2e)"})
    fig_bottom_5.update_layout(height=400)

    top5_countries = data_carbon_line.groupby("Country")["CO2 Emissions"].sum().nlargest(5).index
    bot5_countries = data_carbon_line.groupby("Country")["CO2 Emissions"].sum().nsmallest(5).index
    filt_line = data_carbon_line[data_carbon_line["Country"].isin(top5_countries)|
                                  data_carbon_line["Country"].isin(bot5_countries)]
    top_5_fig = px.line(filt_line[filt_line["Country"].isin(top5_countries)],
        x="Year", y="CO2 Emissions", color="Country",
        title="Line Chart – Top 5 Countries CO2 Emissions")
    top_5_fig.update_layout(height=400)
    bottom_5_fig = px.line(filt_line[filt_line["Country"].isin(bot5_countries)],
        x="Year", y="CO2 Emissions", color="Country",
        title="Line Chart – Bottom 5 Countries CO2 Emissions")
    bottom_5_fig.update_layout(height=400)

    # Heatmap CO2
    data_heat_carbon = pd.read_csv(dp("sorted_data_with_lat_lon.csv"))
    data_heat_carbon.columns = [c.strip() for c in data_heat_carbon.columns]
    co2_h = [c for c in data_heat_carbon.columns if "CO2" in c or "Emission" in c][0]
    data_heat_carbon.rename(columns={co2_h: "CO2 Emissions"}, inplace=True)
    lat_c = [c for c in data_heat_carbon.columns if "lat" in c.lower()][0]
    lon_c = [c for c in data_heat_carbon.columns if "lon" in c.lower()][0]
    fig_heat_carbon = px.density_mapbox(data_heat_carbon, lat=lat_c, lon=lon_c,
        z="CO2 Emissions", hover_data=["Country","CO2 Emissions","Year"],
        radius=20, zoom=1, mapbox_style="carto-positron",
        animation_frame="Year", opacity=0.9,
        title="Heatmap – CO2 Emissions by Country",
        color_continuous_scale=px.colors.sequential.Viridis)

    # Choropleth CO2
    data_carbon_choro = data_carbon_scatter.sort_values("Year")
    fig_carbon_choro = px.choropleth(data_carbon_choro, locations="Country",
        locationmode="country names", color="CO2 Emissions",
        animation_frame="Year", range_color=[0, 1000],
        title="Choropleth Map – Average Carbon Emissions by Country")

    # Bar-race frames
    race = data_carbon_scatter[data_carbon_scatter["Year"].between(1990, 2018)]
    df_total = race.groupby(["Country","Year"])["CO2 Emissions"].sum().reset_index()
    top10 = df_total.groupby("Year").apply(lambda x: x.nlargest(10,"CO2 Emissions")).reset_index(drop=True)
    top10["Rank"]  = top10.groupby("Year")["CO2 Emissions"].rank(ascending=False)
    top10["Color"] = pd.factorize(top10["Country"])[0]

    frames = []
    for yr in sorted(top10["Year"].unique()):
        yr_df = top10[top10["Year"] == yr].sort_values("CO2 Emissions", ascending=False)
        frames.append(go.Frame(data=[go.Bar(
            x=yr_df["Country"], y=yr_df["CO2 Emissions"],
            text=yr_df["CO2 Emissions"].apply(lambda v: f"{v:.1f}"),
            textposition="auto", marker_color=yr_df["Color"],
        )], name=str(yr)))

    first_yr = sorted(top10["Year"].unique())[0]
    first_df = top10[top10["Year"] == first_yr].sort_values("CO2 Emissions", ascending=False)
    fig_race = go.Figure(
        data=[go.Bar(x=first_df["Country"], y=first_df["CO2 Emissions"],
                     text=first_df["CO2 Emissions"].apply(lambda v: f"{v:.1f}"),
                     textposition="auto", marker_color=first_df["Color"])],
        layout=go.Layout(title=f"Top 10 Carbon Emitting Countries – {first_yr}",
                         xaxis_title="Country", yaxis_title="CO2 Emissions (MtCO2e)",
                         updatemenus=[dict(type="buttons", showactive=False,
                             buttons=[dict(label="▶ Play", method="animate",
                                          args=[None, {"frame": {"duration": 800,"redraw": True},
                                                       "fromcurrent": True}]),
                                      dict(label="⏸ Pause", method="animate",
                                          args=[[None], {"frame": {"duration": 0,"redraw": False},
                                                          "mode": "immediate"}])])]),
        frames=frames,
    )
    fig_race.update_layout(sliders=[{
        "steps": [{"args": [[f.name], {"frame": {"duration": 0,"redraw": True},
                              "mode": "immediate"}],
                   "label": f.name, "method": "animate"} for f in frames],
        "transition": {"duration": 0}, "x": 0.08, "len": 0.9,
        "currentvalue": {"prefix": "Year: ", "font": {"size": 18}},
    }])

    # Bubble plot
    df_bb = data_carbon_scatter[data_carbon_scatter["Year"].between(1990, 2018)].copy()
    df_total1 = df_bb.groupby(["Country","Year"])["CO2 Emissions"].sum().reset_index()
    region_map = {"United States":"North America","China":"Asia","India":"Asia",
                  "Russia":"Europe","Japan":"Asia","Germany":"Europe",
                  "South Korea":"Asia","Canada":"North America","Brazil":"South America",
                  "European Union (28)":"Europe","Iran":"Middle East",
                  "Saudi Arabia":"Middle East","Indonesia":"Asia"}
    df_total1["Region"] = df_total1["Country"].map(region_map)
    fig_bb = px.scatter(df_total1, x="CO2 Emissions", y="Year", size="CO2 Emissions",
        color="Region", log_x=True, range_x=[100,15000], range_y=[1990,2018],
        hover_name="Country", animation_frame="Year",
        title="CO2 Emissions Bubble Plot by Country and Year")
    co2_ok = True
    print("[CO2] All carbon figures ready.")
except Exception as e:
    print(f"[CO2] Error: {e}")
    co2_ok = False
    fig_top_5 = fig_bottom_5 = top_5_fig = bottom_5_fig = go.Figure()
    fig_heat_carbon = fig_carbon_choro = fig_race = fig_bb = go.Figure()
    frames = []
    top10 = pd.DataFrame()
    data_carbon_scatter = pd.DataFrame({"Country": [], "Year": [], "CO2 Emissions": []})

# ─── 5. EARLY WARNING PANEL ────────────────────────────────────────────────────
print("[EW] Building early warning panel …")
try:
    from early_warning import build_early_warning_panel
    ew_panel = build_early_warning_panel()
    ew_ok = bool(ew_panel)
except Exception as e:
    print(f"[EW] Error: {e}")
    ew_panel = {}
    ew_ok = False

# ─── 6. HERO IMAGE ─────────────────────────────────────────────────────────────
try:
    with open(dp("earth_image1.png"), "rb") as img_file:
        encoded_image = base64.b64encode(img_file.read()).decode()
    img_src = f"data:image/png;base64,{encoded_image}"
except Exception as e:
    print(f"[IMG] {e}")
    img_src = ""

# ─── 7. DASH APP ───────────────────────────────────────────────────────────────
external_stylesheets = [
    "https://fonts.googleapis.com/css2?family=PT+Sans+Narrow:wght@400;700&family=Inter:wght@400;600&display=swap",
    {
        "href": "https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css",
        "rel": "stylesheet",
        "integrity": "sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO",
        "crossorigin": "anonymous",
    },
]

app = Dash(__name__, external_stylesheets=external_stylesheets,
           suppress_callback_exceptions=True)
app.title = "Earth's Climate Analytics"

DROPDOWN_STYLE = {
    "width": "450px", "marginTop": "20px", "marginBottom": "20px",
    "paddingLeft": "20px", "fontSize": "15px",
    "borderColor": "#2A547E", "borderWidth": "2px",
}
CARD_STYLE = {"marginBottom": "10px", "border": "3px solid #2A547E"}

app.layout = html.Div([
    # ── Header ────────────────────────────────────────────────────────────────
    html.Div([
        html.Img(src=img_src, style={"height": "280px", "display": "block", "margin": "auto"}
                 ) if img_src else html.Div(),
        html.H1("🌍 EARTH'S CLIMATE ANALYTICS",
                style={"textAlign": "center", "fontFamily": "PT Sans Narrow",
                       "fontSize": "48px", "marginTop": "10px"}),
        html.H4("Track changes in Earth's temperature · Carbon Emissions · Sea Levels",
                style={"textAlign": "center", "fontFamily": "PT Sans Narrow",
                       "fontSize": "20px", "opacity": "0.85"}),
    ], style={"paddingTop": "15px", "paddingBottom": "15px",
              "backgroundColor": "#0d1b2a", "color": "white",
              "borderRadius": "12px", "boxShadow": "0 4px 12px rgba(0,0,0,0.4)"}),

    # ── Main dropdown ─────────────────────────────────────────────────────────
    dcc.Dropdown(
        id="main-dropdown",
        options=[
            {"label": "🌡️  Temperature",      "value": "temperature"},
            {"label": "🏭  Carbon Emissions",  "value": "carbon"},
            {"label": "🌊  Sea Levels",        "value": "sea"},
            {"label": "🔗  Correlation",       "value": "correlation"},
            {"label": "🚨  Early Warning",     "value": "early_warning"},
            {"label": "📊  Tableau Dashboards", "value": "tableau"},
        ],
        value="",
        placeholder="➡  Select a Visualization Category …",
        style=DROPDOWN_STYLE,
    ),
    html.Div(id="main-output"),

], style={"backgroundColor": "#CDDEEE", "padding": "12px"})


# ─── 8. MAIN CALLBACK ──────────────────────────────────────────────────────────
@app.callback(Output("main-output", "children"), Input("main-dropdown", "value"))
def render_section(value):

    header_style = {"textAlign": "center", "paddingTop": "40px",
                    "fontFamily": "PT Sans Narrow", "display": "block"}
    h1_style     = {"fontSize": "34px", "color": "white"}
    p_style      = {"fontSize": "18px", "color": "white", "marginTop": "0"}
    SECTION_BG   = {"backgroundColor": "#4482C1"}
    BODY_STYLE   = {"margin": "10px", "display": "block"}

    # ── TEMPERATURE ────────────────────────────────────────────────────────────
    if value == "temperature":
        return html.Div([
            html.Div([
                html.H1("🌡️ Temperature Change Visualization", style=h1_style),
                html.P("Global Average Temperature data across countries, cities & continents.",
                       style=p_style),
            ], style=header_style),

            # Calendar heatmap controls
            html.Div([
                html.H2("Monthly Average Temperature Calendar Heatmap",
                        style={"fontFamily": "Helvetica", "textAlign": "center", "marginTop": "20px"}),
                html.Div([
                    html.Label("Select a Country"),
                    dcc.Dropdown(id="temp-country-dd",
                        options=[{"label": c, "value": c} for c in sorted(fig_CC["Country"].unique())],
                        value=fig_CC["Country"].iloc[0], style=DROPDOWN_STYLE),
                    html.Label("Select a City"),
                    dcc.Dropdown(id="temp-city-dd",
                        options=[{"label": c, "value": c} for c in sorted(fig_CC["City"].unique())],
                        value=fig_CC["City"].iloc[0], style=DROPDOWN_STYLE),
                    html.Label("Select a Year"),
                    dcc.Dropdown(id="temp-year-dd",
                        options=[{"label": y, "value": y} for y in range(
                            int(fig_CC["Year"].min()), int(fig_CC["Year"].max())+1)],
                        value=int(fig_CC["Year"].iloc[0]), style=DROPDOWN_STYLE),
                ]),
                dcc.Graph(id="monthly-temperature", style=CARD_STYLE),
            ]),

            html.Div([
                dcc.Graph(id="Choro", figure=fig_choro,
                          style={**CARD_STYLE, "width": "100%", "height": "850px"}),
                html.Div([
                    dcc.Graph(id="timeline", figure=fig_timeline,
                              style={**CARD_STYLE, "width": "49%"}),
                    dcc.Graph(id="Globe",    figure=fig_globe,
                              style={**CARD_STYLE, "width": "49%"}),
                ], style={"display": "flex", "justifyContent": "space-between"}),

                dcc.Graph(id="Heatmap", figure=fig_heat,
                          style={**CARD_STYLE, "width": "100%", "height": "850px"}),

                dcc.Dropdown(id="choro-dropdown",
                    options=[{"label": k, "value": v} for k, v in [
                        ("🇮🇳 INDIA","fig11"),("🇨🇳 CHINA","fig21"),("🇨🇦 CANADA","fig31"),
                        ("🇧🇷 BRAZIL","fig41"),("🇷🇺 RUSSIA","fig51"),("🇺🇸 USA","fig61")]],
                    value="fig11", style=DROPDOWN_STYLE),
                dcc.Graph(id="choropleth-map11", figure=fig11, style=CARD_STYLE),
                dcc.Graph(id="lines",   figure=fig_lines,  style=CARD_STYLE),
                dcc.Graph(id="maxmin",  figure=fig_maxmin, style=CARD_STYLE),
                dcc.Graph(id="diff",    figure=fig_diff,   style=CARD_STYLE),
            ], style=BODY_STYLE),
        ], style=SECTION_BG)

    # ── CARBON EMISSIONS ───────────────────────────────────────────────────────
    elif value == "carbon":
        return html.Div([
            html.Div([
                html.H1("🏭 Carbon Emissions Visualization", style=h1_style),
                html.P("Global CO₂ Emissions data 1990–2018 (MtCO₂e).", style=p_style),
            ], style=header_style),

            html.Div([
                html.Label("Select countries to display:"),
                dcc.Dropdown(id="co2-country-dd",
                    options=[{"label": c, "value": c} for c in data_carbon_scatter["Country"].unique()],
                    value=["United States", "China"], multi=True,
                    style={**DROPDOWN_STYLE, "width": "700px"}),
            ]),
            dcc.Graph(id="carbon-scatter", style=CARD_STYLE),

            html.H2("Top 10 Emitters – Animated Race", style={"color": "white", "padding": "8px"}),
            dcc.Graph(id="carbon-race", figure=fig_race, style=CARD_STYLE),

            html.Div([
                dcc.Graph(id="carbon-top5",    figure=fig_top_5,    style={**CARD_STYLE, "width": "49%"}),
                dcc.Graph(id="carbon-bottom5", figure=fig_bottom_5, style={**CARD_STYLE, "width": "49%"}),
            ], style={"display": "flex", "justifyContent": "space-between"}),
            dcc.Graph(id="carbon-bubble",  figure=fig_bb,          style=CARD_STYLE),
            dcc.Graph(id="carbon-top5-l",  figure=top_5_fig,       style=CARD_STYLE),
            dcc.Graph(id="carbon-bot5-l",  figure=bottom_5_fig,    style=CARD_STYLE),
            dcc.Graph(id="carbon-choro",   figure=fig_carbon_choro,
                      style={**CARD_STYLE, "height": "850px"}),
            dcc.Graph(id="carbon-heat",    figure=fig_heat_carbon,
                      style={**CARD_STYLE, "height": "850px"}),
        ], style=SECTION_BG)

    # ── SEA LEVELS ─────────────────────────────────────────────────────────────
    elif value == "sea":
        return html.Div([
            html.Div([
                html.H1("🌊 Sea Level Change", style=h1_style),
                html.P("Global sea level rise data from tide gauges & satellites.", style=p_style),
            ], style=header_style),
            html.Div([
                dcc.Graph(id="sea-bar",     figure=fig_bar,     style=CARD_STYLE),
                dcc.Graph(id="sea-scatter", figure=scatter_fig, style=CARD_STYLE),
                html.Div([
                    dcc.Graph(id="sea-box",  figure=fig_box,  style={**CARD_STYLE, "width": "49%"}),
                    dcc.Graph(id="sea-area", figure=area_fig, style={**CARD_STYLE, "width": "49%"}),
                ], style={"display": "flex", "justifyContent": "space-between"}),
                dcc.Graph(id="sea-line", figure=fig_line, style=CARD_STYLE),
            ], style=BODY_STYLE),
        ], style=SECTION_BG)

    # ── CORRELATION ────────────────────────────────────────────────────────────
    elif value == "correlation":
        return html.Div([
            html.Div([
                html.H1("🔗 Correlation – Temp · CO₂ · Sea Level", style=h1_style),
                html.P("Combined view of Land Temperature, Carbon Emissions, and Sea Level "
                       "(1990–2020).", style=p_style),
            ], style=header_style),
            html.Div([
                dcc.Graph(id="c-temp-bar",  figure=fig_corr_temp, style=CARD_STYLE),
                dcc.Graph(id="c-corr1",     figure=fig_corr1,     style=CARD_STYLE),
                dcc.Graph(id="c-emit",      figure=fig_emissions,  style=CARD_STYLE),
                dcc.Graph(id="c-corr3",     figure=fig_corr3,      style=CARD_STYLE),
                dcc.Graph(id="c-scatter",   figure=fig_corr2,      style=CARD_STYLE),
            ], style=BODY_STYLE),
        ], style=SECTION_BG)

    # ── EARLY WARNING ─────────────────────────────────────────────────────────
    elif value == "early_warning":
        if not ew_ok or not ew_panel:
            return html.Div(html.P("⚠️ Early Warning data could not be loaded.",
                                   style={"color": "white", "padding": "30px", "fontSize": "20px"}),
                            style=SECTION_BG)

        n_warn      = len(ew_panel.get("warning_years", []))
        n_high_var  = len(ew_panel.get("high_var_years", []))
        total       = ew_panel.get("total_years", "?")
        synth_start = ew_panel.get("synthetic_start", None)
        warn_years_str = ", ".join(str(y) for y in ew_panel.get("warning_years", [])[-10:])
        synth_note = (f" | Synthetic data from {synth_start} onwards (purple dashed line in charts)"
                      if synth_start else "")

        return html.Div([
            html.Div([
                html.H1("🚨 Early Warning System – Climate Acceleration Detection", style=h1_style),
                html.P(
                    f"Analysed {total} years of global temperature data (1750–2025)"
                    f" using moving averages, differential analysis, and rolling variance."
                    f"{synth_note}",
                    style=p_style),
                html.P(f"⚠️  {n_warn} acceleration warning events  |  📊 {n_high_var} high-variance years detected. "
                       f"Most recent accelerations: {warn_years_str}",
                       style={**p_style, "fontWeight": "bold", "color": "#ffeaa7"}),
            ], style=header_style),

            html.Div([
                html.Div([
                    html.H3("🔢 Methodology", style={"color": "white"}),
                    html.Ul([
                        html.Li("📊 Moving Average: 5-year rolling window to smooth annual noise and reveal the underlying trend.",
                                style={"color": "#dfe6e9", "marginBottom": "6px"}),
                        html.Li("📈 First Difference (ΔT): Year-over-year change in moving average — the rate of warming.",
                                style={"color": "#dfe6e9", "marginBottom": "6px"}),
                        html.Li("⚡ Second Difference (Δ²T): Change in the rate — detects acceleration of warming.",
                                style={"color": "#dfe6e9", "marginBottom": "6px"}),
                        html.Li("🚨 Acceleration Warning: Triggered when Δ²T > mean + 1.5σ — statistically anomalous acceleration.",
                                style={"color": "#ffeaa7", "marginBottom": "6px", "fontWeight": "bold"}),
                        html.Li("📊 Rolling Variance (10-year): Measures climate instability — high variance = more erratic swings.",
                                style={"color": "#fdcb6e", "marginBottom": "6px", "fontWeight": "bold"}),
                    ]),
                ], style={"backgroundColor": "#2d3436", "padding": "18px",
                          "borderRadius": "10px", "margin": "10px"}),

                dcc.Graph(id="ew-moving-avg",   figure=ew_panel.get("moving_avg",   go.Figure()), style=CARD_STYLE),
                dcc.Graph(id="ew-first-diff",   figure=ew_panel.get("first_diff",   go.Figure()), style=CARD_STYLE),
                dcc.Graph(id="ew-second-diff",  figure=ew_panel.get("second_diff",  go.Figure()), style=CARD_STYLE),
                dcc.Graph(id="ew-warning",      figure=ew_panel.get("warning",      go.Figure()),
                          style={**CARD_STYLE, "height": "620px"}),
                dcc.Graph(id="ew-rolling-var",  figure=ew_panel.get("rolling_var",  go.Figure()),
                          style={**CARD_STYLE, "height": "500px"}),
            ], style=BODY_STYLE),
        ], style=SECTION_BG)

    # ── TABLEAU DASHBOARDS ─────────────────────────────────────────────────
    elif value == "tableau":
        return build_tableau_section(BASE_DIR)

    return html.Div()


# ─── 9. CALLBACKS ──────────────────────────────────────────────────────────────

# Calendar heatmap
@app.callback(
    Output("temp-city-dd", "options"),
    Input("temp-country-dd", "value"),
    prevent_initial_call=True,
)
def update_city_options(country):
    if not country:
        return []
    cities = fig_CC[fig_CC["Country"] == country]["City"].unique()
    return [{"label": c, "value": c} for c in sorted(cities)]


@app.callback(
    Output("monthly-temperature", "figure"),
    Input("temp-country-dd", "value"),
    Input("temp-city-dd",    "value"),
    Input("temp-year-dd",    "value"),
    prevent_initial_call=True,
)
def update_calendar_heatmap(country, city, year):
    if not country or not city or not year:
        return go.Figure()
    try:
        sub = fig_CC[(fig_CC["Country"] == country) &
                     (fig_CC["City"] == city) &
                     (fig_CC["Year"] == int(year))].copy()
        sub = sub[sub["AvgTemperature"] != -99]
        sub["datetime"] = pd.to_datetime(sub[["Year","Month","Day"]], errors="coerce")
        sub = sub.dropna(subset=["datetime"])
        sub.set_index("datetime", inplace=True)
        fig = go.Figure(data=go.Heatmap(
            z=sub["AvgTemperature"], x=sub.index.day, y=sub.index.month,
            colorscale="Jet",
            colorbar=dict(title="Temp (°C)"),
            hovertemplate="Day: %{x}<br>Month: %{y}<br>Temp: %{z:.2f}°C<extra></extra>",
        ))
        fig.update_layout(
            title=f"Monthly Average Temperature – {city}, {country} ({year})",
            xaxis_title="Day", yaxis_title="Month")
        return fig
    except Exception as e:
        print(f"[CB calendar] {e}")
        return go.Figure()


# Country choropleth selector
@app.callback(
    Output("choropleth-map11", "figure"),
    Input("choro-dropdown", "value"),
    prevent_initial_call=True,
)
def update_country_choro(val):
    mapping = {"fig11": fig11, "fig21": fig21, "fig31": fig31,
               "fig41": fig41, "fig51": fig51, "fig61": fig61}
    return mapping.get(val, go.Figure())


# CO2 scatter
@app.callback(
    Output("carbon-scatter", "figure"),
    Input("co2-country-dd", "value"),
    prevent_initial_call=True,
)
def update_co2_scatter(countries):
    if not countries:
        return go.Figure()
    sub = data_carbon_scatter[data_carbon_scatter["Country"].isin(countries)]
    fig = px.scatter(sub, x="Year", y="CO2 Emissions", color="Country",
                     title="Scatter – CO₂ Emissions by Country",
                     hover_data=["Country"])
    fig.update_layout(xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
    return fig


# ─── 10. ENTRY POINT ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  🌍  Climate Change Dashboard starting …")
    print("  📍  http://127.0.0.1:8050")
    print("="*55 + "\n")
    app.run(debug=False)
