import argparse
import asyncio

from scrapers.belo_horizonte import BeloHorizonteScraper

SCRAPERS = {
    "belohorizonte": BeloHorizonteScraper,
}


async def main(city: str):
    scraper_class = SCRAPERS.get(city.lower())

    if not scraper_class:
        raise ValueError(
            f"Cidade {city} não suportada"
        )

    scraper = scraper_class()
    await scraper.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--city",
        required=True,
        help="Nome da cidade"
    )

    args = parser.parse_args()

    asyncio.run(main(args.city))