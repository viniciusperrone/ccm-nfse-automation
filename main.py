import asyncio

from playwright.async_api import async_playwright

from config import CCM_BELO_HORIZONTE


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500
        )

        page = await browser.new_page()

        await page.goto(CCM_BELO_HORIZONTE)

        await page.locator("#corpo\\:formulario\\:identificador").fill("28203865000174")

        await page.pause()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())