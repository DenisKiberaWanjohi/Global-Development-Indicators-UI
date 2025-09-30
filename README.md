# 🌍 Global Development Indicators Dashboard

An interactive analytics dashboard built with **Streamlit** and **Plotly**, powered by **Google BigQuery Public Datasets**.  
This project demonstrates how to combine open data and modern UI frameworks to deliver insights similar to Tableau or Power BI, but fully in Python.

---

## ▶️ Access the Dashboard

👉 You can access the live UI here:  
[**Global Development Indicators Dashboard**](https://global-development-indicators-ui.streamlit.app/)

---

## 📊 Data Source

The dashboard uses the **World Bank World Development Indicators** dataset from **BigQuery Public Data**:

- **GDP per capita (current US$)**  
- **Population, total**  
- **CO₂ emissions (metric tons per capita)**  
- **Life expectancy at birth (years)**  
- **School enrollment, primary (% gross)**  
- **Urban population (% of total population)**  

---

## 💻 Features

### 🔎 Filters
- Top-row filters for **countries** and **year range** (calendar selector).  
- Multi-select columns for exporting data.  

### 📈 Visualizations
- **Economic indicators**: GDP per capita trends, population totals.  
- **Social indicators**: Life expectancy, school enrollment, urbanization.  
- **Environmental indicators**: CO₂ emissions per capita trends and choropleth maps.  
- **Comparison view**: Select any indicator and year to compare across countries with side-by-side bar charts and maps.  
- **Automated Summaries**: Narrative insights generated from the data, highlighting leaders, laggards, and growth patterns.  

### 🧾 Executive Scorecards
- Averages across selected countries.  
- Gaps between highest and lowest performers.  
- Growth rates (CAGR) for GDP and population.  
- Leaders in GDP growth, life expectancy improvement, and CO₂ reduction.  
- Transparent data quality coverage per indicator.  

### 📥 Data Export
- Export filtered data in **CSV** or **Excel** format.  
- Filenames dynamically reflect selected countries and years for traceability.  

---

## 🚀 Impact

This dashboard shows how open data and modern Python tools can:

- Deliver **high-level insights** for decision-makers.  
- Replace manual reporting with **automated, interactive analysis**.  
- Empower analysts to explore **economic, social, and environmental trends** without needing a heavy BI platform.  
- Enhance transparency by showing **data coverage and quality** alongside metrics.  

---

## 🛠️ Tech Stack

- **Python**  
- **Streamlit** – interactive UI  
- **Plotly Express** – charts and maps  
- **Pandas** – data wrangling  
- **Google BigQuery** – public dataset sourcing  

---


