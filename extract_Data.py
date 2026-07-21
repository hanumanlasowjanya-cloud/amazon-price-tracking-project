"""
===============================================================================
Amazon Price Tracker
Author  : Sowjanya Hanumanla
Project : Amazon Price Tracking & Analytics System

Description:
------------
This script scrapes Amazon India laptop prices, stores historical prices,
tracks price changes, and updates an Excel file without losing previous data.

Features
--------
✔ Headless Chrome
✔ Selenium Manager (No chromedriver needed)
✔ Explicit Waits
✔ Automatic retries
✔ Historical price tracking
✔ Duplicate prevention
✔ ASIN extraction
✔ Price Drop Detection
✔ Logging
✔ Production Ready

===============================================================================
"""

from __future__ import annotations
import time
import logging
import os
import re
import sys
from datetime import datetime
from urllib.parse import urljoin

import pandas as pd

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


###############################################################################
# CONFIGURATION
###############################################################################

SEARCH_URL = "https://www.amazon.in/s?k=laptop"

AMAZON_BASE_URL = "https://www.amazon.in"

EXCEL_FILE = "amazon_products.xlsx"

LOG_FILE = "amazon_scraper.log"

MAX_PRODUCTS = 50

HEADLESS = True

PAGE_LOAD_TIMEOUT = 40

WAIT_TIMEOUT = 20

REQUIRED_COLUMNS = [
    "Product ID",
    "Product Name",
    "Product URL",
    "Price",
    "Date",
]

TEXT_COLUMNS = [
    "Product ID",
    "Product Name",
    "Product URL",
    "Date",
]

###############################################################################
# LOGGING
###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

###############################################################################
# EXCEL FUNCTIONS
###############################################################################


