"""Utilities for scraping wikis."""

import urllib.parse
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup

from licensed_pile import scrape


def get_page(*args, **kwargs):
    r = scrape.get_page(*args, **kwargs)
    return r.text


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


def wiki_url(base_url: str, title: str) -> str:
    """Create a wiki url from the wiki url and the page name."""
    url = urllib.parse.urljoin(base_url, f"wiki/{title.replace(' ', '_')}")
    return urllib.parse.quote(url, safe=":/")
