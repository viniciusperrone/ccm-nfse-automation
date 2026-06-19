from base.scraper import BaseScraper
from base.config import Config


class BeloHorizonteScraper(BaseScraper):

    def __init__(self):
        self.ccm_url = Config.get_ccm("BELO_HORIZONTE")

    async def scrape(self):
        await self.page.goto(self.ccm_url)

        await self.page.locator(
            "#corpo\\:formulario\\:identificador"
        ).fill("28203865000174")

        await self.page.pause()
