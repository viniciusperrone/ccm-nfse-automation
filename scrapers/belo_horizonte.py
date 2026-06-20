from base.scraper import BaseScraper
from base.config import Config


class BeloHorizonteScraper(BaseScraper):
    CITY = "BELO_HORIZONTE"

    async def select_company_and_capture_ccm(self):
        row = self.page.locator(
            f'tr:has-text("{self.cnpj}"):has-text("ATIVA")'
        )

        ccm = await row.locator("td:nth-child(2)").inner_text()
        self.ccm_number = ccm.strip()

        await row.locator('input[type="radio"]').click()

    async def scrape(self):
        await self.page.goto(Config.get_ccm(self.CITY))

        await self.page.locator(
            '[id="corpo:formulario:identificador"]'
        ).fill(self.cnpj)

        await self.page.pause()

        await self.page.locator(
            '[id="corpo:formulario:botaoAcaoPesquisar"]'
        ).click()

        await self.select_company_and_capture_ccm()

        async with self.page.expect_download() as download_info:
            await self.page.locator(
                '[id="corpo:formulario:botaoAcaoEmiteRelatorio"]'
            ).click()

        download = await download_info.value

        await self.save_document(
            city=self.CITY,
            cnpj=self.cnpj,
            download=download
        )

        print("CCM capturado:", self.ccm_number)
