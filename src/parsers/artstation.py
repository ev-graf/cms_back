from requests import request

from src.universal import retry_request


@retry_request(max_retries=5, delay=1, backoff=2)
def get_author_artstation(post_url: str) -> str:
    if "/artwork/" not in post_url:
        raise ValueError("Неправильный формат ссылки")

    artwork_id = post_url.split("/artwork/")[1]
    url = f"https://www.artstation.com/projects/{artwork_id}.json"

    response = request(method="GET", url=url)
    response.raise_for_status()

    data = response.json()
    return f'artstation.com/{str(data["user"]["permalink"]).split("/")[-1]}'
