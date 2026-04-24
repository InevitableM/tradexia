import requests
from bs4 import BeautifulSoup
import pandas as pd


def get_screener_tables(symbol):
    url = f"https://www.screener.in/company/{symbol}/"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    tables = {}

    # Helper function to parse a table
    def parse_table(section_id):
        section = soup.find("section", {"id": section_id})
        if not section:
            return None

        table = section.find("table")
        if not table:
            return None

        headers = [th.text.strip() for th in table.find_all("th")]

        rows = []
        for tr in table.find_all("tr")[1:]:
            cols = [td.text.strip() for td in tr.find_all(["td", "th"])]
            rows.append(cols)

        return pd.DataFrame(rows, columns=headers)

    # Extract different sections
    tables["quarterly"] = parse_table("quarters")
    tables["profit_loss"] = parse_table("profit-loss")
    tables["balance_sheet"] = parse_table("balance-sheet")
    tables["cash_flow"] = parse_table("cash-flow")

    return tables


if __name__ == "__main__":
    data = get_screener_tables("TCS")

    for name, df in data.items():
        print(f"\n==== {name.upper()} ====\n")
        if df is not None:
            print(df.head())
        else:
            print("Not found")