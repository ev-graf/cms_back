import cloudscraper

from src.universal import retry_request


@retry_request(max_retries=5, delay=1, backoff=2)
def get_author_pixiv(artwork_id: str, lang: str = "en") -> str:
    scraper = cloudscraper.create_scraper(
        browser={"custom": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/125.0.0.0 Safari/537.36"}
    )
    # Обязательно добавляем Referer — Pixiv требует его
    base = f"https://www.pixiv.net/{lang}/artworks/{artwork_id}"
    ajax_url = f"https://www.pixiv.net/ajax/illust/{artwork_id}"
    headers = {"Referer": base, "Accept": "application/json"}

    resp = scraper.get(ajax_url, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    user_id = data["body"]["userId"]
    if not user_id:
        raise ValueError("Не найден userId автора")
    return f"pixiv.net/{lang}/users/{user_id}"
