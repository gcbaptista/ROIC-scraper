import os

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

# Constants for XPath expressions
INCOME_STATEMENT_XPATH = "/html/body/div[1]/div[2]/div[2]/div[2]/div/div"
BALANCE_SHEET_XPATH = "/html/body/div[1]/div[2]/div[2]/div[3]/div/div"
CASH_FLOW_XPATH = "/html/body/div[1]/div[2]/div[2]/div[4]/div/div"
STATEMENT_XPATHS = {
    "income": INCOME_STATEMENT_XPATH,
    "balance_sheet": BALANCE_SHEET_XPATH,
    "cash_flow": CASH_FLOW_XPATH,
}


def get_children_elements(element: WebElement):
    return element.find_elements(By.XPATH, f"./*")


def get_years_from_table_header(table_header: WebElement):
    years = []
    for column in get_children_elements(table_header):
        if column == get_children_elements(table_header)[0]:
            continue

        year = column.text.replace(" Y", "")

        if year == "TTM" or not year.isdigit():
            continue

        years.append(year)
    return years


def parse_statement(driver, statement_xpath):
    years = []
    metrics_names = []
    data = []

    statement_table = driver.find_element(By.XPATH, statement_xpath)
    (table_header, table_rows_frame) = get_children_elements(statement_table)

    years = get_years_from_table_header(table_header)

    rows_elements = get_children_elements(table_rows_frame)

    for row in rows_elements:
        metrics_values = []
        columns = get_children_elements(row)
        metric_name = columns[0].text

        metrics_names.append(metric_name)

        for column in columns[1:]:
            metric_value = column.text.replace(",", "")

            if metric_value == "- -":
                metric_value = "0"

            if metric_value == '12345' or metric_value == '':
                continue

            metrics_values.append(metric_value)

        data.append(metrics_values)

    dataframe = pd.DataFrame(data=data, columns=years, index=metrics_names)
    return dataframe


def scrape_financial_data(tickers, period):
    for ticker in tickers:
        print(f"Scraping {ticker} financial data...")
        directory = f"output/{ticker}"
        # If directory already exists, skip; else, create it
        if os.path.exists(directory):
            print(f"Directory {directory} already exists, skipping...")
            continue

        driver = webdriver.Chrome()

        url = f"https://roic.ai/financials/{ticker}?fs={period}"
        driver.get(url)

        try:
            for statement_type, statement_xpath in STATEMENT_XPATHS.items():
                statement_df = parse_statement(driver, statement_xpath)
                os.makedirs(directory, exist_ok=True)
                statement_df.to_csv(f"{directory}/{statement_type}_statement.csv")
        except Exception as e:
            print(f"Error scraping {ticker}: {e}")
        finally:
            driver.close()


def get_sp500_tickers():
    # fetch s&p 500 tickers from Wikipedia
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    sp500_df = pd.read_html(url)[0]
    return sp500_df["Symbol"].tolist()


if __name__ == "__main__":
    symbols = get_sp500_tickers()
    scrape_financial_data(symbols, "annual")
