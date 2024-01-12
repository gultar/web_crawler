from .web_search import asearch_ddg
import asyncio
from urllib.parse import urljoin, urlparse, urlunparse
from playwright.async_api import async_playwright
from .file_utils import write_file
import difflib
from collections import deque
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Set, Deque, Any
import json


class WebCrawler:
    def __init__(
            self, 
            keywords: List[str] = ["*"], # The asterisk is used to fetch all links within the page, without filtering
            max_concurrent: int = 3, 
            url_list: List[str] = [],
            base_url_list: List[str] = [],
            dump_to_file: bool = False, 
            max_retries: int = 3, 
            retry_delay: int = 5,
            max_visits: int = 200,
            search_query:str = "",
            nb_of_initial_search_results:int = 10,
            delay:int = 0
        ) -> None:
        self.keywords: List[str] = keywords
        self.max_concurrent: int = max_concurrent
        self.max_visits: int = max_visits
        self.nb_of_visits:int = 0##https://vitrinelinguistique.oqlf.gouv.qc.ca/banque-de-depannage-linguistique
        self.url_list: List[str] = url_list
        # base_url_list is used to block the depth of search at a certain route
        # say, https://example.com is the target website, but you're only interested in https://example.com/target/pages/
        # the crawler will limit its search to this route, and will not visit pages further up.
        self.base_url_list: List[str] = base_url_list  
        self.discovered: Set[str] = set()
        self.url_queue: Deque[Tuple[str, str]] = deque()
        self.all_urls: Set[str] = set()
        self.text_content: List[str] = []
        self.dump_to_file: bool = dump_to_file
        self.max_retries: int = max_retries
        self.retry_delay: int = retry_delay
        self.search_query = search_query
        self.nb_of_initial_search_results = nb_of_initial_search_results
        self.history = {}
        self.content_limit = 20000
        self.delay = delay

    def start_crawling(self, keywords: List[str] = [], urls_to_focus_on: List[str] = []) -> List[str]:
        loop = None
        try:
            # Create a new loop in a new thread and run the async method there
            if len(urls_to_focus_on) != 0:
                self.url_list = urls_to_focus_on

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            with ThreadPoolExecutor() as executor:
                future = executor.submit(loop.run_until_complete, self.start_crawling_async(keywords))
                return future.result()
        except KeyboardInterrupt:
            print("KeyboardInterrupt caught, stopping the crawler.")
        finally:
            if loop:
                loop.close()
                
    
    async def start_crawling_async(self, keywords: List[str] = []) -> List[str]:
        browser = None
        try:
            # Start an asynchronous context using Playwright
            async with async_playwright() as p:
                # Launch the browser (Chromium) in non-headless mode (visible browser)
                browser = await p.chromium.launch(headless=False)

                # Redefine the list of keywords used to determine the relevancy of links in the page
                if len(keywords) != 0:
                    self.keywords = keywords

                if not self.search_query and not self.url_list:
                    raise "You need to provide either a list of URLs or a Search query to populate the initial list of URLs"

                # If the URL list is empty, populate initial URLs using the provided keywords
                if not self.url_list:
                    await self.populate_initial_urls()
                else:
                    # If URL list is provided, add each URL and its base URL to the queue
                    for url in self.url_list:
                        base_url = self.get_base_url(url)
                        if url in self.base_url_list:
                            base_url = url
                        self.url_queue.append((url, base_url))

                # Process the queue of URLs to visit and scrape
                await self.process_queue(browser)

                # If enabled, dump the collected text content to a file
                if self.dump_to_file:
                    now = datetime.now()
                    timestamp = now.strftime("%d-%m-%Y_%Hh%Mm%Ss")
                    # Write the text content to a file with a timestamped filename
                    write_file(f"{str(timestamp)}-crawl-result.txt", json.dumps(self.text_content))

                # Return the collected text content from the crawled pages
                return self.text_content

        except KeyboardInterrupt:
            print("KeyboardInterrupt caught in async, stopping the crawler.")
        finally:
            if browser:
                await browser.close()
                

    async def populate_initial_urls(self) -> None:
        search_results = await asearch_ddg(self.search_query, num_results=self.nb_of_initial_search_results)
        for result in search_results:
            url = result['href']
            base_url = self.get_base_url(url)
            if url in self.base_url_list:
                base_url = url
            self.url_queue.append((url, base_url))

    async def process_queue(self, browser: Any) -> None:
        tasks = []
        try:
            while self.url_queue:
                while self.url_queue and len(tasks) < self.max_concurrent:
                    url, base_url = self.url_queue.popleft()
                    task = asyncio.create_task(self.process_url(browser, url, base_url))
                    tasks.append(task)

                if tasks:
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    tasks = list(pending)
        except Exception as e:
            print(f"An error occurred while processing Queue: {e}")
        finally:
            if browser:
                await browser.close()

    async def process_url(self, browser: Any, url: str, base_url: str) -> None:
        
        retry_count = 0
        while retry_count <= self.max_retries:
            try:
                

                if self.nb_of_visits >= self.max_visits:
                    print("Reached max nb of pages")
                    break  # Break out of the loop, and don't visit new websites after


                page = await browser.new_page()
                print(f"Visiting URL: {url}")
                await page.goto(url, timeout=30000)
                
                content = await page.inner_text('body', timeout=30000)

                self.nb_of_visits += 1

                # Both methods need to be implemented in case the user wants to use or transform
                # the page's content or the page's HTML code
                self.handle_html_page(page)
                self.handle_innertext(content)

                content_of_page = {
                    "url":url,
                    "content":content[:self.content_limit]
                }

                self.text_content.append(json.dumps(content_of_page))
                print(f"Fetched content of URL {url}")

                # you could generate a summary to be passed to an LLM for analysis
                # or you could dump the content of each page in a separate file
                # generate summary

                self.history[url] = { "text":content }

                links = await page.query_selector_all('a')
                relevant_links = await self.find_relevant_links(links, base_url, page)

                for link in relevant_links:
                    await self.process_relevant_link(link, base_url)
                    
                await page.close()
                break
            except Exception as e:
                print(e)
                print(f"Attempt {retry_count + 1}: Error fetching {url}: {e}")
                retry_count += 1
                if retry_count > self.max_retries:
                    print(f"Failed to fetch {url} after {self.max_retries} attempts.")
                    break
                else:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)

    async def find_relevant_links(self, links, base_url: str, page) -> List[str]:
        relevant_links = []
        for link in links:
            link_text, href = await self.extract_link_details(page, link)

            if self.is_relevant_link(link_text, href) and self.should_process_link(href):
                full_url = self.construct_full_url(href, base_url)
                normalized_full_url = self.normalize_url(full_url)
                relevant_links.append(normalized_full_url)

        return relevant_links

    async def process_relevant_link(self, relevant_url, base_url):
        if relevant_url in self.discovered: return
        if not self.is_new_link(relevant_url, base_url): return
        if self.is_url_in_queue(relevant_url): return 
        # if relevant_url not in self.discovered and self.is_new_link(relevant_url, base_url):
        self.url_queue.append((relevant_url, base_url))
        self.discovered.add(relevant_url)  # Add to the visited set
        print(f"Queueing relevant link: {relevant_url}")

    def is_url_in_queue(self, url):
        # Check if the URL is already in the queue
        return any(queued_url == url for queued_url, _ in self.url_queue)

    async def extract_link_details(self, page, link):
        link_text = await link.inner_text()
        link_text = link_text.lower()
        href = await self.get_href(page, link)
        return link_text, href


    def is_new_link(self, url, base_url):
        return url not in self.discovered and self.same_domain(base_url, url)
    
    def is_relevant_link(self, link_text, url):
        # Here, a cosine similarity search could be applied, or a keyword match
        # But the logic will need to be tailored to the user's needs
        if "*" in self.keywords:
            return True
        
        combined_text = f"{url} {link_text}"
        return self.efficient_filter(combined_text)
        
    
    def filter_links(self, links):
        return [link for link in links if self.efficient_filter(link)]

    def is_similar(self, link_text):
        return difflib.SequenceMatcher(None, link_text.lower(), " ".join(self.keywords).lower()).ratio() > 0.6
    
    def efficient_filter(self, link_text):
        # Simple keyword matching
        return any(keyword in link_text for keyword in self.keywords)
    
    def handle_html_page(self, page):
        pass

    def handle_innertext(self, text):
        pass
    
    @staticmethod
    def construct_full_url(href, base_url):
        return href if href.startswith("http") else urljoin(base_url, href)
    
    @staticmethod
    def get_base_url(url):
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    @staticmethod
    def should_process_link(href):
        return href and not href.startswith("#")

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
    