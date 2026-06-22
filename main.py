import argparse
import asyncio
import logging

import pandas as pd

from scrapers.belo_horizonte import BeloHorizonteScraper
from scrapers.rio_de_janeiro import RioDeJaneiroScraper
from scrapers.porto_alegre import PortoAlegreScraper


SCRAPERS = {
    "belohorizonte": BeloHorizonteScraper,
    "riodejaneiro": RioDeJaneiroScraper,
    "portoalegre": PortoAlegreScraper,
}

def setup_logger(log_file: str = "scrapper.log") -> logging.Logger:
    logger = logging.getLogger("scrapper")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def normalize_city(city: str) -> str:
    return city.lower().replace(" ", "")


def build_dataframe(input_path: str) -> pd.DataFrame:
    df = pd.read_excel(
        input_path,
        dtype={
            "CNPJ": str,
            "CCM": str,
            "MUNICIPIO": str,
        }
    )

    df["CNPJ"] = (
        df["CNPJ"]
        .astype(str)
        .str.replace(r"\D", "", regex=True)
        .str.zfill(14)
    )

    df["MUNICIPIO"] = (
        df["MUNICIPIO"]
        .astype(str)
        .str.lower()
        .str.replace(r"\s+", "", regex=True)
    )

    return df


async def main(input_path: str, input_city: str):
    logger = setup_logger()

    logger.info("Iniciando processo")
    logger.info(f"Arquivo: {input_path}")

    df = build_dataframe(input_path)

    scraper_class = SCRAPERS.get(input_city.lower())

    if not scraper_class:
        logger.error(f"Cidade '{input_city}' não suportada")
        raise ValueError(f"Cidade '{input_city}' não suportada")

    city_key = normalize_city(input_city)

    total_processed = 0

    for idx, row in df.iterrows():

        if row["MUNICIPIO"] != city_key:
            continue

        if pd.notna(row["CCM"]) and str(row["CCM"]).strip():
            continue

        logger.info(f"[{idx}] Consultando CNPJ {row['CNPJ']}")

        scraper = scraper_class(cnpj=row["CNPJ"])

        try:
            await scraper.run()

            if scraper.ccm_number:
                df.at[idx, "CCM"] = scraper.ccm_number
                total_processed += 1

                logger.info(f"[{idx}] CCM encontrado: {scraper.ccm_number}")
            else:
                logger.warning(f"[{idx}] CCM não encontrado para {row['CNPJ']}")

        except Exception as exc:
            logger.error(
                f"[{idx}] Erro ao processar CNPJ {row['CNPJ']}: {exc}"
            )

    df.to_excel(input_path, index=False)

    logger.info(
        f"Finalizado. Registros preenchidos: {total_processed}"
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
