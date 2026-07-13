from datetime import datetime
from urllib.parse import urljoin
import re
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
    """Fallback if ASIN cannot be extracted."""
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

    if href:
        return urljoin(AMAZON_BASE_URL, href.split("?")[0])

    return ""


def extract_asin(product_url):
    """
    Extract Amazon ASIN from product URL.
    Example:
    https://www.amazon.in/.../dp/B0F3ABC123/
                    ↓
                 B0F3ABC123
    """
    match = re.search(r"/dp/([A-Z0-9]{10})", product_url)

    if match:
        return match.group(1)

    return ""


def scrape_amazon_products():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)

    scraped = []

    try:
        driver.get(SEARCH_URL)
        driver.implicitly_wait(8)

        product_cards = driver.find_elements(
            By.XPATH,
            "//div[@data-component-type='s-search-result']"
        )

        print(f"Cards found: {len(product_cards)}")

        for card in product_cards[:MAX_PRODUCTS]:

            name_elements = card.find_elements(By.CSS_SELECTOR, "h2 span")
            price_elements = card.find_elements(By.CSS_SELECTOR, ".a-price-whole")

            product_name = (
                name_elements[0].text.strip().replace("\n", " ")
                if name_elements else ""
            )

            product_url = extract_product_url(card)

            asin = extract_asin(product_url)

            price = clean_price(
                price_elements[0].text if price_elements else ""
            )

            if not product_name or price is None or price <= 0:
                continue

            print(f"ASIN: {asin}")

            scraped.append(
                {
                    "Product ID": asin,
                    "Product Name": product_name,
                    "Product URL": product_url,
                    "Price": price,
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                }
            )

    finally:
        driver.quit()

    return scraped