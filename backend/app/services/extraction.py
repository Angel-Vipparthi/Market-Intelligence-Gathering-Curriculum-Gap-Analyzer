from firecrawl import FirecrawlApp
from app.config import settings
import structlog

logger = structlog.get_logger()


class FirecrawlExtractor:
    def __init__(self):
        self.client = FirecrawlApp(api_key=settings.firecrawl_api_key)

    async def extract(self, url: str) -> dict:
        try:
            result = self.client.scrape_url(
                url,
                params={
                    "formats": ["markdown"],
                    "onlyMainContent": True,
                    "waitFor": 3000,
                },
            )
            if not result or not result.get("markdown"):
                raise ValueError("No content extracted from URL")

            metadata = result.get("metadata", {})
            return {
                "content": result["markdown"],
                "title": metadata.get("title", ""),
                "description": metadata.get("description", ""),
                "author": metadata.get("author", ""),
                "published_date": metadata.get("publishedDate", ""),
            }
        except Exception as e:
            logger.error("firecrawl_extraction_failed", url=url, error=str(e))
            raise


class PlaywrightExtractor:
    async def extract(self, url: str) -> dict:
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)

                title = await page.title()
                content = await page.evaluate("() => document.body.innerText")

                await browser.close()

                return {
                    "content": content,
                    "title": title,
                    "description": "",
                    "author": "",
                    "published_date": "",
                }
        except Exception as e:
            logger.error("playwright_extraction_failed", url=url, error=str(e))
            raise


_firecrawl = None
_playwright = None


async def extract_content(url: str) -> dict:
    global _firecrawl, _playwright

    if _firecrawl is None:
        _firecrawl = FirecrawlExtractor()
    if _playwright is None:
        _playwright = PlaywrightExtractor()

    try:
        return await _firecrawl.extract(url)
    except Exception as e:
        logger.warning("firecrawl_failed_trying_playwright", url=url, error=str(e))
        return await _playwright.extract(url)
