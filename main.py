import os
import pandas as pd
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

# Constants for XPath expressions
FINANCIALS_XPATHS = {
    "income": "/html/body/div[1]/div[2]/div[2]/div[2]/div/div",
    "balance_sheet": "/html/body/div[1]/div[2]/div[2]/div[3]/div/div",
    "cash_flow": "/html/body/div[1]/div[2]/div[2]/div[4]/div/div",
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
    data = []

    rows_elements = get_children_elements(table_rows_frame)
    for row in rows_elements:
        columns = get_children_elements(row)
        metric_name = columns[0].text
        metrics_values = []

        for column in columns[1:]:
            metric_value = column.text.replace(",", "")
            if metric_value == "- -" or metric_value == "12345" or metric_value == "":
                metric_value = "0"
            metrics_values.append(metric_value)

        data.append(metrics_values)

    data = [data[i][-10:] for i in range(len(data))]
    dataframe = pd.DataFrame(data=data, columns=years,
                             index=[metric_name for metric_name in get_children_elements(table_rows_frame)])
    return dataframe


def scrape_data(driver, tickers, period, xpath_dict, parent_dir):
    for ticker in tickers:
        print(f"Scraping {parent_dir} of {ticker}...")
        directory = f"output/{parent_dir}/{ticker}"
        if os.path.exists(directory):
            print(f"Directory {directory} already exists, skipping...")
            continue

        url = f"https://roic.ai/{parent_dir}/{ticker}?fs={period}"
        driver.get(url)

        try:
            for element_type, element_xpath in xpath_dict.items():
                statement_df = parse_table(driver, element_xpath)
                os.makedirs(directory, exist_ok=True)
                statement_df.to_csv(f"{directory}/{element_type}_{parent_dir}.csv")
        except Exception as e:
            print(f"Error scraping {ticker}: {e}")


def get_sp500_tickers():
    # fetch s&p 500 tickers from Wikipedia
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    sp500_df = pd.read_html(url)[0]
    return sp500_df["Symbol"].tolist()


if __name__ == "__main__":
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    driver = uc.Chrome(options=options)

    symbols = get_sp500_tickers()
    scrape_data(driver, symbols, "annual", FINANCIALS_XPATHS, "financials")
    scrape_data(driver, symbols, "annual", RATIOS_XPATHS, "ratios")
