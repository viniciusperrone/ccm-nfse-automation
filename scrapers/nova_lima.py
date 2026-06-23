from base.scraper import BaseScraper

class NovaLimaScraper(BaseScraper):
    CITY = "NOVA_LIMA"

    async def scrape(self):
        self.logger.warning(
            "Consulta de CCM para Nova Lima indisponível"
        )
        return None

    async def download_ccm(self):
        return None