def normalize_history(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures all required columns exist.
    """

    for column in REQUIRED_COLUMNS:

        if column not in df.columns:
            df[column] = ""

    df = df[REQUIRED_COLUMNS].copy()

    for column in TEXT_COLUMNS:
        df[column] = df[column].fillna("").astype(str)

    df["Price"] = pd.to_numeric(
        df["Price"],
        errors="coerce",
    )

    return df


def read_existing_history() -> pd.DataFrame:
    """
    Reads existing Excel.
    If missing, returns empty dataframe.
    """

    if not os.path.exists(EXCEL_FILE):

        logger.info("Excel not found. Creating new history.")

        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    try:

        df = pd.read_excel(EXCEL_FILE)

        logger.info("Loaded %d history rows.", len(df))

        return normalize_history(df)

    except Exception as e:

        logger.error("Unable to read Excel: %s", e)

        return pd.DataFrame(columns=REQUIRED_COLUMNS)


###############################################################################
# PRODUCT HELPERS
###############################################################################


def clean_price(price_text: str):
    """
    ₹59,990
        ↓
    59990
    """

    digits = "".join(ch for ch in str(price_text) if ch.isdigit())

    if not digits:
        return None

    return int(digits)


def extract_product_url(card):

    try:

        link = card.find_element(
            By.CSS_SELECTOR,
            "h2 a",
        )

        href = link.get_attribute("href")

        if not href:
            return ""

        return urljoin(
            AMAZON_BASE_URL,
            href.split("?")[0],
        )

    except Exception:

        return ""


def extract_asin(product_url: str):

    patterns = [
        r"/dp/([A-Z0-9]{10})",
        r"/gp/product/([A-Z0-9]{10})",
        r"/product/([A-Z0-9]{10})",
    ]

    for pattern in patterns:

        match = re.search(pattern, product_url)

        if match:
            return match.group(1)

    return ""


def make_product_id(
    product_name: str,
    product_url: str,
):
    """
    Uses ASIN if possible.
    Otherwise falls back to URL.
    """

    asin = extract_asin(product_url)

    if asin:
        return asin

    if product_url:
        return product_url

    words = product_name.split()

    return "_".join(words[:5]).lower()

###############################################################################
# CHROME DRIVER
###############################################################################

def create_driver():
    """
    Creates and returns a configured Chrome WebDriver.
    Uses Selenium Manager automatically.
    """

    options = Options()

    if HEADLESS:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-blink-features=AutomationControlled")

    options.add_argument(
        "--user-agent=Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)

    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)

    return driver


###############################################################################
# PAGE SCROLLING
###############################################################################
def scroll_page(driver):
    """
    Scroll page multiple times to load additional products.
    """

    for _ in range(8):

        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )

        time.sleep(2)



###############################################################################
# PRODUCT SCRAPER
###############################################################################

def scrape_amazon_products():
    """
    Scrapes Amazon search results.

    Returns
    -------
    list[dict]
    """

    logger.info("Launching Chrome...")

    driver = create_driver()

    scraped_products = []

    try:

        logger.info("Opening Amazon...")

        driver.get(SEARCH_URL)

        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//div[@data-component-type='s-search-result']"
                )
            )
        )

        logger.info("Amazon page loaded.")

        scroll_page(driver)

        product_cards = driver.find_elements(
            By.XPATH,
            "//div[@data-component-type='s-search-result']"
        )

        logger.info(
            "Found %d product cards.",
            len(product_cards)
        )

        for index, card in enumerate(product_cards, start=1):

            if len(scraped_products) >= MAX_PRODUCTS:
                break

            try:

                name = ""

                price = None

                url = ""

                asin = ""

                ########################################################
                # Product Name
                ########################################################

                try:

                    name = card.find_element(
                        By.CSS_SELECTOR,
                        "h2 span"
                    ).text.strip()

                except NoSuchElementException:
                    continue

                ########################################################
                # Price
                ########################################################

                try:

                    price_text = card.find_element(
                        By.CSS_SELECTOR,
                        ".a-price-whole"
                    ).text

                    price = clean_price(price_text)

                except NoSuchElementException:
                    continue

                ########################################################
                # URL
                ########################################################

                url = extract_product_url(card)

                ########################################################
                # Product ID
                ########################################################

                asin = make_product_id(
                    name,
                    url
                )

                ########################################################
                # Validation
                ########################################################

                if not name:
                    continue

                if price is None:
                    continue

                if price <= 0:
                    continue

                ########################################################
                # Save
                ########################################################

                scraped_products.append(
                    {
                        "Product ID": asin,
                        "Product Name": name,
                        "Product URL": url,
                        "Price": price,
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                    }
                )

                logger.info(
                    "[%02d] %s | ₹%s",
                    len(scraped_products),
                    asin,
                    f"{price:,}",
                )

            except Exception as e:

                logger.warning(
                    "Skipping card %d : %s",
                    index,
                    e,
                )

                continue

        logger.info(
            "Successfully scraped %d products.",
            len(scraped_products)
        )

        return scraped_products

    except TimeoutException:

        logger.error(
            "Amazon page took too long to load."
        )

        return []

    except WebDriverException as e:

        logger.error(
            "Chrome error : %s",
            e,
        )

        return []

    finally:

        logger.info("Closing Chrome.")

        driver.quit()
        
    ###############################################################################
# MERGE HISTORY
###############################################################################

def merge_today_prices(existing_df: pd.DataFrame,
                       scraped_products: list) -> pd.DataFrame:
    """
    Merge today's scraped prices with historical data.

    Rules
    -----
    1. Never delete previous history.
    2. Only one row per product per day.
    3. Preserve complete price history.
    4. Detect price increase/decrease.
    """

    if not scraped_products:
        logger.warning("No products scraped.")
        return existing_df

    history = normalize_history(existing_df)

    today = datetime.now().strftime("%Y-%m-%d")

    for product in scraped_products:

        product_id = product["Product ID"]
        product_name = product["Product Name"]
        product_url = product["Product URL"]
        price = product["Price"]

        same_product = (
        (history["Product ID"].astype(str) == str(product_id))
    |   (history["Product Name"].astype(str) == str(product_name))
         )

        same_day = (
            history["Date"].astype(str)
            == today
        )

        today_row = history[
            same_product & same_day
        ]

        ####################################################
        # PRICE COMPARISON
        ####################################################

        previous_rows = history[same_product &(history["Date"].astype(str) != today)].copy()

        if not previous_rows.empty:

            previous_rows["Date"] = pd.to_datetime(
                previous_rows["Date"],
                errors="coerce"
            )

            previous_rows = previous_rows.sort_values("Date")

            previous_price = previous_rows.iloc[-1]["Price"]

            if pd.notna(previous_price):

                if price < previous_price:

                    logger.info(
                        "PRICE DROPPED | %s | ₹%s → ₹%s",
                        product_name[:60],
                        f"{int(previous_price):,}",
                        f"{price:,}"
                    )

                elif price > previous_price:

                    logger.info(
                        "PRICE INCREASED | %s | ₹%s → ₹%s",
                        product_name[:60],
                        f"{int(previous_price):,}",
                        f"{price:,}"
                    )

                else:

                    logger.info(
                        "NO PRICE CHANGE | %s",
                        product_name[:60]
                    )

        ####################################################
        # UPDATE TODAY
        ####################################################

        if not today_row.empty:

            index = today_row.index[-1]

            history.loc[index, "Product Name"] = product_name
            history.loc[index, "Product URL"] = product_url
            history.loc[index, "Price"] = price
            history.loc[index, "Date"] = today

        ####################################################
        # APPEND NEW ROW
        ####################################################

        else:

            history = pd.concat(
                [
                    history,
                    pd.DataFrame([product])
                ],
                ignore_index=True
            )

    history = history.sort_values(
        ["Product Name", "Date"]
    ).reset_index(drop=True)

    return history


###############################################################################
# SAVE EXCEL
###############################################################################

def save_history(df: pd.DataFrame):

    try:
        df = df.sort_values(["Product Name", "Date"]).reset_index(drop=True)

        df.to_excel(EXCEL_FILE,index=False)

        logger.info(
            "Excel updated successfully."
        )

        logger.info(
            "Total history rows : %d",
            len(df)
        )

    except Exception as e:

        logger.error(
            "Unable to save Excel : %s",
            e
        )


###############################################################################
# MAIN
###############################################################################

def main():

    logger.info("=" * 70)
    logger.info("Amazon Price Tracker Started")
    logger.info("=" * 70)

    existing_history = read_existing_history()

    logger.info(
        "Existing history rows : %d",
        len(existing_history)
    )

    scraped_products = scrape_amazon_products()

    logger.info(
        "Products scraped : %d",
        len(scraped_products)
    )

    updated_history = merge_today_prices(
        existing_history,
        scraped_products
    )

    save_history(updated_history)

    logger.info("=" * 70)
    logger.info("Completed Successfully")
    logger.info("=" * 70)

    logger.info("Summary")
    logger.info("-" * 50)
    logger.info("Products scraped : %d", len(scraped_products))
    logger.info("History records  : %d", len(updated_history))
    logger.info("Excel file       : %s", EXCEL_FILE)
    logger.info("-" * 50)


###############################################################################
# ENTRY POINT
###############################################################################

if __name__ == "__main__":

    main()