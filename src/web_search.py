from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
from .file_utils import clean_text, log
import difflib

def get_content_from_url(urls):
    text_content = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = {}
        for url in urls:
            try:
                page = context.new_page()
                page.goto(url)

                # Extract the text content from the page
                content = page.inner_text('body')
                text_content.append(clean_text(content))
                log(f"Fetched content of URL {url}")
            except Exception as e:
                print(f"An error occurred while fetching the content from {url}: {e}")
                continue

            finally:
                # Close the page after processing
                page.close()

    return text_content

async def get_content_from_url_async(urls):
    text_content = []
    

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()

        for url in urls:
            try:
                page = await context.new_page()
                await page.goto(url)

                # Extract the text content from the page
                content = await page.inner_text('body')
                text_content.append(clean_text(content))

            except Exception as e:
                print(f"An error occurred while fetching the content from {url}: {e}")

            finally:
                # Close the page after processing
                await page.close()

    return text_content

# def search_ddg(query: str, num_results: int = 25):
#     with sync_playwright() as p:
#         browser = p.chromium.launch()
#         context = browser.new_context()
#         page = context.new_page()

#         url = f"https://html.duckduckgo.com/html/?q={query}"
#         page.goto(url)

#         # Adjust the selector based on the structure of the HTML
#         results = page.query_selector_all('div.result, div.web-result')
#         response = []
#         for result in results[:num_results]:  # Use slicing to limit the results
#             # Extract and print relevant information from each result
#             description = result.inner_text().strip()
#             details = description.split("\n")
#             title = details[0]
#             url = details[1]
#             description = details[2]
#             # print("============================")
#             # print(f'Title: {title}\nURL: {url}\nDescription: {description}')
#             response.append({"title": title, "href": "https://"+url.strip(), "description": description})

#         return response

def search_ddg(query: str, num_results: int = 25):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        url = f"https://html.duckduckgo.com/html/?q={query}"
        page.goto(url)

        # Adjust the selector based on the structure of the HTML
        response = []

        while len(response) < num_results:
            results = page.query_selector_all('div.result, div.web-result')
            for result in results:
                if len(response) >= num_results:
                    break

                # Extract and print relevant information from each result
                description = result.inner_text().strip()
                details = description.split("\n")
                title = details[0]
                url = details[1]
                description = details[2]

                response.append({"title": title, "href": "https://"+url.strip(), "description": description})

            # Check if there's a "Next" button and click it
            next_button = page.query_selector('input[value="Next"]')
            if next_button:
                next_button.click()
                page.wait_for_selector('div.result, div.web-result')

        return response[:num_results]

async def asearch_ddg(query: str, num_results: int = 25):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        url = f"https://html.duckduckgo.com/html/?q={query}"
        await page.goto(url)

        response = []

        while len(response) < num_results:
            results = await page.query_selector_all('div.result, div.web-result')
            for result in results:
                if len(response) >= num_results:
                    break

                description = await result.inner_text()
                details = description.split("\n")
                title = details[0]
                url = details[1]
                description = details[2]

                response.append({"title": title, "href": "https://"+url.strip(), "description": description})

            next_button = await page.query_selector('input[value="Next"]')
            if next_button:
                await next_button.click()
                await page.wait_for_selector('div.result, div.web-result')

        await browser.close()
        return response[:num_results]


# def crawl_url(url, visited=None, depth=0, max_depth=3):
#     if visited is None:
#         visited = set()

#     if depth > max_depth:
#         return []

#     text_content = []

#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         context = browser.new_context()
#         page = context.new_page()

#         if url not in visited:
#             visited.add(url)
#             try:
#                 page.goto(url)

#                 content = page.inner_text('body')
#                 text_content.append(clean_text(content))
#                 log(f"Fetched content of URL {url}")

#                 links = page.query_selector_all('a')
#                 for link in links:
#                     link_text = link.inner_text().strip()
#                     href = link.get_attribute('href')
#                     if href and is_similar(link_text, "Agents"):  # Checking similarity with "Agents"
#                         text_content += crawl_url(href, visited, depth+1, max_depth)

#             except Exception as e:
#                 print(f"An error occurred while fetching the content from {url}: {e}")

#             finally:
#                 page.close()

#     return text_content



    # For a more sophisticated similarity check, you could use something like:
    # return difflib.SequenceMatcher(None, link_text.lower(), query.lower()).ratio() > 0.6


# Remember to start the event loop for asynchronous execution
