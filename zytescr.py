Okay, here's how to adapt the provided script to run as a Scrapy spider within Scrapy Cloud (which is part of Zyte), along with explanations and best practices:

**1. Project Structure:**

Your Scrapy project should have the following basic structure:

```
my_pdf_downloader/
├── scrapy.cfg       # Scrapy configuration file
└── my_pdf_downloader/
    ├── __init__.py
    ├── items.py      # Define your Scrapy items (optional, but good practice)
    ├── middlewares.py # (optional)
    ├── pipelines.py  # (optional, but recommended for handling downloaded files)
    ├── settings.py   # Scrapy settings (VERY IMPORTANT)
    └── spiders/
        ├── __init__.py
        └── pdf_spider.py  # Your spider code (adapted from the original script)
```

**2. `pdf_spider.py` (Your Spider):**

This is where you'll adapt the core logic of the original script into a Scrapy spider.  Here's the crucial transformation:

```python
import scrapy
import json
import os
from hashlib import sha256
from scrapy.exceptions import CloseSpider  # Import CloseSpider
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from urllib.parse import urljoin  # Import urljoin

class PdfSpider(scrapy.Spider):
    name = "pdf_spider"  # The name of your spider (used by Scrapy Cloud)
    allowed_domains = ["example.gov"]  # Replace with the actual domain
    start_urls = ["https://www.example.gov/documents"]  # Replace with the starting URL

    # --- Configuration (Moved to settings.py) ---
    # These are now handled in settings.py for better organization
    # ZYTE_API_KEY = ...
    # PDF_DOWNLOAD_DIR = ...
    # STATE_FILE = ...

    def __init__(self, *args, **kwargs):
        super(PdfSpider, self).__init__(*args, **kwargs)
        self.state_file = os.path.join(os.getcwd(), 'state.json')  # Use absolute path
        self.download_dir = os.path.join(os.getcwd(), self.settings.get('PDF_DOWNLOAD_DIR', 'downloaded_pdfs'))
        os.makedirs(self.download_dir, exist_ok=True) #ensure the download directory exists
        self.downloaded_hashes = self.load_state()


    def load_state(self):
        """Loads the state (list of downloaded PDF hashes) from the state file."""
        try:
            with open(self.state_file, "r") as f:
                return json.load(f).get("downloaded_pdfs", []) # get downloaded_pdfs, default to empty list
        except FileNotFoundError:
            return []  # Initialize with an empty list if file doesn't exist

    def save_state(self):
        """Saves the state (list of downloaded PDF hashes) to the state file."""
        state = {"downloaded_pdfs": self.downloaded_hashes} #create the dictionary for the json
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=4)


    def parse(self, response):
        """
        This is the main parsing method, called after the initial request.
        It extracts PDF links and yields requests for each PDF.
        """
        # Use a more robust PDF link extraction (as in the previous improved script)
        pdf_links = response.xpath('//a[contains(@href, ".pdf")]/@href').getall()

         # Make absolute URLS and yield requests.
        for link in pdf_links:
            absolute_url = response.urljoin(link)
            yield scrapy.Request(absolute_url, callback=self.parse_pdf, errback=self.errback_http)

    def parse_pdf(self, response):
        """
        Handles the response from a PDF URL.  Checks if it's been downloaded,
        and if not, yields a dictionary to trigger the FilesPipeline.
        """
        if response.status == 200 and response.headers.get('Content-Type') == b'application/pdf':
            filename = os.path.basename(response.url)
            filepath = os.path.join(self.download_dir, filename)

            with open(filepath, 'wb') as f:
                f.write(response.body)

            file_hash = self.hash_pdf(filepath)

            if file_hash not in self.downloaded_hashes:
                self.downloaded_hashes.append(file_hash)
                self.save_state()
                self.logger.info(f"Downloaded new PDF: {filename}")  # Use Scrapy's logger

                yield {  # Yield a dictionary for the FilesPipeline
                    'file_urls': [response.url],
                    'files': [  # This is needed by FilesPipeline
                        {
                            'url': response.url,
                            'path': filename,  # This is the relative path within FILES_STORE
                            'checksum': file_hash, # Use SHA256 hash
                        }
                    ]
                }
            else:
                self.logger.info(f"Skipping already downloaded PDF: {filename}")
        else:
            self.logger.warning(f"Received non-PDF response or error for {response.url}: Status {response.status}, Content-Type {response.headers.get('Content-Type')}")

    def hash_pdf(self, filename):
        """Calculates the SHA256 hash of a PDF file."""
        hasher = sha256()
        with open(filename, "rb") as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    def errback_http(self, failure):
        # log all failures
        self.logger.error(repr(failure))

        # in case you want to do something special for some errors,
        # you may need the failure's type:

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)
```

**3. `settings.py` (Crucial Settings):**

This file is *essential* for configuring your Scrapy project, especially for Scrapy Cloud.  Here's a well-structured `settings.py`:

```python
BOT_NAME = 'my_pdf_downloader'  # Your project name

SPIDER_MODULES = ['my_pdf_downloader.spiders']
NEWSPIDER_MODULE = 'my_pdf_downloader.spiders'

# --- Zyte API and Scrapy Cloud Settings ---

# Enable Zyte API (Smart Proxy Manager) - VERY IMPORTANT
ZYTE_API_KEY = os.environ.get("ZYTE_API_KEY")  # Get from environment variable
ZYTE_API_ENABLED = True  # Enable Zyte API
ZYTE_API_TRANSPARENT_MODE = True # enables Zyte API for all requests

# --- File Download Settings ---

# Enable the built-in FilesPipeline (for downloading files efficiently)
ITEM_PIPELINES = {
    'scrapy.pipelines.files.FilesPipeline': 1,  # Enable FilesPipeline
}

# Specify the directory to store downloaded files (relative to project root)
FILES_STORE = 'downloaded_pdfs'
PDF_DOWNLOAD_DIR = 'downloaded_pdfs' #used in spider

# --- State File ---
STATE_FILE = 'state.json'

# --- Crawl Behavior ---

# Be polite and respect robots.txt
ROBOTSTXT_OBEY = False  # Set to False if you're sure you can ignore robots.txt

# Configure maximum concurrent requests (adjust based on your Zyte plan)
CONCURRENT_REQUESTS = 16  # Start with a reasonable value

# Configure a delay between requests (to avoid overloading the server)
DOWNLOAD_DELAY = 1  # Add a delay of 1 second (adjust as needed)

# --- Logging ---
LOG_LEVEL = 'INFO'  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)


# --- Error Handling and Retries ---

# Retry failed requests