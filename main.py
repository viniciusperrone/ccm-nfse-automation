import argparse
import asyncio
import re

import pandas as pd

from scrapers.belo_horizonte import BeloHorizonteScraper

SCRAPERS = {
    "belohorizonte": BeloHorizonteScraper,
}


def normalize_cnpj(cnpj: str) -> str:
    if pd.isna(cnpj):
        return ""

    cnpj = str(cnpj)

    if cnpj.endswith(".0"):
        cnpj = cnpj[:-2]

    return re.sub(r"\D", "", cnpj)


def normalize_city(city: str) -> str:
    return city.lower().replace(" ", "")


def build_dataframe(input_path: str) -> pd.DataFrame:
    df = pd.read_excel(input_path)

    required_columns = ["CNPJ", "CCM", "MUNICIPIO"]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Colunas obrigatórias não encontradas: {missing_columns}"
        )

    df["CNPJ"] = df["CNPJ"].apply(normalize_cnpj)

    # CCM é um identificador, não um número
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

    if not scraper_class:
        raise ValueError(
            f"Cidade '{input_city}' não suportada"
        )

    city_key = normalize_city(input_city)

    total_processed = 0

    for idx, row in df.iterrows():

        if row["MUNICIPIO"] != city_key:
            continue

        # pula registros já preenchidos
        if pd.notna(row["CCM"]) and str(row["CCM"]).strip():
            continue

        print(
            f"[{idx}] Consultando CNPJ {row['CNPJ']}"
        )

        scraper = scraper_class(
            cnpj=row["CNPJ"]
        )

        try:
            await scraper.run()

            if scraper.ccm_number:
                df.at[idx, "CCM"] = scraper.ccm_number

                print(
                    f"CCM encontrado: {scraper.ccm_number}"
                )

                total_processed += 1

        except Exception as exc:
            print(
                f"Erro ao processar "
                f"CNPJ {row['CNPJ']}: {exc}"
            )

    df.to_excel(input_path, index=False)

    print(
        f"Planilha atualizada com sucesso. "
        f"Registros preenchidos: {total_processed}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        required=True,
        help="Caminho da planilha de entrada"
    )

    parser.add_argument(
        "--city",
        required=True,
        help="Nome da cidade"
    )

    args = parser.parse_args()

    asyncio.run(
        main(
            input_path=args.input,
            input_city=args.city,
        )
    )
