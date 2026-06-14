# Amazon Price Tracker

An end-to-end Amazon India price tracking project that scrapes laptop listings with Selenium, stores daily price history in Excel, and visualizes price movement in a Streamlit dashboard.

The project is designed as a beginner-friendly data engineering and analytics portfolio project. It demonstrates web scraping, data cleaning, historical storage, price change detection, and dashboard reporting.

## Dashboard Preview

### Dashboard Home

![Dashboard Home](docs/screenshots/dashboard-home.png)

### Price Trend Graph

![Price Trend Graph](docs/screenshots/price-trend-graph.png)

### Product Analytics

![Product Analytics](docs/screenshots/product-analytics.png)

## Features

- Scrapes Amazon India laptop search results using Selenium.
- Extracts product name, product URL, price, date, and product ID.
- Rejects invalid prices where price is missing or less than or equal to zero.
- Stores daily price history in `amazon_products.xlsx`.
- Updates the same product for the current day instead of creating duplicate daily rows.
- Preserves older rows for trend analysis.
- Shows latest price, previous price, discount percentage, and price movement status.
- Displays product filters, date filters, price trend charts, cheapest products, and product-level analytics.

## Tech Stack

- Python
- Selenium
- Pandas
- OpenPyXL
- Streamlit
- Plotly

## Project Structure

```text
Amazon_Price/
|-- app.py
|-- dashboard.py
|-- extract_Data.py
|-- amazon_products.xlsx
|-- requirements.txt
|-- README.md
|-- .gitignore
`-- docs/
    `-- screenshots/
        |-- dashboard-home.png
        |-- price-trend-graph.png
        `-- product-analytics.png
```

## Data Columns

`amazon_products.xlsx` stores the price history with these columns:

- `Product Name`
- `Product URL`
- `Price`
- `Date`
- `Product ID`

## Installation

```bash
pip install -r requirements.txt
```

## Run the Scraper

```bash
python extract_Data.py
```

The scraper opens Amazon India, collects laptop listings, skips bad prices, and saves the cleaned product history to `amazon_products.xlsx`.

## Run the Dashboard

```bash
python -m streamlit run app.py
```

## How Historical Tracking Works

1. The scraper reads existing rows from `amazon_products.xlsx`.
2. New products are appended as new rows.
3. Products already captured today are updated for the same day.
4. Products captured on earlier dates are appended as new daily history rows.
5. The dashboard compares latest price against previous price to calculate price movement.

## Current Limitations

- Amazon page structure can change, so selectors may need maintenance.
- Amazon may block automated scraping depending on traffic and browser behavior.
- Excel is suitable for a portfolio-scale dataset, but a database is better for larger tracking.
- Product URL improves traceability, but ASIN extraction would be a stronger long-term identifier.

## Next Improvements

- Extract ASIN from product URLs.
- Add email alerts for price drops.
- Add scheduled scraping with Windows Task Scheduler, cron, or GitHub Actions.
- Move storage from Excel to SQLite or PostgreSQL.
- Add automated tests for price parsing, duplicate handling, and analytics.
- Deploy the dashboard on Streamlit Community Cloud.

## Portfolio Summary

This project demonstrates a complete scraping-to-dashboard workflow:

- Data collection with Selenium
- Data cleaning with Pandas
- Historical tracking in Excel
- Business analytics with Plotly
- Interactive reporting with Streamlit
