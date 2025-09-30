import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from google.oauth2 import service_account
from google.cloud import bigquery
from io import BytesIO
from datetime import date

# ======================================================
# Page config
# ======================================================
st.set_page_config(page_title="Global Development Dashboard", page_icon="🌍", layout="wide")

# ======================================================
# BigQuery auth
# ======================================================
credentials_dict = st.secrets["gcp_service_account"]
credentials = service_account.Credentials.from_service_account_info(dict(credentials_dict))
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

# ======================================================
# Query
# ======================================================
QUERY = """
SELECT
  country_name,
  country_code,
  year,
  MAX(CASE WHEN indicator_name = 'GDP per capita (current US$)' THEN value END) AS gdp_per_capita_usd,
  MAX(CASE WHEN indicator_name = 'Population, total' THEN value END) AS population_total,
  MAX(CASE WHEN indicator_name = 'CO2 emissions (metric tons per capita)' THEN value END) AS co2_emissions_tons_per_capita,
  MAX(CASE WHEN indicator_name = 'Life expectancy at birth, total (years)' THEN value END) AS life_expectancy_years,
  MAX(CASE WHEN indicator_name = 'School enrollment, primary (% gross)' THEN value END) AS primary_school_enrollment_percent,
  MAX(CASE WHEN indicator_name = 'Urban population (% of total population)' THEN value END) AS urban_population_percent
FROM `bigquery-public-data.world_bank_wdi.indicators_data`
WHERE
  country_name IN (
    'United States', 'China', 'India', 'Brazil', 'Germany',
    'Japan', 'United Kingdom', 'Nigeria', 'South Africa', 'Canada'
  )
  AND year BETWEEN 2000 AND 2020
  AND indicator_name IN (
    'GDP per capita (current US$)',
    'Population, total',
    'CO2 emissions (metric tons per capita)',
    'Life expectancy at birth, total (years)',
    'School enrollment, primary (% gross)',
    'Urban population (% of total population)'
  )
GROUP BY country_name, country_code, year
HAVING
  gdp_per_capita_usd IS NOT NULL
  OR population_total IS NOT NULL
  OR co2_emissions_tons_per_capita IS NOT NULL
  OR life_expectancy_years IS NOT NULL
  OR primary_school_enrollment_percent IS NOT NULL
  OR urban_population_percent IS NOT NULL
ORDER BY country_name, year
"""

@st.cache_data
def get_data() -> pd.DataFrame:
    return client.query(QUERY).to_dataframe()

df = get_data()
df["total_co2_emissions_tons"] = df["co2_emissions_tons_per_capita"] * df["population_total"]

# ======================================================
# Filters
# ======================================================
st.title("🌍 Global Development Indicators Dashboard")
st.markdown("Executive overview and deep-dive analytics across economic, social, and environmental indicators.")

flt1, flt2 = st.columns([2, 2])

with flt1:
    all_countries = df["country_name"].unique().tolist()
    selected_countries = st.multiselect(
        "Countries",
        options=all_countries,
        default=all_countries
    )

