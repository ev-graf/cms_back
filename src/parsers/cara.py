import cloudscraper

from src.universal import retry_request


@retry_request(max_retries=5, delay=1, backoff=2)
def get_author_cara(post_id: str) -> str:
    scraper = cloudscraper.create_scraper()
    url = f"https://cara.app/api/posts/{post_id}"
    data = scraper.get(url).json()
    usr = data["data"]["slug"]
    return f"cara.app/{usr}"
