from base.scraper import BaseScraper

from config import CCM_BELO_HORIZONTE


class BeloHorizonteScraper(BaseScraper):

    async def scrape(self):
        await self.page.goto(CCM_BELO_HORIZONTE)

        await self.page.locator(
            "#corpo\\:formulario\\:identificador"
        ).fill("28203865000174")

        await self.page.pause()
