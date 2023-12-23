
from src.crawler import WebCrawler

def main():
    crawler = WebCrawler(keywords="matrix matrices", dump_to_file=True, max_concurrent=3)
    content = crawler.start_crawling()
    print(content)

main()