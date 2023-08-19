import os

import pandas as pd
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

# Constants for XPath expressions
FINANCIALS_XPATHS = {
    "income_statement": "/html/body/div[1]/div[2]/div[2]/div[2]/div/div",
    "balance_sheet": "/html/body/div[1]/div[2]/div[2]/div[3]/div/div",
    "cash_flow_statement": "/html/body/div[1]/div[2]/div[2]/div[4]/div/div",
}

RATIOS_XPATHS = {
    "profitability": "/html/body/div[1]/div[2]/div[2]/div[2]/div/div",
    "credit": "/html/body/div[1]/div[2]/div[2]/div[3]/div/div",
    "liquidity": "/html/body/div[1]/div[2]/div[2]/div[4]/div/div",
    "working_capital": "/html/body/div[1]/div[2]/div[2]/div[5]/div/div",
    "enterprise_value": "/html/body/div[1]/div[2]/div[2]/div[6]/div/div",
    "multiples": "/html/body/div[1]/div[2]/div[2]/div[7]/div/div",
    "per_share": "/html/body/div[1]/div[2]/div[2]/div[8]/div/div",
}


def get_children_elements(element: WebElement):
    return element.find_elements(By.XPATH, "./child::*")


def get_years_from_table_header(table_header: WebElement):
    years = []
    for column in get_children_elements(table_header):
        year = column.text.replace(" Y", "")
        if year.isdigit():
            years.append(year)
    return years[-10:]


def parse_table(driver, table_xpath):
    table = driver.find_element(By.XPATH, table_xpath)
    (table_header, table_rows_frame) = get_children_elements(table)

    years = get_years_from_table_header(table_header)
    metrics_names = []
    data = []

    rows_elements = get_children_elements(table_rows_frame)
    for row in rows_elements:
        columns = get_children_elements(row)
        metric_name = columns[0].text
        metrics_values = []

        metrics_names.append(metric_name)

        for column in columns[1:]:
            metric_value = column.text.replace(",", "")

            if metric_value == "- -":
                metric_value = "0"

            if metric_value == "12345" or metric_value == "":
                continue

            metrics_values.append(metric_value)

        data.append(metrics_values)

    data = [data[i][-10:] for i in range(len(data))]
    dataframe = pd.DataFrame(data=data, columns=years, index=metrics_names)
    return dataframe


def is_us_company(driver):
    xpath = "/html/body/div[1]/div[2]/div[2]/div/div"
    element = driver.find_elements(By.XPATH, xpath)

    if len(element) == 1:
        return False
    return True


def get_remaining_financial_types(ticker, financial_types):
    remaining_financial_types = []
    for financial_type in financial_types:
        directory = f"output/{ticker}/{financial_type}"
        if not os.path.exists(directory):
            remaining_financial_types.append(financial_type)
    return remaining_financial_types


def scrape_data(driver, tickers, period):
    financial_types = ["financials", "ratios"]
    mirrored_tickers = {
        "GOOGL": "GOOG",
    }

    for ticker in tickers:
        skip_non_us_companies = False
        remaining_financial_types = get_remaining_financial_types(ticker, financial_types)

        if len(remaining_financial_types) == 0:
            print(f"Skipping {ticker}...")
            continue

        for financial_type in remaining_financial_types:

            if skip_non_us_companies:
                break

            if financial_type == "financials":
                xpath_dict = FINANCIALS_XPATHS
            else:
                xpath_dict = RATIOS_XPATHS

            print(f"Scraping {financial_type} of {ticker}...")

            url = f"https://roic.ai/{financial_type}/{ticker}?fs={period}"
            driver.get(url)

            if not is_us_company(driver):
                print(f"[WARNING] Company {ticker} is not a US company, skipping...")
                skip_non_us_companies = True
                continue

            directory = f"output/{ticker}/{financial_type}"
            try:
                for element_type, element_xpath in xpath_dict.items():
                    statement_df = parse_table(driver, element_xpath)
                    write_to_csv(directory, element_type, statement_df, ticker, mirrored_tickers)
            except Exception as e:
                print(f"Error scraping {ticker}: {e}")


def write_to_csv(directory, element_type, statement_df, ticker, mirrored_tickers):
    os.makedirs(directory, exist_ok=True)
    statement_df.to_csv(f"{directory}/{element_type}.csv")

    if ticker in mirrored_tickers:
        directory = directory.replace(ticker, mirrored_tickers[ticker])
        os.makedirs(directory, exist_ok=True)
        statement_df.to_csv(f"{directory}/{element_type}.csv")


def get_sp500_tickers():
    # fetch s&p 500 tickers from Wikipedia
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    sp500_df = pd.read_html(url)[0]
    return sp500_df["Symbol"].tolist()


def create_chrome_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    return uc.Chrome(options=options)


if __name__ == "__main__":
    driver = create_chrome_driver()
    symbols = get_sp500_tickers()
    period = "annual"

    scrape_data(driver, symbols, period)
