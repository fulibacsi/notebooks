"""Download the data of chapter XI, and save it into the data folder.

- data/population.csv: the total population of every country, from the
  World Bank (indicator SP.POP.TOTL).
- data/alcohol.csv: the recorded alcohol consumption per person aged 15 or
  over, in litres of pure alcohol, by type of drink, for the countries of the
  WHO Europe region. It comes from the data API of the World Health
  Organization (WHO), the Global Health Observatory (indicator SA_0000001400).

Run it from the command line, in this folder:

    python python101_11_data_scraping.py

It overwrites both files with the latest data. The exercises of chapter XI
(and the asserts in its solutions) were written for the data of November
2026, so check them after a new download.
"""

import csv
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

from helpers import download_json

DATA = Path(__file__).parent / "data"

POPULATION_URL = "https://api.worldbank.org/v2/en/indicator/SP.POP.TOTL?downloadformat=csv"
WHO_API = "https://ghoapi.azureedge.net/api/"
ALCOHOL = "SA_0000001400"
EUROPE = "EUR"


def download_population(path):
    """Download the World Bank's population table and save it as a csv file.

    The World Bank sends a zip file. The table in it has four lines of notes
    above the column names: we leave those out, so that pandas can read the
    file without any extra settings.

    Arguments:
        path: where to save the csv file.

    Returns:
        The number of rows saved (countries and groups of countries).
    """
    response = requests.get(POPULATION_URL, timeout=60)
    response.raise_for_status()

    # the zip holds three csv files - the table is the one whose name starts with API_
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    for name in archive.namelist():
        if name.startswith("API_"):
            table = archive.read(name).decode("utf-8-sig")

    lines = table.replace("\r\n", "\n").split("\n")

    # skip the notes: the table starts at the line with the column names
    start = 0
    while not lines[start].startswith('"Country Name"'):
        start = start + 1

    with open(path, "w", encoding="utf-8", newline="") as file:
        file.write("\n".join(lines[start:]))

    rows = [line for line in lines[start + 1:] if line]
    return len(rows)


def who_names(dimension):
    """Download the names the WHO uses for the codes of a dimension.

    Arguments:
        dimension: the name of the dimension, for example "COUNTRY".

    Returns:
        A dictionary that gives the name for each code,
        for example {"HUN": "Hungary", "FRA": "France", ...}.
    """
    names = {}
    for item in download_json(WHO_API + "DIMENSION/" + dimension + "/DimensionValues")["value"]:
        names[item["Code"]] = item["Title"]
    return names


def download_alcohol(path, region=EUROPE):
    """Download the WHO's alcohol consumption data and save it as a csv file.

    There is one row for every country, year and type of drink, with the
    WHO's own names for the countries and the drinks.

    Arguments:
        path: where to save the csv file.
        region: the code of the WHO region to keep. "EUR" is the WHO Europe region.

    Returns:
        The number of rows saved.
    """
    indicator = download_json(WHO_API + "Indicator?$filter=IndicatorCode eq '" + ALCOHOL + "'")["value"][0]
    countries = who_names("COUNTRY")
    drinks = who_names("ALCOHOLTYPE")

    rows = []
    for value in download_json(WHO_API + ALCOHOL + "?$filter=ParentLocationCode eq '" + region + "'")["value"]:
        # two decimals, like 12.50 - and an empty cell where the WHO has no number
        if value["NumericValue"] is None:
            amount = ""
        else:
            amount = f"{value['NumericValue']:.2f}"

        rows.append({
            "Indicator": indicator["IndicatorName"],
            "Year": value["TimeDim"],
            "WHO region": value["ParentLocation"],
            "Country Code": value["SpatialDim"],
            "Country": countries[value["SpatialDim"]],
            "Beverage Types": drinks[value["Dim1"]],
            "Display Value": amount,
        })

    table = pd.DataFrame(rows).sort_values(["Country", "Year", "Beverage Types"])
    table.to_csv(path, index=False, quoting=csv.QUOTE_ALL, lineterminator="\n")
    return len(table)


# this part only runs when the file is started as a script, not when it is imported
if __name__ == "__main__":
    print("population.csv:", download_population(DATA / "population.csv"), "rows")
    print("alcohol.csv:   ", download_alcohol(DATA / "alcohol.csv"), "rows")
