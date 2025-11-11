from __future__ import annotations

from typing import List, Optional

from bs4 import BeautifulSoup
from urllib.parse import urljoin


def _normalize_urls(elements, attribute: str, base_url: Optional[str]) -> List[str]:
    urls: list[str] = []
    for element in elements:
        href = element.get(attribute)
        if not href:
            continue
        if base_url:
            href = urljoin(base_url, href)
        urls.append(href)
    return urls


def parse_basic_structure(html: str, base_url: Optional[str] = None) -> dict:
    soup = BeautifulSoup(html, "lxml")
    title_el = soup.find("title")
    title = title_el.get_text(strip=True) if title_el else ""

    links = _normalize_urls(soup.find_all("a", href=True), "href", base_url)
    images = _normalize_urls(soup.find_all("img", src=True), "src", base_url)

    headers = {
        "h1": len(soup.find_all("h1")),
        "h2": len(soup.find_all("h2")),
        "h3": len(soup.find_all("h3")),
        "h4": len(soup.find_all("h4")),
        "h5": len(soup.find_all("h5")),
        "h6": len(soup.find_all("h6")),
    }

    images_count = len(soup.find_all("img"))

    return {
        "title": title,
        "links": links,
        "structure": headers,
        "images_count": images_count,
        "image_urls": images,
    }

