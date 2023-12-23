from .web_search import asearch_ddg
import asyncio
from urllib.parse import urljoin, urlparse, urlunparse
from playwright.async_api import async_playwright
from .file_utils import write_file
import difflib
from collections import deque
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import json

class WebCrawler:
    def __init__(self, keywords, max_concurrent=3, url_list=[], dump_to_file=False):
        self.keywords = keywords
        self.max_concurrent = max_concurrent
        self.url_list = url_list
        self.visited = set()
        self.url_queue = deque()
        self.text_content = []
        self.dump_to_file = dump_to_file

    def start_crawling(self):
        # Create a new loop in a new thread and run the async method there
        with ThreadPoolExecutor() as executor:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            future = executor.submit(loop.run_until_complete, self.start_crawling_async())
            return future.result()
    
    async def start_crawling_async(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            if not self.url_list:
                await self.populate_initial_urls()
            else:
                for url in self.url_list:
                    base_url = self.get_base_url(url)
                    self.url_queue.append((url, base_url))
            await self.process_queue(browser)
            if self.dump_to_file:
                now = datetime.now()
                timestamp = now.strftime("%d-%m-%Y_%H-%M-%S")
                write_file(f"{str(timestamp)}-crawl-result.txt", json.dumps(self.text_content))
            return self.text_content

    async def populate_initial_urls(self):
        search_results = await asearch_ddg("Machine learning tutorial", num_results=10)
        for result in search_results:
            url = result['href']
            base_url = self.get_base_url(url)
            self.url_queue.append((url, base_url))

    async def process_queue(self, browser):
        tasks = []
        while self.url_queue:
            while self.url_queue and len(tasks) < self.max_concurrent:
                url, base_url = self.url_queue.popleft()
                task = asyncio.create_task(self.process_url(browser, url, base_url))
                tasks.append(task)

            if tasks:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                tasks = list(pending)

    async def process_url(self, browser, url, base_url):
        if url in self.visited:
            return
        self.visited.add(url)

        try:
            page = await browser.new_page()
            print("Visiting URL: ", url)
            await page.goto(url, timeout=30000)
            
            content = await page.inner_text('body', timeout=5000)
            self.text_content.append(content[:10000])
            print(f"Fetched content of URL {url}")

            links = await page.query_selector_all('a')
            for link in links:
                await self.process_link(page, link, base_url)

            await page.close()
        except Exception as e:
            print(f"An error occurred while fetching the content from {url}: {e}")

    async def process_link(self, page, link, base_url):
        link_text, href = await self.extract_link_details(page, link)

        if self.should_process_link(href, link_text):
            full_url = self.construct_full_url(href, base_url)
            normalized_full_url = self.normalize_url(full_url)

            if self.is_new_and_relevant_link(normalized_full_url, base_url, link_text):
                print(f"Queueing link: {normalized_full_url}")
                self.url_queue.append((normalized_full_url, base_url))

    async def extract_link_details(self, page, link):
        link_text = await link.inner_text()
        href = await self.get_href(page, link)
        return link_text, href

    def should_process_link(self, href, link_text):
        return href and not href.startswith("#") #and self.efficient_filter(link_text)

    def is_new_and_relevant_link(self, url, base_url, link_text):
        return url not in self.visited and self.same_domain(base_url, url) and self.is_similar(link_text)

    @staticmethod
    def construct_full_url(href, base_url):
        return href if href.startswith("http") else urljoin(base_url, href)
    
    @staticmethod
    def get_base_url(url):
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"

    @staticmethod
    def normalize_url(url):
        parsed_url = urlparse(url)
        return urlunparse(parsed_url._replace(query=""))

    @staticmethod
    async def get_href(page, element):
        if str(type(element)).startswith("<class 'playwright._impl._js_handle.JSHandle'>"):
            return await page.evaluate('element => element.getAttribute("href")', element)
        return await element.get_attribute('href')

    @staticmethod
    def same_domain(url1, url2):
        return urlparse(url1).netloc == urlparse(url2).netloc
    
    def efficient_filter(self, link):
        # Simple keyword matching
        if any(keyword in link for keyword in self.keywords):
            return True
        # Add other simple checks here
        return False
    
    def filter_links(self, links):
        return [link for link in links if self.efficient_filter(link)]

    def is_similar(self, link_text):
        return difflib.SequenceMatcher(None, link_text.lower(), self.keywords.lower()).ratio() > 0.6


