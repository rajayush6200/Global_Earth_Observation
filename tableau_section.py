"""
Professional Tableau integration UI for the Dash app: embedded Public views,
capability mapping, export catalog, and workbook workflow.
"""
import os
from typing import Optional

import pandas as pd
from dash import dcc, html


def _read_summary(base_dir: str) -> Optional[pd.DataFrame]:
    path = os.path.join(base_dir, "tableau_data", "tableau_summary.csv")
    if not os.path.exists(path):
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def build_tableau_section(base_dir: str) -> html.Div:
    h1_style = {
        "fontSize": "34px",
        "color": "white",
        "fontFamily": "PT Sans Narrow, sans-serif",
        "fontWeight": "600",
        "marginBottom": "8px",
    }
    p_style = {
        "fontSize": "17px",
        "color": "#dfe6e9",
        "marginTop": "0",
        "lineHeight": "1.5",
    }
    header_style = {
        "textAlign": "center",
        "paddingTop": "28px",
        "paddingBottom": "12px",
        "fontFamily": "Inter, sans-serif",
        "display": "block",
        "borderBottom": "3px solid #E97627",
        "marginBottom": "20px",
    }
    body = {
        "margin": "10px",
        "display": "block",
        "maxWidth": "1400px",
        "marginLeft": "auto",
        "marginRight": "auto",
    }
    bg = {"backgroundColor": "#0f1419", "minHeight": "100vh"}
    card = {
        "backgroundColor": "#1b2838",
        "borderRadius": "10px",
        "padding": "22px",
        "marginBottom": "16px",
        "border": "1px solid #2c3e50",
        "boxShadow": "0 8px 32px rgba(0,0,0,0.35)",
    }
    frame = {
        "width": "100%",
        "height": "600px",
        "border": "none",
        "borderRadius": "6px",
        "backgroundColor": "#0d1117",
    }
    orange = "#E97627"
    muted = "#8b9aab"

    q = ":showVizHome=no&:embed=y&:toolbar=yes&:origin=viz_share_link"
    embed_co2 = f"https://public.tableau.com/views/CountriesCO2emissionspercapita_16421584351800/Dashboard1?{q}"
    embed_super = f"https://public.tableau.com/views/Superstore_24/Overview?{q}"
    embed_climate = f"https://public.tableau.com/views/ClimateChange-BigQuestions/Allhistory?{q}"

    tdir = os.path.join(base_dir, "tableau_data")
    ready = os.path.exists(tdir) and any(f.endswith(".csv") for f in os.listdir(tdir))
    status_color = "#00b894" if ready else "#fdcb6e"
    status_txt = (
        "Extracts ready for Tableau Desktop, Public, and Web Authoring."
        if ready
        else "Run  python tableau_export.py  to generate Tableau-optimized CSV extracts."
    )

    file_rows = []
    if ready:
        for fn in sorted(os.listdir(tdir)):
            if fn.endswith(".csv"):
                fp = os.path.join(tdir, fn)
                kb = os.path.getsize(fp) / 1024
                file_rows.append(
                    html.Tr(
                        [
                            html.Td(
                                fn,
                                style={
                                    "color": "#dfe6e9",
                                    "padding": "10px 12px",
                                    "fontFamily": "ui-monospace, Consolas, monospace",
                                    "fontSize": "13px",
                                    "borderBottom": "1px solid #2c3e50",
                                },
                            ),
                            html.Td(
                                f"{kb:.1f} KB",
                                style={
                                    "color": muted,
                                    "padding": "10px 12px",
                                    "borderBottom": "1px solid #2c3e50",
                                    "textAlign": "right",
                                },
                            ),
                        ]
                    )
                )

    summary_df = _read_summary(base_dir)
    th_style = {
        "color": orange,
        "padding": "12px 10px",
        "textAlign": "left",
        "borderBottom": f"2px solid {orange}",
        "fontSize": "12px",
        "textTransform": "uppercase",
        "letterSpacing": "0.06em",
    }
    catalog_rows = []
    if summary_df is not None and len(summary_df) > 0:
        for _, row in summary_df.iterrows():
            cols = str(row.get("Column_Names", ""))
            catalog_rows.append(
                html.Tr(
                    [
                        html.Td(
                            str(row.get("Dataset", "")),
                            style={
                                "color": "#dfe6e9",
                                "padding": "10px",
                                "verticalAlign": "top",
                                "borderBottom": "1px solid #2c3e50",
                                "fontWeight": "600",
                            },
                        ),
                        html.Td(
                            str(row.get("Description", "")),
                            style={
                                "color": muted,
                                "padding": "10px",
                                "fontSize": "13px",
                                "borderBottom": "1px solid #2c3e50",
                                "maxWidth": "320px",
                            },
                        ),
                        html.Td(
                            f"{int(row.get('Rows', 0)):,} × {int(row.get('Columns', 0))}",
                            style={
                                "color": orange,
                                "padding": "10px",
                                "whiteSpace": "nowrap",
                                "borderBottom": "1px solid #2c3e50",
                                "fontFamily": "monospace",
                            },
                        ),
                        html.Td(
                            (cols[:140] + "…") if len(cols) > 140 else cols,
                            style={
                                "color": "#5c6b7a",
                                "padding": "10px",
                                "fontSize": "11px",
                                "borderBottom": "1px solid #2c3e50",
                                "fontFamily": "monospace",
                            },
                        ),
                    ]
                )
            )

    def cap(title, text, tag):
        return html.Div(
            [
                html.Span(
                    tag,
                    style={
                        "fontSize": "10px",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.08em",
                        "color": orange,
                        "fontWeight": "700",
                    },
                ),
                html.H4(title, style={"color": "white", "margin": "8px 0 6px", "fontSize": "16px"}),
                html.P(text, style={"color": muted, "fontSize": "13px", "lineHeight": "1.45", "margin": 0}),
            ],
            style={
                "backgroundColor": "#131c26",
                "borderRadius": "8px",
                "padding": "16px",
                "border": "1px solid #2c3e50",
                "flex": "1 1 260px",
                "minWidth": "240px",
            },
        )

    def embed_card(title, subtitle, src, note, accent):
        return html.Div(
            [
                html.H3(title, style={"color": accent, "marginBottom": "6px", "fontSize": "18px"}),
                html.P(subtitle, style={"color": muted, "fontSize": "13px", "marginBottom": "12px"}),
                html.Iframe(src=src, style=frame, title=title),
                html.P(note, style={"color": "#5c6b7a", "fontSize": "11px", "marginTop": "10px", "fontStyle": "italic"}),
            ],
            style=card,
        )

    caps = html.Div(
        [
            cap(
                "Parameters & dashboard actions",
                "Use parameters for Year or Region; add filter actions across sheets so a decade "
                "selection on temperature drives CO₂ and sea-level views.",
                "Interactivity",
            ),
            cap(
                "Sets, groups & highlighting",
                "Build sets from Accel_Warning or High_Variance_Flag; apply to colour, reference "
                "bands, and set actions for executive dashboards.",
                "Modeling",
            ),
            cap(
                "Calculated fields & table calculations",
                "Pipeline fields include deltas and YoY metrics — extend with RUNNING_SUM, "
                "WINDOW_AVG, and rank table calcs for rankings over time.",
                "Analytics",
            ),
            cap(
                "LOD expressions",
                "FIXED [Country] baselines; INCLUDE/EXCLUDE for regional rollups on emissions "
                "and country temperature extracts.",
                "LOD",
            ),
            cap(
                "Stories & device layouts",
                "Publish Stories for narrative briefings; use phone/tablet layouts for field "
                "monitoring of warning-year indicators.",
                "Presentation",
            ),
            cap(
                "Maps, dual axis & blending",
                "Dual-axis time series from correlation extract; maps coloured by Temp_Anomaly or "
                "Global_Share_Pct with optional spatial joins.",
                "Geospatial",
            ),
        ],
        style={"display": "flex", "flexWrap": "wrap", "gap": "14px", "marginBottom": "20px"},
    )

    tab_embed = html.Div(
        [
            html.P(
                "Live Tableau Public workbooks below show native features: filters, highlights, "
                "tooltips, and toolbar actions. Connect tableau_workbook.twb to the exported CSVs "
                "to mirror these patterns on your climate data.",
                style={"color": muted, "fontSize": "14px", "marginBottom": "18px", "lineHeight": "1.5"},
            ),
            html.Div(
                [
                    embed_card(
                        "CO₂ — Tableau Public",
                        "National and per-capita emissions — template for maps, BANs, and bar races.",
                        embed_co2,
                        "Gallery viz; requires network. If blocked, open the same URL on tableau.com.",
                        "#74b9ff",
                    ),
                    embed_card(
                        "Climate Q&A — Tableau Public",
                        "Story-style climate overview — cross-check narratives against our correlation extract.",
                        embed_climate,
                        "Some networks block embedded Public; use Open in new tab if the frame is empty.",
                        "#55efc4",
                    ),
                ],
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(480px, 1fr))", "gap": "16px"},
            ),
            html.Div(
                [
                    embed_card(
                        "Superstore — UX reference",
                        "Shows quick filters, cross-highlighting, and polished dashboard chrome.",
                        embed_super,
                        "Apply the same interaction design to tableau_global_temperatures and correlation data.",
                        "#a29bfe",
                    ),
                    html.Div(
                        [
                            html.H3("Your dashboards", style={"color": orange, "fontSize": "18px"}),
                            html.P(
                                "Publish to Tableau Public, copy the embed link, and set the iframe src "
                                "in tableau_section.build_tableau_section (or add a small config dict).",
                                style={"color": muted, "fontSize": "13px", "lineHeight": "1.5"},
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        html.A(
                                            "Viz of the Day — Tableau Public",
                                            href="https://public.tableau.com/app/discover/viz-of-the-day",
                                            target="_blank",
                                            rel="noopener noreferrer",
                                            style={"color": "#74b9ff"},
                                        )
                                    ),
                                    html.Li(
                                        html.A(
                                            "Embed views — Tableau Help",
                                            href="https://help.tableau.com/current/pro/desktop/en-us/embed_list.htm",
                                            target="_blank",
                                            rel="noopener noreferrer",
                                            style={"color": "#74b9ff"},
                                        )
                                    ),
                                    html.Li(
                                        html.A(
                                            "Parameters — Tableau Help",
                                            href="https://help.tableau.com/current/pro/desktop/en-us/parameters_create.htm",
                                            target="_blank",
                                            rel="noopener noreferrer",
                                            style={"color": "#74b9ff"},
                                        )
                                    ),
                                ],
                                style={"color": muted, "fontSize": "13px"},
                            ),
                        ],
                        style={**card, "minHeight": "200px"},
                    ),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(auto-fit, minmax(480px, 1fr))",
                    "gap": "16px",
                    "marginTop": "16px",
                },
            ),
        ]
    )

    catalog_body = (
        html.Tbody(catalog_rows)
        if catalog_rows
        else html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(
                            "Run tableau_export.py to populate tableau_summary.csv.",
                            colSpan=4,
                            style={"color": muted, "padding": "16px"},
                        ),
                    ]
                )
            ]
        )
    )

    tab_features = html.Div(
        [
            html.H2(
                "Tableau capabilities mapped to this project",
                style={"color": "white", "fontSize": "22px", "marginBottom": "8px"},
            ),
            html.P(
                "How Desktop / Public features apply to the CSVs produced by tableau_export.py.",
                style={"color": muted, "fontSize": "14px", "marginBottom": "18px"},
            ),
            caps,
            html.H2(
                "Export catalog (tableau_summary.csv)",
                style={"color": "white", "fontSize": "20px", "marginTop": "24px", "marginBottom": "10px"},
            ),
            html.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th("Dataset", style=th_style),
                                html.Th("Description", style=th_style),
                                html.Th("Shape", style=th_style),
                                html.Th("Fields (preview)", style=th_style),
                            ]
                        )
                    ),
                    catalog_body,
                ],
                style={"width": "100%", "borderCollapse": "collapse", "fontSize": "13px"},
            ),
        ]
    )

    step = {"backgroundColor": "#131c26", "borderRadius": "8px", "padding": "16px", "marginBottom": "10px", "border": "1px solid #2c3e50"}
    badge = {
        "display": "inline-block",
        "backgroundColor": orange,
        "color": "white",
        "borderRadius": "50%",
        "width": "28px",
        "height": "28px",
        "textAlign": "center",
        "lineHeight": "28px",
        "fontWeight": "bold",
        "marginRight": "10px",
        "fontSize": "14px",
    }

    tab_workflow = html.Div(
        [
            html.H2("Implementation workflow", style={"color": "white", "fontSize": "20px", "marginBottom": "14px"}),
            html.Div(
                [
                    html.Span("1", style=badge),
                    html.Span("Export", style={"color": "white", "fontWeight": "bold"}),
                    html.Pre(
                        "python tableau_export.py",
                        style={
                            "backgroundColor": "#0d1117",
                            "color": "#00b894",
                            "padding": "10px",
                            "borderRadius": "6px",
                            "marginTop": "8px",
                            "fontFamily": "Consolas, monospace",
                            "fontSize": "14px",
                        },
                    ),
                ],
                style=step,
            ),
            html.Div(
                [
                    html.Span("2", style=badge),
                    html.Span("Open workbook", style={"color": "white", "fontWeight": "bold"}),
                    html.P(
                        "Open tableau_workbook.twb in Tableau Desktop or Tableau Public. Data sources "
                        "point at tableau_data/*.csv — refresh extracts after each export.",
                        style={"color": "#dfe6e9", "marginTop": "8px", "fontSize": "13px"},
                    ),
                ],
                style=step,
            ),
            html.Div(
                [
                    html.Span("3", style=badge),
                    html.Span("Publish & embed", style={"color": "white", "fontWeight": "bold"}),
                    html.P(
                        "Publish dashboards to Tableau Public and paste embed URLs into custom iframes "
                        "or extend this module with a CONFIG dict.",
                        style={"color": "#dfe6e9", "marginTop": "8px", "fontSize": "13px"},
                    ),
                ],
                style=step,
            ),
            html.H3("Files in tableau_data/", style={"color": "white", "marginTop": "22px", "fontSize": "16px"}),
            html.Table(
                [html.Thead(html.Tr([html.Th("File", style=th_style), html.Th("Size", style=th_style)]))]
                + [html.Tbody(file_rows if file_rows else [html.Tr([html.Td("No CSVs yet.", colSpan=2, style={"color": muted, "padding": "12px"})])])],
                style={"width": "100%", "borderCollapse": "collapse", "marginTop": "8px"},
            ),
        ]
    )

    tabs = dcc.Tabs(
        id="tableau-subtabs",
        value="tab-embed",
        persistence=True,
        persistence_type="session",
        children=[
            dcc.Tab(
                label="Embedded analytics",
                value="tab-embed",
                children=html.Div(tab_embed, style={"paddingTop": "16px"}),
                style={"padding": "10px 16px", "fontWeight": "600"},
                selected_style={"padding": "10px 16px", "fontWeight": "700", "borderTop": f"3px solid {orange}"},
            ),
            dcc.Tab(
                label="Features & catalog",
                value="tab-feat",
                children=html.Div(tab_features, style={"paddingTop": "16px"}),
                style={"padding": "10px 16px", "fontWeight": "600"},
                selected_style={"padding": "10px 16px", "fontWeight": "700", "borderTop": f"3px solid {orange}"},
            ),
            dcc.Tab(
                label="Workbook workflow",
                value="tab-flow",
                children=html.Div(tab_workflow, style={"paddingTop": "16px"}),
                style={"padding": "10px 16px", "fontWeight": "600"},
                selected_style={"padding": "10px 16px", "fontWeight": "700", "borderTop": f"3px solid {orange}"},
            ),
        ],
        colors={"border": "#2c3e50", "primary": orange, "background": "#1b2838"},
        style={"marginTop": "8px"},
        content_style={"backgroundColor": "#0f1419", "padding": "4px 0 20px", "borderRadius": "0 0 8px 8px"},
    )

    return html.Div(
        [
            html.Div(
                [
                    html.H1("Tableau analytics suite", style=h1_style),
                    html.P(
                        "Enterprise-style BI alongside Plotly: curated embeds, export catalog, and "
                        "a guided map of Tableau features on your climate extracts.",
                        style=p_style,
                    ),
                ],
                style=header_style,
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                "STATUS ",
                                style={
                                    "color": status_color,
                                    "fontSize": "11px",
                                    "marginRight": "8px",
                                    "fontWeight": "800",
                                    "letterSpacing": "0.12em",
                                },
                            ),
                            html.Span(status_txt, style={"fontSize": "16px", "color": "white"}),
                        ],
                        style={
                            "backgroundColor": "#131c26",
                            "borderRadius": "8px",
                            "padding": "16px 20px",
                            "marginBottom": "18px",
                            "borderLeft": f"4px solid {status_color}",
                            "border": "1px solid #2c3e50",
                        },
                    ),
                    tabs,
                ],
                style=body,
            ),
        ],
        style=bg,
    )
