import os

import pandas as pd
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


def get_children_elements(element: WebElement):
    return element.find_elements(By.XPATH, f"./*")


def get_years_from_table_header(table_header: WebElement):
    years = []
    for column in get_children_elements(table_header):
        # skip the first column
        if column == get_children_elements(table_header)[0]:
            continue

        year = column.text.replace(" Y", "")

        if year == "TTM" or not year.isdigit():
            continue

        years.append(year)
    return years


def parse_income_statement(driver: webdriver.Chrome):
    years = []
    metrics_names = []
    data = []

    income_statement_table = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div[2]/div[2]/div/div")

    (table_header, table_rows_frame) = get_children_elements(income_statement_table)

    years = get_years_from_table_header(table_header)

    rows_elements = get_children_elements(table_rows_frame)

    for row in rows_elements:
        metrics_values = []
        columns = get_children_elements(row)
        metric_name = columns[0].text

        metrics_names.append(metric_name)

        # iterate over columns by skip the first
        for column in columns[1:]:
            metric_value = column.text.replace(",", "")

            if metric_value == "- -":
                metric_value = "0"

            # If metric value is not a number nor it is '12,345' then skip it.
            if metric_value == '12345' or metric_value == '':
                continue

            metrics_values.append(metric_value)

        data.append(metrics_values)

    dataframe = pd.DataFrame(data=data, columns=years, index=metrics_names)

    return dataframe


def scrape_financial_data(ticker, period):
    """Parses financial data from roic.ai for the given ticker and period.

  Args:
    ticker: The stock ticker symbol.
    period: The financial period, such as "annual" or "quarterly".

  Returns:
    A Pandas DataFrame containing the financial data.
  """

    driver = webdriver.Chrome()
    url = f"https://roic.ai/financials/{ticker}?fs={period}"
    driver.get(url)

    # Parse the income statement.
    dataframe = parse_income_statement(driver)

    directory = f"output/{ticker}"

    if not os.path.exists(directory):
        os.makedirs(directory)

    dataframe.to_csv(f"{directory}/income_statement.csv")


if __name__ == "__main__":
    ticker = "AAPL"

    # Parse the financial data for Apple for the annual period.
    scrape_financial_data(ticker, "annual")
