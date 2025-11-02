"""Quick test script to run the sitemap spider"""
import sys
import os

# Add project root to path
sys.path.insert(0, r'C:\CarScout-AI')

# Change to scrapy project directory
os.chdir(r'C:\CarScout-AI\workers\scrape')

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

settings = get_project_settings()
settings.set('CLOSESPIDER_ITEMCOUNT', 3)
settings.set('LOG_LEVEL', 'INFO')

process = CrawlerProcess(settings)
process.crawl('mobile_bg_sitemap')
process.start()
