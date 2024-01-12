
from src.crawler import WebCrawler
import json
def write_file(filepath, content):
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content)

def main():
    crawler = WebCrawler(
        keywords=["*"], 
        dump_to_file=True, 
        max_concurrent=2,
        max_visits=5,
        url_list=["https://vitrinelinguistique.oqlf.gouv.qc.ca/banque-de-depannage-linguistique/lorthographe",],
        # base_url_list=["https://vitrinelinguistique.oqlf.gouv.qc.ca/banque-de-depannage-linguistique/lorthographe",],
    )
    
    contents = crawler.start_crawling()
    print(contents)

main()