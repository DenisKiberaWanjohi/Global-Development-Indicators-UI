import streamlit as st
import pandas as pd
import altair as alt
from google.oauth2 import service_account
from google.cloud import bigquery
from io import BytesIO

# --- Page Config ---
st.set_page_config(page_title="Global Development Dashboard", layout="wide")

# Load credentials from secrets.toml
credentials_dict = st.secrets["gcp_service_account"]
credentials = service_account.Credentials.from_service_account_info(dict(credentials_dict))
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

# --- SQL Query ---
query = """
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
def get_data():
    return client.query(query).to_dataframe()

df = get_data()

# --- Sidebar Filters ---
st.sidebar.header("Filters")
countries = df["country_name"].unique().tolist()
selected_countries = st.sidebar.multiselect("Select Countries", countries, default=countries)

year_range = st.sidebar.slider("Select Year Range", min_value=2000, max_value=2020, value=(2005, 2020))
df_filtered = df[
    df["country_name"].isin(selected_countries) &
    df["year"].between(year_range[0], year_range[1])
]

# --- Column Selector for Export ---
st.sidebar.header("Export Settings")
export_columns = st.sidebar.multiselect("Select columns to export", df.columns.tolist(), default=df.columns.tolist())

# --- Main Dashboard ---
st.title("🌍 Global Development Indicators Dashboard")
st.markdown("Explore key economic, social, and environmental indicators from the World Bank (2000–2020).")

# --- Download Buttons ---
st.subheader("⬇️ Download Filtered Data")

col_csv, col_excel = st.columns(2)

with col_csv:
    csv = df_filtered[export_columns].to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", data=csv, file_name="filtered_data.csv", mime="text/csv")

with col_excel:
    output = BytesIO()
    df_filtered[export_columns].to_excel(output, index=False, engine="openpyxl")
    st.download_button("Download Excel", data=output.getvalue(), file_name="filtered_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Metrics ---
latest_year = df_filtered["year"].max()
latest_data = df_filtered[df_filtered["year"] == latest_year]

st.subheader(f"📊 Key Metrics for {latest_year}")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Average GDP per Capita (USD)", f"${latest_data['gdp_per_capita_usd'].mean():,.0f}")
with col2:
    st.metric("Avg Life Expectancy (Years)", f"{latest_data['life_expectancy_years'].mean():.1f}")
with col3:
    st.metric("Avg CO2 Emissions per Capita (Tons)", f"{latest_data['co2_emissions_tons_per_capita'].mean():.2f}")

# --- Charts ---
st.subheader("📈 Indicator Trends Over Time")

def plot_line_chart(df, y, title, y_title):
    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("year:O", title="Year"),
        y=alt.Y(y, title=y_title),
        color="country_name:N"
    ).properties(
        title=title,
        width=800,
        height=400
    ).interactive()
    st.altair_chart(chart)

plot_line_chart(df_filtered, "gdp_per_capita_usd", "GDP per Capita Over Time", "USD")
plot_line_chart(df_filtered, "life_expectancy_years", "Life Expectancy Over Time", "Years")
plot_line_chart(df_filtered, "co2_emissions_tons_per_capita", "CO2 Emissions per Capita Over Time", "Tons")
plot_line_chart(df_filtered, "primary_school_enrollment_percent", "Primary School Enrollment (%)", "%")
plot_line_chart(df_filtered, "urban_population_percent", "Urban Population (%)", "%")

# --- Data Table ---
st.subheader("📋 View Filtered Data")
st.dataframe(df_filtered[export_columns])

