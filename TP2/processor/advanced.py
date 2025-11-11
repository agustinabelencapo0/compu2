from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup


def detect_technologies(html: str) -> List[str]:
    """Heurísticas simples para detectar tecnologías comunes en el frontend/backend."""
    soup = BeautifulSoup(html, "lxml")
    text = html.lower()
    technologies: set[str] = set()

    markers: Dict[str, List[str]] = {
        "React": ["data-reactroot", "react"],
        "Angular": ["ng-app", "ng-controller", "angular"],
        "Vue": ["v-bind:", "vuejs", "vue.js", "vue"],
        "Svelte": ["svelte"],
        "jQuery": ["jquery"],
        "Bootstrap": ["bootstrap"],
        "TailwindCSS": ["tailwind"],
        "WordPress": ["wp-content", "wp-json"],
        "Drupal": ["drupal"],
        "Django": ["django"],
        "Laravel": ["laravel"],
        "Next.js": ["__next", "next/dist"],
        "Nuxt.js": ["nuxt"],
    }

    scripts = " ".join(script.get("src") or "" for script in soup.find_all("script"))
    styles = " ".join(link.get("href") or "" for link in soup.find_all("link"))
    haystack = " ".join([text, scripts.lower(), styles.lower()])

    for label, clues in markers.items():
        if any(clue in haystack for clue in clues):
            technologies.add(label)

    return sorted(technologies)


def evaluate_seo(html: str, scraping_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    title = (scraping_data or {}).get("title") or (soup.find("title").get_text(strip=True) if soup.find("title") else "")
    meta_tags = (scraping_data or {}).get("meta_tags", {})
    description = meta_tags.get("description") or ""

    h1_count = len(soup.find_all("h1"))
    canonical = soup.find("link", rel="canonical")
    robots = soup.find("meta", attrs={"name": "robots"})
    has_open_graph = any("og:" in (tag.get("property") or "") for tag in soup.find_all("meta"))

    score = 0
    score += 15 if title else 0
    score += 20 if 10 <= len(title) <= 70 else 0
    score += 15 if description else 0
    score += 15 if 50 <= len(description) <= 160 else 0
    score += 10 if h1_count == 1 else 0
    score += 10 if canonical else 0
    score += 5 if robots else 0
    score += 10 if has_open_graph else 0

    return {
        "title_length": len(title),
        "meta_description_length": len(description),
        "h1_count": h1_count,
        "has_canonical": bool(canonical),
        "has_robots": bool(robots),
        "has_open_graph": has_open_graph,
        "score": min(score, 100),
    }


def extract_structured_data(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    structured_data: List[Dict[str, Any]] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.get_text(strip=True))
            if isinstance(data, list):
                structured_data.extend(item for item in data if isinstance(item, dict))
            elif isinstance(data, dict):
                structured_data.append(data)
        except json.JSONDecodeError:
            continue
    return structured_data


def analyze_accessibility(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    images = soup.find_all("img")
    images_missing_alt = [img.get("src") for img in images if not (img.get("alt") or "").strip()]

    links = soup.find_all("a")
    links_without_text = [
        link.get("href") for link in links if not (link.get_text(strip=True) or "").strip()
    ]

    buttons = soup.find_all("button")
    buttons_without_text = [
        idx
        for idx, button in enumerate(buttons)
        if not (button.get_text(strip=True) or "").strip()
    ]

    contrast_warnings = _detect_basic_contrast_issues(soup)

    total_issues = (
        len(images_missing_alt)
        + len(links_without_text)
        + len(buttons_without_text)
        + len(contrast_warnings)
    )
    score = max(0, 100 - total_issues * 10)

    return {
        "images_missing_alt": images_missing_alt,
        "links_without_text": links_without_text,
        "buttons_without_text": buttons_without_text,
        "contrast_warnings": contrast_warnings,
        "score": score,
    }


def _detect_basic_contrast_issues(soup: BeautifulSoup) -> List[str]:
    warnings: List[str] = []
    for element in soup.find_all(style=True):
        style = element.get("style", "").lower()
        color_match = re.search(r"color:\s*#([0-9a-f]{3,6})", style)
        bg_match = re.search(r"background(-color)?:\s*#([0-9a-f]{3,6})", style)
        if color_match and bg_match:
            fg = color_match.group(1)
            bg = bg_match.group(2)
            if fg == bg:
                warnings.append(f"Posible poco contraste en elemento: {element.name}")
    return warnings

