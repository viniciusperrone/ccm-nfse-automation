import os
import traceback
from abc import ABC, abstractmethod
from typing import Optional

from playwright.async_api import async_playwright

from twocaptcha import AsyncTwoCaptcha
from playwright_captcha import (
    TwoCaptchaSolver,
    FrameworkType,
    CaptchaType,
)

from base.config import Config
from utils import get_logger


class BaseScraper(ABC):

    def __init__(self, cnpj: str, access_key: Optional[str] = None):
        self.cnpj = cnpj
        self.access_key = access_key

        self.ccm_number: Optional[str] = None

        self.playwright = None
        self.browser = None
        self.page = None

        self.logger = get_logger(self.__class__.__name__)

    async def run(self):
        self.logger.info(
            f"START scraper={self.__class__.__name__} cnpj={self.cnpj}"
        )

        try:
            await self.start()

            await self.before_scrape()
            await self.scrape()

            ccm_download = await self.download_ccm()
            if ccm_download:
                await self.save_document(
                    city=getattr(self, "CITY", "UNKNOWN"),
                    filename="CADASTRO_MUNICIPAL",
                    download=ccm_download,
                )
            await self.download_nfse()

            await self.after_scrape()

            self.logger.info(
                f"FINISHED scraper={self.__class__.__name__} cnpj={self.cnpj} ccm={self.ccm_number} nfse={self.access_key}"
            )

        except Exception as exc:
            self.logger.error(
                f"FAILED scraper={self.__class__.__name__} cnpj={self.cnpj} error={exc}"
            )
            self.logger.debug(traceback.format_exc())
            raise

        finally:
            await self.close()

    async def start(self):
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=False,
            slow_mo=500,
        )

        self.page = await self.browser.new_page()

        self.logger.info("Browser started")

    async def close(self):
        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

        self.logger.info("Browser closed")

    async def waiting_human_interact(self):
        self.logger.warning("Necessário interação humana")
        await self.page.pause()

    async def before_scrape(self):
        pass

    @abstractmethod
    async def scrape(self):
        pass

    async def after_scrape(self):
        pass

    @abstractmethod
    async def download_ccm(self):
        pass

    async def download_nfse(self):
        if self.access_key is None:
            self.logger.warning("Cód. de acesso não fornecido")

            return

        self.logger.info(
            f"Iniciando baixa da NFS-e."
            f"Chave: {self.access_key}"
        )

        await self.page.goto(Config.NFSe_URL)

        await self.page.wait_for_timeout(1000)

        sitekey = await self.get_hcaptcha_sitekey()

        await self.solve_hcaptcha(sitekey=sitekey)

        await self.page.locator("#ChaveAcesso").fill(self.access_key)

        await self.page.get_by_role("button", name="Consultar").click()

        await self.page.wait_for_timeout(2000)

        if await self.nfse_not_found():
            self.logger.warning(
                f"NFS-e not found | cnpj={self.cnpj} | access_key={self.access_key}"
            )
            return

        link = self.page.locator(
            'a[href*="/ConsultaPublica/Download/DANFSe"]'
        ).first

        await link.wait_for(state="visible", timeout=30000)

        async with self.page.expect_download() as download_info:
            await link.click()

        download = await download_info.value

        await self.save_document(
            city=getattr(self, "CITY", "UNKNOWN"),
            filename="Nota",
            download=download
        )

    async def nfse_not_found(self) -> bool:
        return await self.page.locator(
            "div.alert-warning"
        ).filter(
            has_text="Nota Fiscal de Serviço inexistente"
        ).count() > 0

    async def solve_recaptcha_v2(self, sitekey: str, url: str | None = None):
        client = AsyncTwoCaptcha(Config.CAPTCHA_API_KEY)

        async with TwoCaptchaSolver(
            framework=FrameworkType.PLAYWRIGHT,
            page=self.page,
            async_two_captcha_client=client,
        ) as solver:

            return await solver.solve_captcha(
                captcha_container=self.page,
                captcha_type=CaptchaType.RECAPTCHA_V2,
                sitekey=sitekey,
                url=url or self.page.url,
            )

    async def solve_hcaptcha(self, sitekey: str, url: str | None = None):
        client = AsyncTwoCaptcha(Config.CAPTCHA_API_KEY, recaptchaTimeout=600)

        result = await client.hcaptcha(
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

    async def get_hcaptcha_sitekey(self) -> str:
        self.logger.info("Capturando sitekey")
        locator = self.page.locator(".h-captcha").first

        sitekey = await locator.get_attribute("data-sitekey")

        if not sitekey:
            raise ValueError("hCaptcha sitekey not found")

        self.logger.info("Sitekey capturado")

        return sitekey

    async def save_document(self, city: str, filename: str, download):
        os.makedirs("outputs", exist_ok=True)

        folder = os.path.join("outputs", city.lower(), self.cnpj)
        os.makedirs(folder, exist_ok=True)

        file_path = os.path.join(folder, f"{filename}.pdf")

        await download.save_as(file_path)

        self.logger.info(f"Saved file: {file_path}")
