"""Convert a wikiscrape of media-wiki dump into the dolma format."""

import argparse
import datetime
import functools
import glob
import os
import urllib.parse

from utils import get_wiki_name, make_wiki_url

from licensed_pile.licenses import PermissiveLicenses
from licensed_pile.logs import configure_logging, get_logger
from licensed_pile.write import to_dolma
from licensed_pile.xml import iterate_xmls

SOURCE_NAME = "wiki/scrape"


parser = argparse.ArgumentParser(description="Convert the xml export to dolma.")
parser.add_argument("--wiki", required=True, help="The wiki url we are processing.")
parser.add_argument("--license", required=True, help="The licenses this is under.")
parser.add_argument("--export", help="The location of the exported pages.")
parser.add_argument(
    "--output_dir",
    default=f"data/{SOURCE_NAME}/raw/documents/",
    help="Where the dolma formatted data goes.",
)
parser.add_argument(
    "--source",
    choices=["wiki/scrape", "wiki/archive", "wiki/dump"],
    default="wiki/scrape",
    help="Where does the data come from?",
)
parser.add_argument(
    "--filename", default=None, help="The base filename for our wiki data."
)
parser.add_argument(
    "--shard_size", type=int, default=1, help="Size, in GB, for each shard."
)
parser.add_argument(
    "--last_author",
    action="store_true",
    help="Should we only include the most recent author? (Faster)",
)
parser.add_argument(
    "--include_redirects",
    action="store_true",
    help="Should we skip pages that are redirects to others?",
)


def main(args):
    # Calculate defaults
    license = PermissiveLicenses.from_string(args.license)
    logger = get_logger("wiki/scrape")
    logger.info("Saving all exported pages as licensed with %s", license)
    args.filename = (
        args.filename if args.filename else f"{get_wiki_name(args.wiki)}.jsonl.gz"
    )
    logger.info("Saving to dolma format at %s", args.filename)
    args.export = (
        args.export
        if args.export
        else os.path.join("data", get_wiki_name(args.wiki), "export", "*.xml")
    )
    logger.info("Loading export from %s", args.export)

    logger.info("Saving Dolma formatted data to %s", args.output_dir)
    # Our parser can ignore xml-namespaces so just use `page`.
    pages = iterate_xmls(glob.iglob(args.export), tag="page")
    pages = map(
        functools.partial(
            format_dolma,
            source_name=args.source,
            wiki=args.wiki,
            license=license,
            all_authors=not args.last_author,
            skip_redirect=not args.include_redirects,
        ),
        pages,
    )
    # When we filter out pages based on things like redirects, they may be None
    pages = filter(lambda p: p is not None, pages)
    to_dolma(pages, args.output_dir, args.filename, args.shard_size)


def generate_old():
    pass


def format_old(
    page,
    source_name: str,
    wiki: str,
    license: PermissiveLicenses,
    all_authors: bool = True,
):
    with open(f"{page}.wikitext") as f:
        wikitext = f.read()

    metadata = pd.read_csv(f"{page}.history.csv")
    # Should created be fisrt of last edit?
    date = metadata["Date (America/Los_Angeles)"].max()
    authors = set(metadata["Author"])
    page_title = os.path.basename(page)
    # Doesn't seem available in old dumps
    page_namespace = None

    return {
        "id": None,
        "text": wikitext,
        "source": f"{source_name}-{wiki}",
        "added": datetime.datetime.utcnow().isoformat(),
        "created": date.isoformat(),
        "metadata": {
            "license": str(license),
            "authors": sorted(authors),
            "url": make_wiki_url(wiki, page_title),
            "wiki": get_wiki_name(wiki),
            "namespace": page_namespace,
            "title": page_title,
        },
    }


def format_dolma(
    xml,
    source_name: str,
    wiki: str,
    license: PermissiveLicenses,
    all_authors: bool = True,
    skip_redirect: bool = True,
):
    if skip_redirect and [x for x in xml if x.tag.endswith("redirect")]:
        return None
    revisions = [r for r in xml if r.tag.endswith("revision")]
    # TODO Handle if this fails and add logging.
    text = [t for t in revisions[-1] if t.tag.endswith("text")][0].text
    page_namespace = [ns for ns in xml if ns.tag.endswith("ns")][0].text
    page_id = [pid for pid in xml if pid.tag.endswith("id")][0].text
    created = datetime.datetime.fromisoformat(
        [ts for ts in revisions[-1] if ts.tag.endswith("timestamp")][0].text
    ).replace(tzinfo=None)
    page_title = [t for t in xml if t.tag.endswith("title")][0].text

    contributors = set()
    if all_authors:
        for revision in revisions:
            contribs = [c for c in revision if c.tag.endswith("contributor")]
            # When there are multiple contributors, there are multiple contributor
            # xml items where each one has a single username and id items.
            names = [u.text for c in contribs for u in c if u.tag.endswith("username")]
            # Save their id too in case they change their username
            uid = [u.text for c in contribs for u in c if u.tag.endswith("id")]
            contributors.update(zip(names, uid))
    else:
        contrib = [c for c in revisions[-1] if c.tag.endswith("contributor")]
        # When there are multiple contributors, there are multiple contributor
        # xml items where each one has a single username and id items.
        name = [u.text for c in contrib for u in c if u.tag.endswith("username")]
        # Save their id too in case they change their username
        uid = [u.text for c in contrib for u in c if u.tag.endswith("id")]
        contributors.update(zip(name, uid))

    return {
        "id": f"{page_namespace}-{page_id}",
        "text": text,
        "source": f"{source_name}/{get_wiki_name(wiki)}",
        "added": datetime.datetime.utcnow().isoformat(),
        "created": created.isoformat(),
        "metadata": {
            "license": str(license),
            "authors": sorted(contributors),
            "url": make_wiki_url(wiki, page_title),
            "wiki": get_wiki_name(wiki),
            "namespace": page_namespace,
            "title": page_title,
        },
    }


if __name__ == "__main__":
    args = parser.parse_args()
    configure_logging("wiki/scrape")
    main(args)