"""Enumerate all the namespaces in a mediawiki wiki."""

import argparse
import json
import logging
import os
import urllib.parse
from typing import Dict

from utils import get_page, get_wiki_name

parser = argparse.ArgumentParser(description="Find all namespaces in a mediawiki wiki.")
parser.add_argument("--wiki", required=True, help="The Url for the wiki in question.")
parser.add_argument(
    "--output",
    help="Where to save the id -> namespace mapping. Normally (data/${wiki_name}/namespaces.json)",
)


def find_namespaces(wiki_url: str) -> Dict[int, str]:
    options = {}
    logging.info(f"Finding all namespaces from {args.wiki}")
    # Even though they recomment using the index.php?title=PAGETITLE url for a lot
    # of things (with the /wiki/ being for readers), we use it here to start looking
    # for pages because it is more consistent (some wiki's want /w/index.php and
    # some just want /index.php).
    soup = get_page(urllib.parse.urljoin(wiki_url, "/wiki/Special:AllPages"))
    # Extract the list of namespaces from the URL
    namespaces = soup.find(id="namespace")
    for option in namespaces.find_all("option"):
        options[option.text] = int(option.attrs["value"])
    return options


def main(args):
    namespaces = find_namespaces(args.wiki)
    args.output = (
        args.output
        if args.output is not None
        else os.path.join("data", get_wiki_name(args.wiki), "namespaces.json")
    )

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as wf:
        json.dump(namespaces, wf, indent=2)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
