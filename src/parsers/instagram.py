import cloudscraper
from bs4 import BeautifulSoup

from src.universal import retry_request


@retry_request(max_retries=5, delay=1, backoff=2)
def get_author_instagram(post_url: str) -> str:
    scraper = cloudscraper.create_scraper(browser={'custom': 'Chrome/125.0.6422.XX'})
    resp = scraper.get(post_url, headers={'Referer': 'https://www.instagram.com/'})
    resp.raise_for_status()
    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    element = soup.find(attrs={"property": "og:url"})
    if element:
        link = element['content']
        p = link.split("/")
        if len(p) > 4 and p[4] == "p":
            return f"instagram.com/{p[3]}"
    return ""
