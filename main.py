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

def build_dataframe(input_path: str):
    df = pd.read_excel(input_path)

    df = df[["CNPJ", "CCM", "MUNICIPIO"]]

    df["CNPJ"] = df["CNPJ"].apply(normalize_cnpj)

    df["CCM"] = df["CCM"].astype("string")

    df["MUNICIPIO"] = (
        df["MUNICIPIO"]
        .astype(str)
        .str.lower()
        .str.replace(r"\s+", "", regex=True)
    )

    return df

async def main(input_path: str, input_city: str):
    df = build_dataframe(input_path)

    scraper_class = SCRAPERS.get(input_city.lower())

    city_key = normalize_city(input_city)

    for idx, row in df.iterrows():

        if row["MUNICIPIO"] != city_key:
            continue

        scraper = scraper_class(cnpj=row["CNPJ"])

        await scraper.run()

        df.at[idx, "CCM"] = scraper.ccm_number

    output_path = input_path.replace(".xlsx", "_updated.xlsx")
    df.to_excel(output_path, index=False)

    print(f"Arquivo atualizado salvo em: {output_path}")


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
