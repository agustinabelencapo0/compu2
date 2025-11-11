from __future__ import annotations

from bs4 import BeautifulSoup


def extract_meta_tags(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    meta: dict[str, str] = {}

    def set_if_present(key: str, value: str | None) -> None:
        if value:
            meta[key] = value

    description = soup.find("meta", attrs={"name": "description"})
    keywords = soup.find("meta", attrs={"name": "keywords"})
    og_title = soup.find("meta", attrs={"property": "og:title"}) or soup.find(
        "meta", attrs={"name": "og:title"}
    )
    og_desc = soup.find("meta", attrs={"property": "og:description"}) or soup.find(
        "meta", attrs={"name": "og:description"}
    )

    set_if_present("description", description.get("content") if description else None)
    set_if_present("keywords", keywords.get("content") if keywords else None)
    set_if_present("og:title", og_title.get("content") if og_title else None)
    set_if_present("og:description", og_desc.get("content") if og_desc else None)

    return meta

