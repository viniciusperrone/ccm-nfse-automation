import os
from abc import ABC, abstractmethod

from playwright.async_api import async_playwright, Page
from playwright_captcha import TwoCaptchaSolver, FrameworkType, CaptchaType
from twocaptcha import AsyncTwoCaptcha

from base.config import Config
from utils import get_logger


class BaseScraper(ABC):

    def __init__(self, headless: bool = False, slow_mo: int = 500, **kwargs):
        self.headless = headless
        self.slow_mo = slow_mo

        self.ccm_number = None
        self.access_key = kwargs.get("access_key")
        self.cnpj = kwargs.get("cnpj")

        self.playwright = None
        self.browser = None
        self.page = None

    async def start(self):
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
        )

        self.page = await self.browser.new_page()

    async def close(self):
        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

    @abstractmethod
    async def scrape(self):
        pass

    async def run(self):
        try:
            await self.start()
            await self.scrape()
        finally:
            await self.close()

    async def solve_recaptcha_v2(self, sitekey: str, url: str | None = None):
        captcha_client = AsyncTwoCaptcha(Config.CAPTCHA_API_KEY)

        async with TwoCaptchaSolver(
            framework=FrameworkType.PLAYWRIGHT,
            page=self.page,
            async_two_captcha_client=captcha_client
        ) as solver:

            return await solver.solve_captcha(
                captcha_container=self.page,
                captcha_type=CaptchaType.RECAPTCHA_V2,
                sitekey=sitekey,
                url=url or self.page.url,
            )

    async def get_hcaptcha_sitekey(self) -> str:
        locator = self.page.locator(".h-captcha").first

        sitekey = await locator.get_attribute(
            "data-sitekey"
        )

        if not sitekey:
            raise ValueError(
                "Sitekey do hCaptcha não encontrada."
            )

        return sitekey

    async def solve_hcaptcha(
            self,
            sitekey: str,
            url: str | None = None,
    ):
        captcha_client = AsyncTwoCaptcha(
            Config.CAPTCHA_API_KEY
        )

        result = await captcha_client.hcaptcha(
            sitekey=sitekey,
            url=url or self.page.url,
        )

        token = result["code"]

        await self.page.evaluate(
            """
            (token) => {

                document
                    .querySelectorAll('[name="h-captcha-response"]')
                    .forEach(el => {
                        el.value = token;
                        el.innerHTML = token;
                    });

                document
                    .querySelectorAll('[name="g-recaptcha-response"]')
                    .forEach(el => {
                        el.value = token;
                        el.innerHTML = token;
                    });

            }
            """,
            token
        )

    async def save_document(self, city: str, filename: str, download):
        os.makedirs("outputs", exist_ok=True)

        folder = os.path.join("outputs", city.lower(), self.cnpj)

        os.makedirs(folder, exist_ok=True)

        file_path = os.path.join(folder, f"{filename}.pdf")

        await download.save_as(file_path)

        logger = get_logger("scrapers.base.save_document")

        logger.info(f"Arquivo salvo em: {file_path}")


class NFSeScraper(BaseScraper):
    """
    Classe para consulta pública de NFS-e.

    URL:
    https://www.nfse.gov.br/consultapublica
    """
    URL = "https://www.nfse.gov.br/consultapublica"
    ACCESS_KEY = "31062002228203865000174000000000002426013942565090"
    DOCUMENT = "28203865000174"

    async def scrape(self):
        await self.page.goto(self.URL)

        await self.page.wait_for_timeout(1000)

        sitekey = await self.get_hcaptcha_sitekey()

        await self.solve_hcaptcha(sitekey=sitekey)

        await self.page.locator("#ChaveAcesso").fill(self.ACCESS_KEY)

        await self.page.pause()

        await self.page.get_by_role("button", name="Consultar").click()

        link = self.page.locator(
            'a[href*="/ConsultaPublica/Download/DANFSe"]'
        ).first

        await link.wait_for(state="visible", timeout=30000)

        async with self.page.expect_download() as download_info:
            await link.click()

        download = await download_info.value

        self.cnpj = self.DOCUMENT

        await self.save_document(
            city="BELO_HORIZONTE",
            filename="Nota",
            download=download
        )
