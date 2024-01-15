"""Utilities for scraping wikis."""

import logging
import urllib.parse
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_random_exponential

logging.basicConfig(
    level=logging.INFO,
    format="wikiscrape: [%(asctime)s] %(levelname)s - %(message)s",
)


@retry(stop=stop_after_attempt(5), wait=wait_random_exponential(multiplier=1, max=30))
def get_page(
    url: str, params: Optional[Dict[str, str]] = None, parser: str = "html.parser"
):
    """Get page and parse into soup."""
    params = params if params is not None else {}
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        logging.warning(
            f"Failed request to {resp.url}: {resp.status_code}, {resp.reason}"
        )
        raise RuntimeError(f"Failed request to {resp.url}")
    return BeautifulSoup(resp.text, parser)


def get_wiki_name(url: str) -> str:
    """Use a wiki's url as it's name."""
    return urllib.parse.urlparse(url).netloc


def removeprefix(s: str, prefix: str) -> str:
    """Incase we aren't using python >= 3.9"""
    if s.startswith(prefix):
        return s[len(prefix) :]
    return s[:]
