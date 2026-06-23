from base.scraper import BaseScraper
from base.config import Config

from utils import get_logger

logger = get_logger("scrapers.porto_alegre")


class PortoAlegreScraper(BaseScraper):
    CITY = "PORTO_ALEGRE"

    async def scrape(self):
        await self.page.goto(Config.get_ccm(self.CITY))

        sitekey = await self.get_recaptcha_v2_sitekey()
        await self.solve_recaptcha_v2(sitekey)

        await self.page.wait_for_timeout(1000)

        await self.page.locator("select.gwt-ListBox").select_option(
            label="CNPJ"
        )

        await self.page.locator("input.gwt-TextBox").first.fill(self.cnpj)

    async def download_ccm(self):
        await self.page.wait_for_timeout(500)

        async with self.page.expect_download() as download_info:
            await self.page.locator(".gwt-CustomButton").first.click()

        return await download_info.value
