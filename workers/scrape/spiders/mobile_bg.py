"""
Mobile.bg spider
"""
import scrapy
from scrapy_playwright.page import PageMethod


class MobileBgSpider(scrapy.Spider):
    name = "mobile_bg"
    allowed_domains = ["mobile.bg"]
    
    custom_settings = {
        "CONCURRENT_REQUESTS": 2,
        "DOWNLOAD_DELAY": 1.0,
        "ROBOTSTXT_OBEY": True,
    }
    
    def start_requests(self):
        """Start scraping latest car listings"""
        # TODO: Implement pagination logic
        url = "https://www.mobile.bg/pcgi/mobile.cgi?act=3&slink=tkqnfd"
        yield scrapy.Request(
            url,
            meta=dict(
                playwright=True,
                playwright_page_methods=[
                    PageMethod("wait_for_selector", ".tablereset"),
                ],
            ),
        )
    
    def parse(self, response):
        """Parse listing page"""
        # TODO: Extract listing URLs
        # TODO: Follow to detail pages
        # TODO: Extract and save to listings_raw
        pass
