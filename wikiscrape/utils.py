"""Utilities for scraping wikis."""

import logging
import urllib.parse
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_random_exponential

from licensed_pile.scrape import USER_AGENT

logging.basicConfig(
    level=logging.INFO,
    format="wikiscrape: [%(asctime)s] %(levelname)s - %(message)s",
)


@retry(stop=stop_after_attempt(5), wait=wait_random_exponential(multiplier=1, max=30))
def get_page(url: str, params: Optional[Dict[str, str]] = None):
    """Get page and parse into soup."""
    params = params if params is not None else {}
    resp = requests.get(url, params=params, headers={"User-Agent": USER_AGENT})
    logging.debug(f"Sending GET to {resp.url}")
    if resp.status_code != 200:
        logging.warning(
            f"Failed request to {resp.url}: {resp.status_code}, {resp.reason}"
        )
        raise RuntimeError(f"Failed request to {resp.url}")
    return resp.text


def get_soup(text, parser="html.parser"):
    """Abstract into a function in case we want to swap how we parse html."""
    return BeautifulSoup(text, parser)


def get_wiki_name(url: str) -> str:
    """Use a wiki's url as it's name.

    This functions is to abstract into a semantic unit, even though it doesn't do much.
    """
    return urllib.parse.urlparse(url).netloc


def removeprefix(s: str, prefix: str) -> str:
    """Incase we aren't using python >= 3.9"""
    if s.startswith(prefix):
        return s[len(prefix) :]
    return s[:]
