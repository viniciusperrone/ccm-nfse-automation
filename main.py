import argparse
import asyncio
import re

import pandas as pd
from collections import defaultdict


from scrapers.belo_horizonte import BeloHorizonteScraper

SCRAPERS = {
    "belohorizonte": BeloHorizonteScraper,
}

def normalize_cnpj(cnpj: str) -> str:
    return re.sub(r"\D", "", str(cnpj))

def normalize_city(city: str):
    return city.lower().replace(" ", "")

def build_data_per_city(input_path: str):
    df = pd.read_excel(input_path)

    df = df[["CNPJ", "CCM", "MUNICIPIO"]]

    df["MUNICIPIO"] = (
        df["MUNICIPIO"]
        .astype(str)
        .str.lower()
        .str.replace(r"\s+", "", regex=True)
    )

    data_per_city = defaultdict(list)

    for row in df.itertuples(index=False):
        data_per_city[row.MUNICIPIO].append({
            "cnpj": str(row.CNPJ).strip(),
            "ccm": row.CCM
        })

    return dict(data_per_city)

def build_data_per_city(input_path: str):
    df = pd.read_excel(input_path)

    df = df[["CNPJ", "CCM", "MUNICIPIO"]]

    df["MUNICIPIO"] = (
        df["MUNICIPIO"]
        .astype(str)
        .str.lower()
        .str.replace(r"\s+", "", regex=True)
    )

    data_per_city = defaultdict(list)

    for row in df.itertuples(index=False):
        data_per_city[row.MUNICIPIO].append({
            "cnpj": normalize_cnpj(str(row.CNPJ)),
            "ccm": row.CCM
        })

    return dict(data_per_city)



async def main(input_path: str, input_city: str):
    scraper_class = SCRAPERS.get(input_city.lower()) if input_city else None

    data_per_city = build_data_per_city(input_path)

    if input_city:
        city_key = normalize_city(input_city)

        city_data = data_per_city.get(city_key, [])

        for item in city_data:
            scraper = scraper_class(cnpj=item["cnpj"])
            await scraper.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        required=True,
        help="Caminho da planilha de entrada"
    )
    parser.add_argument(
        "--city",
        required=False,
        help="Nome da cidade"
    )

    args = parser.parse_args()

    asyncio.run(main(args.input, args.city))
