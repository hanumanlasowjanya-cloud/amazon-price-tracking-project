from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st


EXCEL_FILE = "amazon_products.xlsx"
REQUIRED_COLUMNS = ["Product Name", "Product URL", "Price", "Date", "Product ID"]


st.set_page_config(
    page_title="Amazon Price Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_data():
    """Load existing Excel history without changing it."""
    try:
        df = pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        st.error(f"{EXCEL_FILE} not found. Run the scraper first or place the file in this folder.")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = None

    df = df[REQUIRED_COLUMNS].copy()
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Product Name", "Product ID", "Price", "Date"])
    df = df[df["Price"] > 0]
    return df.sort_values(["Product ID", "Date"])


def latest_products(df):
    latest = df.sort_values("Date").groupby("Product ID", as_index=False).tail(1).copy()
    previous = df.copy()
    previous["Previous Price"] = previous.groupby("Product ID")["Price"].shift(1)
    previous = previous.groupby("Product ID", as_index=False).tail(1)[["Product ID", "Previous Price"]]
    latest = latest.merge(previous, on="Product ID", how="left")
    latest["Previous Price"] = latest["Previous Price"].fillna(latest["Price"])
    latest["Price Difference"] = latest["Price"] - latest["Previous Price"]
    latest["Discount %"] = (
        ((latest["Previous Price"] - latest["Price"]) / latest["Previous Price"]) * 100
    ).clip(lower=0).fillna(0)
    latest["Status"] = "Stable"
    latest.loc[latest["Price"] < latest["Previous Price"], "Status"] = "Price Dropped"
    latest.loc[latest["Price"] > latest["Previous Price"], "Status"] = "Price Increased"
    return latest


def rupees(value):
    return f"₹{float(value):,.0f}"


def inject_css():
    st.markdown(
        """
        <style>
        .stApp { background: #f6f7fb; }
        .main-title {
            padding: 20px 22px;
            border-radius: 14px;
            color: white;
            background: linear-gradient(135deg, #131921, #243447 62%, #ff9900);
            box-shadow: 0 16px 35px rgba(19,25,33,.18);
            margin-bottom: 18px;
        }
        .main-title h1 { margin: 0; font-size: clamp(28px, 4vw, 42px); }
        .main-title p { margin: 8px 0 0; color: #e5e7eb; }
        .metric-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 10px 26px rgba(17,24,39,.08);
            min-height: 112px;
        }
        .metric-label { color: #6b7280; font-size: 12px; font-weight: 800; text-transform: uppercase; }
        .metric-value { color: #111827; font-size: clamp(22px, 3vw, 30px); font-weight: 900; margin-top: 8px; }
        .deal-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 14px;
            box-shadow: 0 10px 26px rgba(17,24,39,.08);
            min-height: 190px;
        }
        .deal-title { font-weight: 800; color: #111827; line-height: 1.35; height: 58px; overflow: hidden; }
        .deal-price { font-size: 24px; font-weight: 900; margin-top: 10px; }
        .pill { display: inline-block; border-radius: 999px; padding: 5px 10px; font-weight: 800; font-size: 12px; margin-top: 8px; }
        .drop { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
        .up { background: #dbeafe; color: #1d4ed8; border: 1px solid #bfdbfe; }
        .stable { background: #f3f4f6; color: #374151; border: 1px solid #d1d5db; }
        @media (max-width: 768px) {
            .block-container { padding-left: .75rem; padding-right: .75rem; }
            .main-title { padding: 16px; border-radius: 10px; }
            .metric-card, .deal-card { margin-bottom: 10px; min-height: auto; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_grid(latest, df):
    biggest_drop = max((latest["Previous Price"] - latest["Price"]).max(), 0)
    metrics = [
        ("Total Products", f"{latest['Product ID'].nunique():,}"),
        ("Average Price", rupees(latest["Price"].mean())),
        ("Lowest Price", rupees(latest["Price"].min())),
        ("Highest Price", rupees(latest["Price"].max())),
        ("Biggest Price Drop", rupees(biggest_drop)),
        ("History Rows", f"{len(df):,}"),
    ]
    for start in range(0, len(metrics), 3):
        cols = st.columns(3)
        for col, (label, value) in zip(cols, metrics[start:start + 3]):
            col.markdown(
                f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div></div>",
                unsafe_allow_html=True,
            )


def product_cards(latest):
    cards = latest.sort_values(["Discount %", "Price"], ascending=[False, True]).head(6)
    for start in range(0, len(cards), 3):
        cols = st.columns(3)
        for col, (_, row) in zip(cols, cards.iloc[start:start + 3].iterrows()):
            status_class = "drop" if row["Status"] == "Price Dropped" else "up" if row["Status"] == "Price Increased" else "stable"
            status_text = "PRICE DROPPED" if row["Status"] == "Price Dropped" else "PRICE INCREASED" if row["Status"] == "Price Increased" else "STABLE"
            product_url = row.get("Product URL")
            link_html = f'<div><a href="{product_url}" target="_blank">View on Amazon</a></div>' if pd.notna(product_url) and str(product_url).strip() else ""
            col.markdown(
                f"""
                <div class="deal-card">
                    <div class="deal-title">{row['Product Name']}</div>
                    <div class="deal-price">{rupees(row['Price'])}</div>
                    <div>Previous: {rupees(row['Previous Price'])}</div>
                    <div>Difference: {rupees(abs(row['Price Difference']))} | Discount: {row['Discount %']:.1f}%</div>
                    <span class="pill {status_class}">{status_text}</span>
                    {link_html}
                </div>
                """,
                unsafe_allow_html=True,
            )


def main():
    inject_css()
    st.markdown(
        """
        <div class="main-title">
            <h1>Amazon Price Tracker</h1>
            <p>Excel-based price history dashboard for tracking Amazon product price changes.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = load_data()
    if df.empty:
        st.stop()

    latest = latest_products(df)

    st.sidebar.header("Filters")
    product_options = latest["Product Name"].sort_values().tolist()
    selected_products = st.sidebar.multiselect("Products", product_options, default=product_options[:5])
    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()
    selected_dates = st.sidebar.date_input("Date range", (min_date, max_date), min_value=min_date, max_value=max_date)

    filtered_latest = latest[latest["Product Name"].isin(selected_products)] if selected_products else latest
    filtered_history = df[df["Product ID"].isin(filtered_latest["Product ID"])]
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = pd.to_datetime(selected_dates[0]), pd.to_datetime(selected_dates[1])
        filtered_history = filtered_history[
            (filtered_history["Date"] >= start_date) & (filtered_history["Date"] <= end_date + pd.Timedelta(days=1))
        ]

    metric_grid(filtered_latest, filtered_history)

    st.subheader("Top Deals & Price Changes")
    product_cards(filtered_latest)

    st.subheader("Price History")
    if filtered_history["Product ID"].nunique() >= 1:
        fig = px.line(
            filtered_history,
            x="Date",
            y="Price",
            color="Product Name",
            markers=True,
            template="plotly_white",
            labels={"Price": "Price (₹)", "Date": "Date"},
        )
        fig.update_layout(height=430, hovermode="x unified", legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Top 5 Cheapest Products")
        cheapest = filtered_latest.sort_values("Price").head(5).copy()
        cheapest["Short Name"] = cheapest["Product Name"].str.slice(0, 34)
        fig = px.bar(cheapest, x="Short Name", y="Price", template="plotly_white")
        fig.update_layout(height=360, xaxis_title="", yaxis_title="Price (₹)")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Product Analytics")
        selected = st.selectbox("Select product", filtered_latest["Product Name"].tolist())
        product_id = filtered_latest.loc[filtered_latest["Product Name"] == selected, "Product ID"].iloc[0]
        product_history = filtered_history[filtered_history["Product ID"] == product_id].sort_values("Date")
        if product_history.empty:
            st.info("No records found for the selected product in this date range.")
        else:
            cheapest_day = product_history.loc[product_history["Price"].idxmin()]
            highest_day = product_history.loc[product_history["Price"].idxmax()]
            c1, c2 = st.columns(2)
            c1.metric("Cheapest Day", cheapest_day["Date"].strftime("%Y-%m-%d"), rupees(cheapest_day["Price"]))
            c2.metric("Highest Price", rupees(highest_day["Price"]), highest_day["Date"].strftime("%Y-%m-%d"))
            st.dataframe(product_history.tail(10), use_container_width=True, hide_index=True)

    st.caption(f"Last dashboard refresh: {date.today().isoformat()} | Source file: {EXCEL_FILE}")


if __name__ == "__main__":
    main()
