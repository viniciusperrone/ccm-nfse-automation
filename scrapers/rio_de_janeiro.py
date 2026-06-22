from base.scraper import BaseScraper
from base.config import Config

"""
1. Mapear as colunas (CNPJ, MUNICIO, CCM, COD. VERIFICACAO)
2. ATUALIZAR CCM
3. Realizar BAIXA CADASTRO MUNICIPAL
4. Realizar BAIXA NFS-e
"""
class RioDeJaneiroScraper(BaseScraper):
    CITY = "RIO_DE_JANEIRO"

    async def select_company_and_capture_ccm(self):
        ccm = await self.page.locator(
            'strong:has-text("Inscrição Municipal:") + span'
        ).inner_text()

        self.ccm_number = ccm.strip()

    async def has_no_results(self):
        return await self.page.get_by_text(
            "Nenhuma inscrição encontrada para o valor informado."
        ).count() > 0

    async def scrape(self):
        await self.page.goto(Config.get_ccm(self.CITY))

        await self.page.locator(
            'input[type="radio"][value="cnpj"]'
        ).check()

        await self.page.locator(
            'input[placeholder="Digite o CNPJ"]'
        ).fill(self.cnpj)

        await self.page.locator(
            'button[type="submit"]'
        ).click()

        await self.page.wait_for_timeout(1000)

        if await self.has_no_results():
            print(f"[WARN] Nenhum registro encontrado: {self.cnpj}")
            return

        await self.page.locator(
            'td[class^="ListaDeInscricoes_linkInscricao"]'
        ).click()

        await self.page.wait_for_timeout(1000)

        await self.select_company_and_capture_ccm()

        async with self.page.expect_download() as download_info:
            await self.page.get_by_role(
                "button",
                name="Imprimir"
            ).click()

        download = await download_info.value

        await self.save_document(
            city=self.CITY,
            cnpj=self.cnpj,
            download=download
        )
