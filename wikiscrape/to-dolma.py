"""Convert a wikiscrape of media-wiki dump into the dolma format."""

import argparse
import datetime
import functools
import glob
import itertools
import urllib.parse

from utils import get_wiki_name, wiki_url

from licensed_pile.licenses import PermissiveLicenses
from licensed_pile.write import to_dolma
from licensed_pile.xml import iterate_xmls

SOURCE_NAME = "wikiscrape"


parser = argparse.ArgumentParser(description="Convert the xml export to dolma.")
parser.add_argument("--wiki", required=True, help="The wiki url we are exporting.")
parser.add_argument("--license", required=True, help="The licenses this is under.")
parser.add_argument("--export", help="The location of the exported pages.")
parser.add_argument(
    "--output_dir",
    default=f"data/{SOURCE_NAME}/raw/documents/",
    help="Where the dolma formatted data goes.",
)
parser.add_argument(
    "--filename", default=None, help="The base filename for our chat data."
)
parser.add_argument(
    "--shard_size", type=int, default=1, help="Size, in GB, for each shard."
)


def main(args):
    # Calculate defaults
    license = PermissiveLicenses.from_string(args.license)
    args.filename = (
        args.filename if args.filename else f"{get_wiki_name(args.wiki)}.jsonl.gz"
    )
    args.export = (
        args.export
        if args.export
        else os.path.join("data", get_wiki_name(args.wiki), "export", "*.xml")
    )

    # Our parser can ignore namespaces so just use `page`.
    pages = iterate_xmls(glob.iglob(args.export), tag="page")
    pages = map(
        functools.partial(
            format_dolma, source_name=SOURCE_NAME, wiki=args.wiki, license=license
        ),
        pages,
    )
    to_dolma(pages, args.output_dir, args.filename, args.shard_size)


def format_dolma(xml, source_name: str, wiki: str, license: PermissiveLicenses):
    revisions = [r for r in xml if r.tag.endswith("revision")]
    # TODO Handle if this fails.
    text = [t for t in revisions[-1] if t.tag.endswith("text")][0].text
    page_namespace = [ns for ns in xml if ns.tag.endswith("ns")][0].text
    page_id = [pid for pid in xml if pid.tag.endswith("id")][0].text
    created = datetime.datetime.fromisoformat(
        [ts for ts in revisions[-1] if ts.tag.endswith("timestamp")][0].text
    ).replace(tzinfo=None)
    page_title = [t for t in xml if t.tag.endswith("title")][0].text

    contributors = set()
    for revision in revisions:
        contribs = [c for c in revision if c.tag.endswith("contributor")]
        # When there are multiple contributors, there are multiple contributor
        # xml items where each one has a single username and id items.
        names = [u.text for c in contribs for u in c if u.tag.endswith("username")]
        # Save their id too in case they change their username
        uid = [u.text for c in contribs for u in c if u.tag.endswith("id")]
        contributors.update(zip(names, uid))

    return {
        "id": f"{page_namespace}-{page_id}",
        "text": text,
        "source": f"{source_name}-{wiki}",
        "added": datetime.datetime.utcnow().isoformat(),
        "created": created.isoformat(),
        "metadata": {
            "license": str(license),
            "authors": sorted(contributors),
            "url": wiki_url(wiki, page_title),
            "wiki": get_wiki_name(wiki),
            "namespace": page_namespace,
            "title": page_title,
        },
    }


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
