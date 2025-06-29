import re

from .artstation import get_author_artstation
from .cara import get_author_cara
from .instagram import get_author_instagram
from .pixiv import get_author_pixiv


def parser_universal(link: str) -> str:
    link = re.sub(r"^(https?://)(www\.)?", "", link)
    p = link.split("/")
    return f"{p[0]}/{p[1]}" if len(p) > 1 else ""


def parser_tg(link: str) -> str:
    s = "t.me"
    p = link.split("/")
    return f"{s}/{p[3]}" if len(p) > 3 else ""


def parser_deviantart(link: str) -> str:
    s = "deviantart.com"
    p = link.split("/")
    return f"{s}/{p[3]}" if len(p) > 3 and p[4] == "art" else ""


def parser_newgrounds(link: str) -> str:
    e = "newgrounds.com"
    p = link.split("/")
    return f"{p[5]}.{e}" if len(p) > 5 and p[3] == "art" else ""


def parser_x(link: str) -> str:
    s = "x.com"
    p = link.split("/")
    return f"{s}/{p[3]}" if len(p) > 3 and p[4] == "status" else ""


def parser_bsky(link: str) -> str:
    s, e = "bsky.app/profile", "bsky.social"
    p = link.split('/')
    return (p[4] if p[4].endswith(f".{e}") else f"{s}/{p[4]}") if len(p) > 5 and p[5] == "post" else ""


def parser_tumblr(link: str) -> str:
    s = "tumblr.com"
    p = link.split("/")
    return (f"{s}/{p[3]}" if f"www.{s}/" in link else (p[2] if p[3] == "post" else "")) if len(p) > 3 else ""


def parser_vk(link: str) -> str:
    s = "vk.com"
    p = link.split("/")
    return f"{s}/club{p[3].replace('wall-', '').split('_')[0]}" if len(p) >= 3 and "wall" in p[3] else ""


def parser_instagram(link: str) -> str:
    s = "instagram.com"
    p = link.split("/")
    return (f"{s}/{p[3]}" if p[4] == "p" else (get_author_instagram(link) if p[3] == "p" else "")) if len(p) > 4 else ""


def parser_artstation(link: str) -> str:
    p = link.split("/")
    return get_author_artstation(link) if len(p) > 3 and p[3] == "artwork" else ""


def parser_pixiv(link: str) -> str:
    p = link.split("/")
    return get_author_pixiv(p[5]) if len(p) == 6 and p[4] == "artworks" else ""


def parser_cara(link: str) -> str:
    p = link.split("/")
    return get_author_cara(p[4]) if len(p) > 3 and p[3] == "post" else ""


def get_parsers() -> dict:
    parsers = {
        "t.me/": parser_tg,
        "x.com/": parser_x,
        "vk.com/": parser_vk,
        "bsky.app/": parser_bsky,
        "cara.app/": parser_cara,
        "pixiv.net/": parser_pixiv,
        "tumblr.com/": parser_tumblr,
        "instagram.com/": parser_instagram,
        "deviantart.com/": parser_deviantart,
        "artstation.com/": parser_artstation,
        "newgrounds.com/": parser_newgrounds,
    }
    return parsers


def get_author_url(link: str) -> str:
    link = link.replace("twitter.com/", "x.com/")
    parsers = get_parsers()
    link_site = next((site for site in parsers.keys() if site in link), "")

    try:
        author = parsers.get(link_site, parser_universal)(link)
        return author
    except Exception as e:
        # print(e)
        return ""
