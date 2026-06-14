import pandas as pd
import plotly.express as px


EXCEL_FILE = "amazon_products.xlsx"
REQUIRED_COLUMNS = ["Product Name", "Product URL", "Price", "Date", "Product ID"]


def load_price_history():
    df = pd.read_excel(EXCEL_FILE)
    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = None

    df = df[REQUIRED_COLUMNS].copy()
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Product Name", "Product ID", "Price", "Date"])
    df = df[df["Price"] > 0]
    return df.sort_values("Date")


def latest_products(df):
    latest = df.groupby("Product ID", as_index=False).tail(1).copy()
    latest["Previous Price"] = df.groupby("Product ID")["Price"].shift(1).groupby(df["Product ID"]).transform("last")
    latest["Previous Price"] = latest["Previous Price"].fillna(latest["Price"])
    latest["Price Difference"] = latest["Price"] - latest["Previous Price"]
    latest["Discount %"] = (
        ((latest["Previous Price"] - latest["Price"]) / latest["Previous Price"]) * 100
    ).clip(lower=0).fillna(0)
    return latest


def print_summary():
    df = load_price_history()
    latest = latest_products(df)
    print("Amazon Price Tracker Summary")
    print("-" * 36)
    print(f"History rows: {len(df)}")
    print(f"Unique products: {latest['Product ID'].nunique()}")
    print(f"Average latest price: Rs.{latest['Price'].mean():,.0f}")
    print(f"Lowest latest price: Rs.{latest['Price'].min():,.0f}")
    print(f"Highest latest price: Rs.{latest['Price'].max():,.0f}")


def build_price_trend_figure(product_names=None):
    df = load_price_history()
    if product_names:
        df = df[df["Product Name"].isin(product_names)]
    return px.line(df, x="Date", y="Price", color="Product Name", markers=True, template="plotly_white")


if __name__ == "__main__":
    print_summary()
