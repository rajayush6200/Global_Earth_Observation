# 🌍 Earth's Climate Analytics: Visualization & Early Warning System

![Python Status](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Dash](https://img.shields.io/badge/Dash-2.x-008de4.svg?logo=plotly)
![Plotly](https://img.shields.io/badge/Plotly-5.x-success.svg?logo=plotly)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-150458.svg?logo=pandas)
![Tableau](https://img.shields.io/badge/Tableau-Integration-E97627.svg?logo=tableau)

A comprehensive, interactive data visualization dashboard built with **Plotly Dash** to explore the profound impacts of climate change on our planet. This standalone application analyzes and visualizes large-scale datasets relating to **Earth's Surface Temperature**, **Carbon Dioxide Emissions**, and **Global Sea Level Rise** from 1750 through to 2025. 

Beyond standard visualizations, this project features an **Early Warning System (Climate Acceleration Detection)** that calculates sophisticated statistical indicators to flag anomalous climate instability and warming acceleration.

---

## 🌟 Key Features

The application is structured into six core interactive modules:

### 1. 🌡️ Temperature Change Visualization
Explore historical and recent temperature trends across countries, continents, and major cities:
*   **Calendar Heatmap:** Monthly average temperatures for individual cities.
*   **Interactive Choropleth Maps:** Temperature variations mapped by country.
*   **3D Globe Representation:** Orthographic projection of global temperature distributions.
*   **Mapbox & Scatter Geo:** Visualizing temperature differences (Max vs. Mean) since 1825.
*   **Time Series Analysis:** Decadal line charts highlighting continental temperature changes.

### 2. 🏭 Carbon Emissions (1990–2018 base, projected to 2025)
*   **Animated Bar Chart Race:** Watch the historical progression of the top 10 emitting nations.
*   **Bubble Plots & Scatter Plots:** Correlation of emissions by region and year.
*   **Global Heatmap & Choropleth:** Geographical distribution of $\text{CO}_2$ footprints.

### 3. 🌊 Sea Level Rise
*   Tracking sea-level variations using tide gauge and satellite data.
*   Includes Box & Whisker plots, Area charts, and trend-line visualizations to map the long-term upward trajectory.

### 4. 🔗 Correlation Analysis
*   **Multi-Axis Time Series:** Joint visualization plotting Land+Ocean Temperature, Carbon Emissions, and Sea Level on concurrent axes to highlight alarming parallel trends.
*   **Stacked Bars & Scatter Diagnostics:** Analyzing the direct relationship between greenhouse gas emissions and surface temperature increases.

### 5. 🚨 Early Warning System (Novelty Feature)
A dedicated statistical module (`early_warning.py`) designed to detect alarming shift-patterns in global temperatures:
*   **Moving Average (5-Year Window):** Smooths annual variability to reveal the underlying macro-trend.
*   **First Difference ($\Delta T$):** Computes the year-over-year rate of climate warming.
*   **Second Difference (Acceleration, $\Delta^2 T$):** Measures the *change in the rate* of warming. Flags "Warning Years" where acceleration exceeds $\mu + 1.5\sigma$.
*   **Rolling Variance (10-Year Window):** Acts as an **Instability Indicator**. High rolling variance points to increasingly erratic year-to-year swings.

### 6. 📊 Tableau Integration (Business Intelligence)
A complete Tableau pipeline that bridges Python analytics with enterprise-grade BI visualization:
*   **Data Export Pipeline (`tableau_export.py`):** Generates 5 Tableau-optimized CSV datasets with enriched fields (rankings, cumulative totals, normalized values, anomalies, decade groupings).
*   **Pre-configured Workbook (`tableau_workbook.twb`):** A Tableau Workbook file with all data sources pre-linked and starter worksheets for immediate use.
*   **Embedded Dashboards:** The Dash app includes an embedded Tableau section with `Iframe` panels for inline Tableau Public visualization.
*   **Dataset Catalog:** Interactive guide within the app listing all exported datasets, key fields, and usage instructions.

---

## 🚀 Synthetic Data Extension (Up to 2025)

To modernize historical datasets that originally ended between 2013–2018, the project includes `generate_synthetic_data.py`. This script produces realistic, scientifically grounded data extensions covering the years 2021–2025:
*   **Temperature:** Extrapolates a $+0.02^\circ\text{C}$/year underlying trend (in line with IPCC AR6) whilst preserving historical seasonal profiles and injecting localized noise. It incorporates real-world temperature anomalies (e.g., the record-breaking warmth of 2023/2024).
*   **Emissions & Sea Level:** Models a slowing emission growth rate post-2023 and an accelerating sea-level rise (~$4.2\text{ mm/yr}$).
*   **Transparency:** All synthetic data rows are strictly tagged with `source = 'synthetic'` allowing the UI to clearly demarcate historical truth from projected estimates.

---

## 🛠️ Architecture & Tech Stack

*   **Frontend / UI:** [Plotly Dash](https://dash.plotly.com/) (Dash Core Components, Dash HTML Components)
*   **Visualizations:** Plotly Express, Plotly Graph Objects
*   **BI Platform:** [Tableau](https://www.tableau.com/) (Tableau Public / Tableau Desktop) – embedded via Iframe + data export pipeline
*   **Data Processing:** Pandas, NumPy
*   **Deployment & Export:** standard Python `app.run()`, Kaleido (for static chart exports)

### Project Structure
```text
Climate-Change-Data-Visualization-and-Analysis/
│
├── app.py                      # Main Plotly Dash application (6 modules incl. Tableau)
├── early_warning.py            # Statistical detection logic and graph components
├── generate_synthetic_data.py  # Data augmentation script (extends limits to 2025)
├── tableau_export.py           # Tableau data export pipeline (generates tableau_data/)
├── tableau_workbook.twb        # Pre-configured Tableau Workbook template
├── requirements.txt            # Python dependencies
├── inspect_data.py / _nb.py    # Utility scripts for data/notebook inspection
│
├── Dataset/                    # Raw & Extended Datasets (CSVs & GeoJSONs)
│   ├── avg_dataset_extended.csv
│   ├── GlobalTemperatures_extended.csv
│   ├── UpdatedMajorCity_temperatures_extended.csv
│   └── ...
│
├── tableau_data/               # Tableau-Optimized Exports (auto-generated)
│   ├── tableau_global_temperatures.csv
│   ├── tableau_carbon_emissions.csv
│   ├── tableau_sea_level.csv
│   ├── tableau_correlation_matrix.csv
│   ├── tableau_country_temperatures.csv
│   └── tableau_summary.csv
│
└── outputs/                    # Exported static analysis images
```

---

## ⚙️ Installation & Usage

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/susovanpatra00/Climate-Change-Data-Visualization-and-Analysis.git
    cd Climate-Change-Data-Visualization-and-Analysis
    ```

2.  **Install Requirements**
    Ensure you have Python 3.8+ installed. It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Generate Extended Datasets (Optional but Recommended)**
    If deploying for the first time, run the generator script to create the `*_extended.csv` files up to the year 2025.
    ```bash
    python generate_synthetic_data.py
    ```

4.  **Run the Dashboard**
    ```bash
    python app.py
    ```
    Open your browser and navigate to `http://127.0.0.1:8050` to view the interactive dashboard.

5.  **Export Data for Tableau (Optional)**
    Generate Tableau-optimized datasets for use in Tableau Desktop or Tableau Public.
    ```bash
    python tableau_export.py
    ```
    This creates a `tableau_data/` folder with 5 enriched CSVs. Open `tableau_workbook.twb` in Tableau to get started.

---

## 📊 Tableau Integration

This project includes full Tableau support for enterprise-grade visual analytics:

### Quick Start
1.  Run the export pipeline:
    ```bash
    python tableau_export.py
    ```
2.  Open `tableau_workbook.twb` in **Tableau Public** (free) or **Tableau Desktop**.
3.  The workbook comes with 5 pre-configured data sources and starter worksheets.
4.  Build dashboards, then publish to [Tableau Public](https://public.tableau.com/).
5.  (Optional) Paste your Tableau Public embed URLs into `app.py` to display inline in the Dash app.

### Exported Datasets
| Dataset | Description | Key Fields |
|---------|-------------|------------|
| `tableau_global_temperatures.csv` | Yearly global temperatures | Year, Temp, Moving Avg, ΔT, Δ²T, Warning Flags |
| `tableau_carbon_emissions.csv` | Country CO₂ emissions | Country, Year, CO₂, Region, Rank, Cumulative |
| `tableau_sea_level.csv` | Sea level rise | Year, Sea Level, Trend, Rate |
| `tableau_correlation_matrix.csv` | Combined climate metrics | Year, Temp, CO₂, Sea Level, Normalized |
| `tableau_country_temperatures.csv` | Country-level temps | Country, Year, Temp, Continent, Anomaly |

---

## 📈 Visual Showcase

### 1. The Early Warning System
Detecting acceleration and variance in the global climate signal.
![Early Warning Output](https://user-images.githubusercontent.com/100257642/234190921-b12c524a-8b37-45ad-924c-e12df7c7de6a.png)
*(Note: Interface has evolved since initial release to include new ML/Statistical indicators as detailed above).*

### 2. Global Temperature Distribution (3D Globe)
<img width="800" alt="Globe_3d" src="https://user-images.githubusercontent.com/100257642/234192561-2d3ac8ee-4698-4121-bc3c-7fe117971446.png">

### 3. Global Sea Level Rise (Box plots & Line charts)
<img width="800" alt="SeaLevel_Box1" src="https://user-images.githubusercontent.com/100257642/234193003-0d482a05-1216-4754-8280-d14fe40c9334.png">

### 4. Correlation Analysis
Multiplexed views correlating carbon footprint to land/ocean heat metrics.
<img width="800" alt="corr3" src="https://user-images.githubusercontent.com/100257642/234193512-aa1b3ddc-22c0-4a30-a9fb-6c6e99cafc25.png">

---

## 🤝 Contributors
*   **Ayush Raj**
*   **Mohole Saukhyad Bhupendra**
*   **Ishika Bharti**
*   **Chittibotula Niharika**

*With recent maintenance, modernization (Dash v2 structure), and statistical intelligence (Early Warning extensions). *
