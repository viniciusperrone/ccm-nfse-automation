from abc import ABC, abstractmethod

from playwright.async_api import async_playwright


class BaseScraper(ABC):

    def __init__(self, headless: bool = False, slow_mo: int = 500):
        self.headless = headless
        self.slow_mo = slow_mo

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
