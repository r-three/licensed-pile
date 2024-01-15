"""Export the pages we enumerated as xml.

This page https://www.mediawiki.org/wiki/Manual:Parameters_to_Special:Export
lists multiple limits to the amount of data that can be returned. In the two
wiki's I have been testing on I haven't found these to be true. The main
points of concern are:
* pages: The limit is 35
* limit: The maximum number of revisions to return, limited at 1000.
* history: It mentions there are cases where this doesn't return all the revisions.
* listauthors: This didn't seem active on any of the wikis I tested on.
"""


import argparse
import glob
import os
import urllib.parse
from typing import List

from utils import get_page, get_wiki_name

parser = argparse.ArgumentParser(description="Export mediawikis as XML")
parser.add_argument("--wiki", required=True, help="The wiki url we are exporting.")
parser.add_argument(
    "--pages",
    action="append",
    help="A list of files of pages to export, or a dir to export all. defaults to data/${wiki_name}/pages/.",
)
# Using firefox I didn't have issues sending a lot of pages at once, but I was
# getting URI too long errors when using requests.
parser.add_argument(
    "--page_limit", default=35, help="The max number of pages to export at once."
)
parser.add_argument(
    "--output_dir",
    help="Where to save the xml export. defaults to data/${wiki_name}/export/.",
)
# TODO: Implement this if we find a wiki that has this enabled.
parser.add_argument(
    "--listauthors",
    help="Use the listauthors url param instead of getting multiple revisions. UNIMPLEMENTED.",
)


def export_pages(wiki: str, pages: List[str]):
    # Note: We don't quote the newline ourselves as requests will do it too and
    # you'll get `%250A` instead of `%0A` in the url.
    pages = "\n".join(pages).strip("\n")
    # Even though they recomment using the index.php?title=PAGETITLE url for a lot
    # of things (with the /wiki/ being for readers), we use it here to start looking
    # for pages because it is more consistent (some wiki's want /w/index.php and
    # some just want /index.php).
    return get_page(
        urllib.parse.urljoin(wiki, "/wiki/Special:Export"),
        params={"pages": pages, "history": 1},
    )


def read_page_titles(filename: str) -> List[str]:
    with open(filename) as f:
        return f.read().strip("\n").split("\n")


def main(args):
    args.pages = (
        args.pages
        if args.pages is not None
        else [os.path.join("data", get_wiki_name(args.wiki), "pages")]
    )
    pages = []
    for page in args.pages:
        if os.path.exists(page) and os.path.isdir(page):
            for f in glob.glob(os.path.join(page, "*.txt")):
                pages.extend(read_page_titles(f))
        else:
            pages.extend(read_page_titles(page))

    args.output_dir = (
        args.output_dir
        if args.output_dir is not None
        else os.path.join("data", get_wiki_name(args.wiki), "export")
    )
    os.makedirs(args.output_dir, exist_ok=True)

    # Save shards of exported pages to
    #   data/${wiki_name}/export/${shard_idx}-pages.xml
    # These shards can be processed as if they are one large xml file with
    #   licensed_pile.xml.iterate_xmls(glob.iglob(...), tag)
    # Note: These exports seem to an xml namespace so all tags are actually
    #   "{http://mediawiki.org/xml/export-0.11/}TAGNAME"
    # with literal "{"'s.
    for i, j in enumerate(range(0, len(pages), args.page_limit)):
        xml = export_pages(args.wiki, pages[j : j + args.page_limit])
        dirname, filename = os.path.split(args.output)
        with open(os.path.join(dirname, f"{i:>05}-{filename}"), "w") as wf:
            wf.write(xml)


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
