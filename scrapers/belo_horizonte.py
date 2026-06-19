from base.scraper import BaseScraper
from base.config import Config


class BeloHorizonteScraper(BaseScraper):
    CITY = "BELO_HORIZONTE"

    async def scrape(self):
        await self.page.goto(Config.get_ccm(self.CITY))

        await self.page.locator(
            '[id="corpo:formulario:identificador"]'
        ).fill("28203865000174")

        await self.page.pause()
