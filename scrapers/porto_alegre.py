from twocaptcha import AsyncTwoCaptcha
from playwright_captcha import CaptchaType, TwoCaptchaSolver, FrameworkType

from base.scraper import BaseScraper
from base.config import Config


class PortoAlegreScraper(BaseScraper):
    CITY = "PORTO_ALEGRE"
    SITEKEY = "6LcJrQcTAAAAABQRp3xSdl6rAqKkxp0XE47zpC1t"

    async def select_company_and_capture_ccm(self):
        pass

    async def has_no_results(self):
        pass

    async def scrape(self):
        await self.page.goto(Config.get_ccm(self.CITY))

        captcha_client = AsyncTwoCaptcha(Config.CAPTCHA_API_KEY)

        balance = await captcha_client.balance()
        print("Saldo:", balance)

        async with TwoCaptchaSolver(
                framework=FrameworkType.PLAYWRIGHT,
                page=self.page,
                async_two_captcha_client=captcha_client
        ) as solver:
            print("Antes do solve")

            result = await solver.solve_captcha(
                captcha_container=self.page,
                captcha_type=CaptchaType.RECAPTCHA_V2,
                sitekey=self.SITEKEY,
                url=self.page.url,
            )

            print(result)

        await self.page.wait_for_timeout(1000)

        await self.page.locator("select.gwt-ListBox").select_option(
            label="CNPJ"
        )

        await self.page.locator("input.gwt-TextBox").first.fill(self.cnpj)

        async with self.page.expect_download() as download_info:
            await self.page.locator(".gwt-CustomButton").first.click()

        download = await download_info.value

        await self.save_document(
            city=self.CITY,
            cnpj=self.cnpj,
            download=download
        )
