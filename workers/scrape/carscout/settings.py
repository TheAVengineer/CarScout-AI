# Scrapy settings for carscout project

BOT_NAME = 'carscout'

SPIDER_MODULES = ['carscout.spiders']
NEWSPIDER_MODULE = 'carscout.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 8

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 1

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware': 543,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler': 800,
}

# Playwright configuration
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Playwright timeout settings (prevent infinite hangs)
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000  # 30 seconds max wait for page load
PLAYWRIGHT_BROWSER_TYPE = 'chromium'
DOWNLOAD_TIMEOUT = 60  # 60 seconds for downloads

# Playwright browser context settings (prevent hangs after timeouts)
PLAYWRIGHT_LAUNCH_OPTIONS = {
    'timeout': 60000,  # 60 seconds to launch browser
}
PLAYWRIGHT_CONTEXTS = {
    'default': {
        'ignore_https_errors': True,
    },
}
PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 1  # Force new context per page to avoid stuck state

# Retry settings (handle failed requests gracefully)
RETRY_ENABLED = True
RETRY_TIMES = 2  # Reduce to 2 retries (was causing extra hangs)
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 404, 0]  # Add 0 for timeout errors
RETRY_BACKOFF_MULTIPLIER = 2

# Close idle browser/context to prevent resource leaks
PLAYWRIGHT_ABORT_REQUEST = lambda req: req.resource_type in ('image', 'stylesheet', 'font', 'media')

# Configure item pipelines
ITEM_PIPELINES = {
    'carscout.pipelines.CarScoutPipeline': 300,
}

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
FEED_EXPORT_ENCODING = 'utf-8'

# Logging
LOG_LEVEL = 'INFO'
