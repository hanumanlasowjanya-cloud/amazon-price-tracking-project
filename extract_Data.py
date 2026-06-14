from datetime import datetime
from urllib.parse import urljoin

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


EXCEL_FILE = "amazon_products.xlsx"
SEARCH_URL = "https://www.amazon.in/s?k=laptop"
AMAZON_BASE_URL = "https://www.amazon.in"
MAX_PRODUCTS = 10
REQUIRED_COLUMNS = ["Product Name", "Product URL", "Price", "Date", "Product ID"]
TEXT_COLUMNS = ["Product Name", "Product URL", "Date", "Product ID"]


def normalize_history(df):
    for column in REQUIRED_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    df = df[REQUIRED_COLUMNS].copy()
    for column in TEXT_COLUMNS:
        df[column] = df[column].fillna("").astype(object)

    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    return df


def read_existing_history():
    try:
        df = pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    return normalize_history(df)


def make_product_id(product_name, product_url=""):
    """Prefer Amazon URL as the stable identifier, then fall back to title text."""
    if product_url:
        return str(product_url).split("?")[0].rstrip("/")

    words = str(product_name).split()
    return " ".join(words[:5]) if words else "unknown-product"


def clean_price(price_text):
    digits = "".join(ch for ch in str(price_text) if ch.isdigit())
    return int(digits) if digits else None


def extract_product_url(card):
    link_elements = card.find_elements(By.CSS_SELECTOR, "h2 a")
    if not link_elements:
        return ""

    href = link_elements[0].get_attribute("href") or ""
    return urljoin(AMAZON_BASE_URL, href.split("?")[0]) if href else ""


def scrape_amazon_products():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)
    scraped = []
    try:
        driver.get(SEARCH_URL)
        driver.implicitly_wait(8)
        product_cards = driver.find_elements(By.XPATH, "//div[@data-component-type='s-search-result']")

        for card in product_cards[:MAX_PRODUCTS]:
            name_elements = card.find_elements(By.CSS_SELECTOR, "h2 span")
            price_elements = card.find_elements(By.CSS_SELECTOR, ".a-price-whole")

            product_name = name_elements[0].text.strip().replace("\n", " ") if name_elements else ""
            product_url = extract_product_url(card)
            price = clean_price(price_elements[0].text if price_elements else "")

            if not product_name or price is None or price <= 0:
                continue

            scraped.append(
                {
                    "Product ID": make_product_id(product_name, product_url),
                    "Product Name": product_name,
                    "Product URL": product_url,
                    "Price": price,
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                }
            )
    finally:
        driver.quit()

    return scraped


def merge_today_prices(existing_df, scraped_rows):
    """Append new daily history rows and update today's row for repeated products."""
    if not scraped_rows:
        return existing_df

    final_df = normalize_history(existing_df)
    today = datetime.now().strftime("%Y-%m-%d")

    for row in scraped_rows:
        product_id = row["Product ID"]
        product_name = row["Product Name"]
        product_url = "" if pd.isna(row.get("Product URL", "")) else str(row.get("Product URL", ""))
        price = row["Price"]

        same_product = (
            (final_df["Product ID"].astype(str) == str(product_id))
            | (final_df["Product URL"].fillna("").astype(str) == str(product_url))
            | (final_df["Product Name"].astype(str) == str(product_name))
        )
        same_day = final_df["Date"].astype(str).str[:10] == today
        existing_today = final_df[same_product & same_day]

        previous_rows = final_df[same_product].copy()
        if not previous_rows.empty:
            previous_rows["Date"] = pd.to_datetime(previous_rows["Date"], errors="coerce")
            previous_rows = previous_rows.sort_values("Date")
            previous_price = pd.to_numeric(previous_rows.iloc[-1]["Price"], errors="coerce")
            if pd.notna(previous_price):
                if price < previous_price:
                    print(f"PRICE DROPPED: {product_name[:70]}")
                    print(f"Old: Rs.{previous_price:,.0f} -> New: Rs.{price:,.0f} | Save Rs.{previous_price - price:,.0f}")
                elif price > previous_price:
                    print(f"PRICE INCREASED: {product_name[:70]}")
                    print(f"Old: Rs.{previous_price:,.0f} -> New: Rs.{price:,.0f}")

        if not existing_today.empty:
            index = existing_today.index[-1]
            final_df.loc[index, "Product ID"] = product_id
            final_df.loc[index, "Product Name"] = product_name
            final_df.loc[index, "Product URL"] = product_url
            final_df.loc[index, "Price"] = price
            final_df.loc[index, "Date"] = today
        else:
            final_df = pd.concat([final_df, pd.DataFrame([row])], ignore_index=True)

    final_df = final_df[REQUIRED_COLUMNS]
    return final_df


def main():
    print("Reading existing Excel history...")
    existing_df = read_existing_history()
    print(f"Existing rows preserved: {len(existing_df)}")

    print("Scraping Amazon products...")
    try:
        scraped_rows = scrape_amazon_products()
    except WebDriverException as exc:
        print(f"Selenium error: {exc}")
        return

    print(f"Scraped valid products: {len(scraped_rows)}")
    updated_df = merge_today_prices(existing_df, scraped_rows)

    updated_df.to_excel(EXCEL_FILE, index=False)
    print(f"Saved {len(updated_df)} total history rows to {EXCEL_FILE}")


if __name__ == "__main__":
    main()
