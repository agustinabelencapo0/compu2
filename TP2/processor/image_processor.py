from __future__ import annotations

import io
from typing import Iterable, List

import urllib.request
from PIL import Image


def _download_bytes(url: str, timeout: int = 20) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read()


def generate_thumbnails(image_urls: Iterable[str], size: int = 160, max_images: int = 3) -> List[bytes]:
    thumbs: list[bytes] = []
    for url in list(image_urls)[:max_images]:
        try:
            raw = _download_bytes(url)
            img = Image.open(io.BytesIO(raw))
            img.thumbnail((size, size))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            thumbs.append(buf.getvalue())
        except Exception:
            continue
    return thumbs

