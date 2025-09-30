🌍 Global Development Indicators Dashboard

An interactive analytics dashboard built with Streamlit and Plotly, powered by Google BigQuery Public Datasets.
This project demonstrates how to combine open data and modern UI frameworks to deliver insights similar to Tableau or Power BI, but fully in Python.

📊 Data Source

The dashboard uses the World Bank World Development Indicators dataset from BigQuery Public Data:

GDP per capita (current US$)

Population, total

CO₂ emissions (metric tons per capita)

Life expectancy at birth (years)

School enrollment, primary (% gross)

Urban population (% of total population)

Querying is done directly from BigQuery, ensuring access to reliable and up-to-date global development statistics.

💻 Features
🔎 Filters

Top-row filters for countries and year range (calendar selector).

Multi-select columns for exporting data.

Defaults set to all countries and 2010–2015 for ease of exploration.

📈 Visualizations

Economic indicators: GDP per capita trends, population totals.

Social indicators: Life expectancy, school enrollment, urbanization.

Environmental indicators: CO₂ emissions per capita trends and choropleth maps.

Comparison view: Select any indicator and year to compare across countries with side-by-side bar charts and maps.

Automated Summaries: Narrative insights generated from the data, highlighting leaders, laggards, and growth patterns.

🧾 Executive Scorecards

Average values across countries.

Gaps between highest and lowest performers.

Growth rates (CAGR) for GDP and population.

Leaders in GDP growth, life expectancy improvement, and CO₂ reduction.

Transparent data quality coverage per indicator.

📥 Data Export

Export filtered data in CSV or Excel format.

Filenames dynamically reflect selected countries and years for traceability.

🚀 Impact

This dashboard demonstrates how open data and modern Python tools can:

Deliver high-level insights for decision-makers.

Replace manual reporting with automated, interactive analysis.

Empower analysts to dive into economic, social, and environmental trends without needing a heavy BI platform.

Enhance transparency by showing data coverage and quality alongside metrics.

🛠️ Tech Stack

Python

Streamlit for interactive UI

Plotly Express for rich, interactive charts and maps

Pandas for data wrangling

Google BigQuery (Public Dataset) for data sourcing
