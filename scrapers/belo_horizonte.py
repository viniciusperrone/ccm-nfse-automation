from base.scraper import BaseScraper
from base.config import Config


class BeloHorizonteScraper(BaseScraper):
    CITY = "BELO_HORIZONTE"

    async def has_no_results(self) -> bool:
        return await self.page.locator(
            "text=Nenhum registro encontrado"
        ).count() > 0

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

        await self.waiting_human_interact()

        await self.page.locator(
            '[id="corpo:formulario:botaoAcaoPesquisar"]'
        ).click()

        await self.page.wait_for_timeout(1000)

        if await self.has_no_results():
            self.logger.warning(f"Nenhum registro encontrado: {self.cnpj}")
            return

        await self.select_company_and_capture_ccm()

    async def download_ccm(self):
        async with self.page.expect_download() as download_info:
            await self.page.locator(
                '[id="corpo:formulario:botaoAcaoEmiteRelatorio"]'
            ).click()

        return await download_info.value