with flt2:
    year_min, year_max = int(df["year"].min()), int(df["year"].max())
    default_start = date(2010, 1, 1)
    default_end = date(2015, 12, 31)
    date_range = st.date_input(
        "Select Year Range",
        value=(default_start, default_end),
        min_value=date(year_min, 1, 1),
        max_value=date(year_max, 12, 31)
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_year = date_range[0].year
        end_year = date_range[1].year
    else:
        start_year = date_range.year
        end_year = date_range.year

df_filtered = df[
    df["country_name"].isin(selected_countries) &
    df["year"].between(start_year, end_year)
].copy()

if df_filtered.empty:
    st.warning("No data matches the current filters.")
    st.stop()

# ======================================================
# Helpers
# ======================================================
def safe_cagr(v0, v1, periods):
    if periods is None or periods <= 0:
        return np.nan
    if pd.isna(v0) or pd.isna(v1) or v0 <= 0 or v1 <= 0:
        return np.nan
    try:
        return (v1 / v0) ** (1 / periods) - 1
    except Exception:
        return np.nan

def fmt_pct(x, decimals=1):
    return "NA" if pd.isna(x) else f"{x*100:.{decimals}f}%"

def fmt_num(x, decimals=0):
    return "NA" if pd.isna(x) else f"{x:,.{decimals}f}"

def latest_snapshot_with_data(df_sel: pd.DataFrame, value_col: str):
    tmp = df_sel.dropna(subset=[value_col])
    if tmp.empty:
        return None, pd.DataFrame(columns=df_sel.columns)
    y = int(tmp["year"].max())
    return y, tmp[tmp["year"] == y].copy()

def coverage_label(snap: pd.DataFrame, total_selected: int):
    have = snap["country_name"].nunique()
    cov = (have / total_selected) if total_selected else 0.0
    return have, total_selected, cov

COVERAGE_THRESHOLD = 0.7

# Growth frames using first and last non-null per country
sorted_df = df_filtered.sort_values(["country_name", "year"])
first_rows = sorted_df.dropna(subset=["gdp_per_capita_usd","population_total",
                                      "co2_emissions_tons_per_capita","life_expectancy_years",
                                      "urban_population_percent","primary_school_enrollment_percent"])\
                      .groupby("country_name", as_index=False).first()
last_rows = sorted_df.dropna(subset=["gdp_per_capita_usd","population_total",
                                     "co2_emissions_tons_per_capita","life_expectancy_years",
                                     "urban_population_percent","primary_school_enrollment_percent"])\
                     .groupby("country_name", as_index=False).last()

growth = pd.merge(first_rows[["country_name","year","gdp_per_capita_usd","population_total",
                              "co2_emissions_tons_per_capita","life_expectancy_years",
                              "urban_population_percent","primary_school_enrollment_percent"]],
                  last_rows[["country_name","year","gdp_per_capita_usd","population_total",
                             "co2_emissions_tons_per_capita","life_expectancy_years",
                             "urban_population_percent","primary_school_enrollment_percent"]],
                  on="country_name", suffixes=("_start","_end"), how="inner")
growth["periods"] = growth["year_end"] - growth["year_start"]
growth["gdp_cagr"] = [safe_cagr(v0, v1, p) for v0, v1, p in zip(growth["gdp_per_capita_usd_start"],
                                                                 growth["gdp_per_capita_usd_end"],
                                                                 growth["periods"])]
growth["pop_cagr"] = [safe_cagr(v0, v1, p) for v0, v1, p in zip(growth["population_total_start"],
                                                                 growth["population_total_end"],
                                                                 growth["periods"])]
growth["co2pc_cagr"] = [safe_cagr(v0, v1, p) for v0, v1, p in zip(growth["co2_emissions_tons_per_capita_start"],
                                                                   growth["co2_emissions_tons_per_capita_end"],
                                                                   growth["periods"])]
growth["life_change"] = growth["life_expectancy_years_end"] - growth["life_expectancy_years_start"]
growth["urban_change_pp"] = growth["urban_population_percent_end"] - growth["urban_population_percent_start"]
growth["enrol_change_pp"] = growth["primary_school_enrollment_percent_end"] - growth["primary_school_enrollment_percent_start"]
growth["co2pc_change"] = growth["co2_emissions_tons_per_capita_end"] - growth["co2_emissions_tons_per_capita_start"]

# Indicator snapshots with coverage
yr_gdp, snap_gdp = latest_snapshot_with_data(df_filtered, "gdp_per_capita_usd")
yr_life, snap_life = latest_snapshot_with_data(df_filtered, "life_expectancy_years")
yr_co2pc, snap_co2pc = latest_snapshot_with_data(df_filtered, "co2_emissions_tons_per_capita")

g_have, g_total, g_cov = coverage_label(snap_gdp, len(selected_countries))
l_have, l_total, l_cov = coverage_label(snap_life, len(selected_countries))
c_have, c_total, c_cov = coverage_label(snap_co2pc, len(selected_countries))

# Latest-year frame for totals across all indicators still needed
latest_year = int(df_filtered["year"].max())
latest_data = df_filtered[df_filtered["year"] == latest_year]

# ======================================================
# Executive score cards
# ======================================================
st.subheader("Executive score cards")

r1c1, r1c2, r1c3, r1c4 = st.columns(4)
with r1c1:
    st.metric("Countries selected", f"{len(selected_countries)}")

with r1c2:
    if yr_gdp is not None and g_cov >= COVERAGE_THRESHOLD:
        st.metric("Average GDP per capita USD",
                  fmt_num(snap_gdp["gdp_per_capita_usd"].mean()),
                  help=f"Snapshot {yr_gdp} • {g_have}/{g_total} countries")
    else:
        st.metric("Average GDP per capita USD", "NA",
                  help=f"Insufficient coverage • {g_have}/{g_total}")

with r1c3:
    if yr_life is not None and l_cov >= COVERAGE_THRESHOLD:
        st.metric("Average life expectancy years",
                  fmt_num(snap_life["life_expectancy_years"].mean(), 1),
                  help=f"Snapshot {yr_life} • {l_have}/{l_total}")
    else:
        st.metric("Average life expectancy years", "NA",
                  help=f"Insufficient coverage • {l_have}/{l_total}")

with r1c4:
    if yr_co2pc is not None and c_cov >= COVERAGE_THRESHOLD:
        st.metric("Average CO₂ tons per capita",
                  fmt_num(snap_co2pc["co2_emissions_tons_per_capita"].mean(), 2),
                  help=f"Snapshot {yr_co2pc} • {c_have}/{c_total}")
    else:
        st.metric("Average CO₂ tons per capita", "NA",
                  help=f"Insufficient coverage • {c_have}/{c_total}")

r2c1, r2c2, r2c3, r2c4 = st.columns(4)
with r2c1:
    gdp_gap = (snap_gdp["gdp_per_capita_usd"].max() - snap_gdp["gdp_per_capita_usd"].min()) if len(snap_gdp) > 1 else np.nan
    st.metric("GDP per capita gap", fmt_num(gdp_gap),
              help=f"Snapshot {yr_gdp}" if yr_gdp else "NA")

with r2c2:
    life_gap = (snap_life["life_expectancy_years"].max() - snap_life["life_expectancy_years"].min()) if len(snap_life) > 1 else np.nan
    st.metric("Life expectancy gap", fmt_num(life_gap, 1),
              help=f"Snapshot {yr_life}" if yr_life else "NA")

with r2c3:
    total_co2_latest = latest_data["total_co2_emissions_tons"].sum(min_count=1)
    st.metric("Total CO₂ emissions tons", fmt_num(total_co2_latest))

with r2c4:
    st.metric("Median GDP per capita CAGR", fmt_pct(growth["gdp_cagr"].median(), 2))

r3c1, r3c2, r3c3, r3c4 = st.columns(4)
with r3c1:
    tmp = growth.dropna(subset=["gdp_cagr"]).sort_values("gdp_cagr", ascending=False)
    if not tmp.empty:
        row = tmp.iloc[0]
        st.metric("Fastest GDP per capita growth", fmt_pct(row["gdp_cagr"], 2),
                  help=f"{int(row['year_start'])}–{int(row['year_end'])} • {row['country_name']}")
    else:
        st.metric("Fastest GDP per capita growth", "NA", help="No valid period")

with r3c2:
    tmp = growth.dropna(subset=["life_change"]).sort_values("life_change", ascending=False)
    if not tmp.empty:
        row = tmp.iloc[0]
        st.metric("Largest life expectancy gain", fmt_num(row["life_change"], 1),
                  help=f"{int(row['year_start'])}–{int(row['year_end'])} • {row['country_name']}")
    else:
        st.metric("Largest life expectancy gain", "NA")

with r3c3:
    tmp = growth.dropna(subset=["co2pc_change"]).sort_values("co2pc_change", ascending=True)
    if not tmp.empty:
        row = tmp.iloc[0]
        st.metric("Largest CO₂ per capita reduction", fmt_num(-row["co2pc_change"], 2),
                  help=f"{int(row['year_start'])}–{int(row['year_end'])} • {row['country_name']}")
    else:
        st.metric("Largest CO₂ per capita reduction", "NA")

with r3c4:
    if yr_co2pc is not None and not snap_co2pc.empty:
        low = snap_co2pc.dropna(subset=["co2_emissions_tons_per_capita"]).sort_values("co2_emissions_tons_per_capita").head(1)
        if not low.empty:
            st.metric("Lowest CO₂ per capita", fmt_num(low.iloc[0]["co2_emissions_tons_per_capita"], 2),
                      help=f"{yr_co2pc} • {low.iloc[0]['country_name']}")
        else:
            st.metric("Lowest CO₂ per capita", "NA")
    else:
        st.metric("Lowest CO₂ per capita", "NA")

# ======================================================
# Tabs (Summary moved to last and renamed)
# ======================================================
tab_econ, tab_social, tab_env, tab_comp, tab_summary = st.tabs(
    ["Economic", "Social", "Environmental", "Comparison", "Automated Summaries"]
)

# Economic
with tab_econ:
    st.caption("Economic indicators")
    c1, c2 = st.columns(2)

    fig_gdp_line = px.line(
        df_filtered, x="year", y="gdp_per_capita_usd", color="country_name",
        markers=True, title="GDP per capita over time",
        labels={"year": "Year", "gdp_per_capita_usd": "USD", "country_name": "Country"}
    )
    c1.plotly_chart(fig_gdp_line, use_container_width=True)

    if not snap_gdp.empty:
        gdp_sorted = snap_gdp.sort_values("gdp_per_capita_usd", ascending=False)
        fig_gdp_bar = px.bar(
            gdp_sorted, x="country_name", y="gdp_per_capita_usd", color="country_name",
            title=f"GDP per capita in {yr_gdp}",
            labels={"country_name": "Country", "gdp_per_capita_usd": "USD"}
        )
        fig_gdp_bar.update_layout(showlegend=False)
        fig_gdp_bar.update_xaxes(tickangle=-30)
        c2.plotly_chart(fig_gdp_bar, use_container_width=True)
    else:
        c2.info("No GDP snapshot available in the selected window.")

# Social
with tab_social:
    st.caption("Social and demographic indicators")
    r1, r2 = st.columns(2)

    fig_life = px.line(
        df_filtered, x="year", y="life_expectancy_years", color="country_name",
        markers=True, title="Life expectancy over time",
        labels={"life_expectancy_years": "Years", "country_name": "Country"}
    )
    r1.plotly_chart(fig_life, use_container_width=True)

    fig_school = px.line(
        df_filtered, x="year", y="primary_school_enrollment_percent", color="country_name",
        markers=True, title="Primary school enrollment percent",
        labels={"primary_school_enrollment_percent": "%", "country_name": "Country"}
    )
    r2.plotly_chart(fig_school, use_container_width=True)

    r3, r4 = st.columns(2)
    fig_urban = px.line(
        df_filtered, x="year", y="urban_population_percent", color="country_name",
        markers=True, title="Urban population percent",
        labels={"urban_population_percent": "%", "country_name": "Country"}
    )
    r3.plotly_chart(fig_urban, use_container_width=True)

    fig_pop = px.line(
        df_filtered, x="year", y="population_total", color="country_name",
        markers=True, title="Population total over time",
        labels={"population_total": "People", "country_name": "Country"}
    )
    r4.plotly_chart(fig_pop, use_container_width=True)

# Environmental
with tab_env:
    st.caption("Environmental indicator")
    fig_co2 = px.line(
        df_filtered, x="year", y="co2_emissions_tons_per_capita", color="country_name",
        markers=True, title="CO₂ emissions tons per capita over time",
        labels={"co2_emissions_tons_per_capita": "Tons per capita", "country_name": "Country"}
    )
    st.plotly_chart(fig_co2, use_container_width=True)

    if not snap_co2pc.empty:
        fig_map = px.choropleth(
            snap_co2pc,
            locations="country_code",
            color="co2_emissions_tons_per_capita",
            hover_name="country_name",
            locationmode="ISO-3",
            color_continuous_scale="YlOrRd",
            title=f"CO₂ emissions tons per capita in {yr_co2pc}",
            labels={"co2_emissions_tons_per_capita": "Tons per capita"}
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("No CO₂ snapshot available in the selected window.")

# Comparison
with tab_comp:
    st.caption("Cross country comparison")
    left, right = st.columns([2, 1])
    with left:
        indicator_options = {
            "GDP per capita USD": "gdp_per_capita_usd",
            "Population total": "population_total",
            "CO₂ tons per capita": "co2_emissions_tons_per_capita",
            "Life expectancy years": "life_expectancy_years",
            "Primary school enrollment %": "primary_school_enrollment_percent",
            "Urban population %": "urban_population_percent",
            "Total CO₂ emissions tons": "total_co2_emissions_tons",
        }
        sel_name = st.selectbox("Indicator", list(indicator_options.keys()))
        sel_col = indicator_options[sel_name]
    with right:
        years_available = sorted(df_filtered["year"].unique())
        comp_year = st.selectbox("Year", years_available, index=len(years_available) - 1)

    comp_df = df_filtered[df_filtered["year"] == comp_year].dropna(subset=[sel_col]).copy()
    if comp_df.empty:
        st.info("No data for this selection.")
    else:
        cA, cB = st.columns([3, 2])
        fig_cmp_map = px.choropleth(
            comp_df,
            locations="country_code",
            color=sel_col,
            hover_name="country_name",
            locationmode="ISO-3",
            color_continuous_scale="Viridis",
            title=f"{sel_name} in {comp_year}",
            labels={sel_col: sel_name}
        )
        cA.plotly_chart(fig_cmp_map, use_container_width=True)

        comp_df = comp_df.sort_values(sel_col, ascending=False)
        fig_cmp_bar = px.bar(
            comp_df, x="country_name", y=sel_col, color="country_name",
            title=f"{sel_name} in {comp_year}",
            labels={"country_name": "Country", sel_col: sel_name}
        )
        fig_cmp_bar.update_layout(showlegend=False)
        fig_cmp_bar.update_xaxes(tickangle=-30)
        cB.plotly_chart(fig_cmp_bar, use_container_width=True)

# Automated Summaries (moved to last)
with tab_summary:
    st.caption("Automated insights for the selected scope")
    bullets = []

    if not snap_gdp.empty:
        top_row = snap_gdp.dropna(subset=["gdp_per_capita_usd"]).sort_values("gdp_per_capita_usd", ascending=False).head(1)
        if not top_row.empty:
            bullets.append(f"{top_row.iloc[0]['country_name']} leads GDP per capita at {fmt_num(top_row.iloc[0]['gdp_per_capita_usd'])} in {yr_gdp}.")

    tmp = growth.dropna(subset=["gdp_cagr"]).sort_values("gdp_cagr", ascending=False)
    if not tmp.empty:
        row = tmp.iloc[0]
        bullets.append(f"{row['country_name']} shows the fastest GDP per capita growth at {fmt_pct(row['gdp_cagr'], 2)} during {int(row['year_start'])}–{int(row['year_end'])}.")

    tmp = growth.dropna(subset=["life_change"]).sort_values("life_change", ascending=False)
    if not tmp.empty:
        row = tmp.iloc[0]
        bullets.append(f"{row['country_name']} records the largest life expectancy gain at {fmt_num(row['life_change'], 1)} years during {int(row['year_start'])}–{int(row['year_end'])}.")

    if not snap_co2pc.empty:
        low = snap_co2pc.dropna(subset=["co2_emissions_tons_per_capita"]).sort_values("co2_emissions_tons_per_capita").head(1)
        if not low.empty:
            bullets.append(f"{low.iloc[0]['country_name']} has the lowest CO₂ per capita at {fmt_num(low.iloc[0]['co2_emissions_tons_per_capita'], 2)} tons in {yr_co2pc}.")

    if len(bullets) == 0:
        st.info("No narratives available for the current selection.")
    else:
        for b in bullets:
            st.markdown(f"• {b}")

    with st.expander("Data quality summary"):
        dq = []
        dq.append({"Indicator": "GDP per capita", "Snapshot Year": yr_gdp, "Countries": f"{g_have}/{g_total}"})
        dq.append({"Indicator": "Life expectancy", "Snapshot Year": yr_life, "Countries": f"{l_have}/{l_total}"})
        dq.append({"Indicator": "CO₂ per capita", "Snapshot Year": yr_co2pc, "Countries": f"{c_have}/{c_total}"})
        st.dataframe(pd.DataFrame(dq), use_container_width=True)

# ======================================================
# Data table and downloads
# ======================================================
st.subheader("View and download filtered data")

export_columns = st.multiselect(
    "Columns to include",
    options=list(df_filtered.columns),
    default=list(df_filtered.columns)
)
view_df = df_filtered[export_columns].copy()
st.dataframe(view_df, use_container_width=True)

def make_context_filename(prefix: str, ext: str) -> str:
    yrs = f"{start_year}_{end_year}"
    if len(selected_countries) <= 4:
        cc = "-".join([c.replace(' ', '') for c in selected_countries])
    else:
        cc = f"{len(selected_countries)}countries"
    return f"{prefix}_{cc}_{yrs}.{ext}"

# Prepare bytes for both formats
csv_bytes = view_df.to_csv(index=False).encode("utf-8")
excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
    view_df.to_excel(writer, index=False, sheet_name="Data")
excel_bytes = excel_buffer.getvalue()

fmt_col, btn_col = st.columns([1, 3])
with fmt_col:
    fmt = st.selectbox("Download type", ["CSV", "Excel"])
with btn_col:
    if fmt == "CSV":
        st.download_button(
            "Download",
            data=csv_bytes,
            file_name=make_context_filename("filtered_data", "csv"),
            mime="text/csv"
        )
    else:
        st.download_button(
            "Download",
            data=excel_bytes,
            file_name=make_context_filename("filtered_data", "xlsx"),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )