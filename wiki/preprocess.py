#!/usr/bin/env python3

import argparse
import glob
import multiprocessing as mp
import os
import re
from tempfile import TemporaryDirectory

import requests
import tqdm

import wiki
from licensed_pile import logs, utils
from licensed_pile.write import ShardParallelProcessor

parser = argparse.ArgumentParser(description="Preprocess raw books in dolma format.")
parser.add_argument(
    "--input",
    default="dump/data/wiki/dump/raw",
    help="The input version, this directory should be where the `documents` dir lives.",
)
parser.add_argument(
    "--output",
    default="dump/data/wiki/dump/v0",
    help="The output version, this directory should be where the `documents` dir will live.",
)
parser.add_argument(
    "--filename",
    default="*.jsonl.gz",
    help="The filename to match with globs, probably needs to be escaped.",
)
# TODO: Respect this flag
parser.add_argument(
    "--overwrite",
    action="store_true",
    help="Should we overwrite previously processed examples?",
)
parser.add_argument(
    "--debug",
    action="store_true",
    help="Should we log when documents are not changed by preprocessing.",
)
parser.add_argument(
    "--processes",
    type=int,
    default=mp.cpu_count(),
    help="Number of processors for multicore.",
)

logs.configure_logging("dolma.WTFWikipediaParallel")


class WTFWikipediaParallel(ShardParallelProcessor):
    @classmethod
    def process_example(cls, example, **kwargs):
        logger = cls.get_logger()
        logger.warning(f"Processing example: {example['id']}")
        wikitext = example["text"]
        # Should be fixed in the dolma generation script.
        if wikitext is None:
            wikitext = ""
        # Convert <math>
        wikitext = wiki.replace_math_tags(wikitext)
        # Adjust indentation to avoid reorderings.
        wikitext = wiki.adjust_indentation(wikitext)
        # Extract Templates
        wikitext, math_templates = wiki.extract_templates(
            wikitext, ("math",), wiki.MATH_MARKER
        )
        # Parse Wiki Text
        document = wiki.parse_wikitext(wikitext, example["id"], example["source"])
        # Format plaintext into document
        document = wiki.format_document(
            document, example.get("metadata", {}).get("title", "")
        )
        # Process Templates
        math_templates = map(wiki.fix_math, math_templates)
        parsed_templates = [
            wiki.parse_wikitext(t, example["id"], example["source"])[0]["text"]
            for t in math_templates
        ]
        parsed_templates = [t.replace(wiki.ABS_MARKER, "|") for t in parsed_templates]
        parsed_templates = [f"${t}$" for t in parsed_templates]
        # Reinsert Templates
        document = wiki.insert_templates(document, parsed_templates, wiki.MATH_MARKER)
        example["text"] = document
        return example


def main(args):
    with TemporaryDirectory() as tempdir:
        processor = WTFWikipediaParallel(
            source_prefix=utils.dolma_input(args.input, args.filename),
            destination_prefix=utils.dolma_output(args.output),
            metadata_prefix=tempdir,
            num_processes=args.processes,
        )
        processor(debug=args.debug)


if __name__ == "__main__":
    # Dolma examples use spawn over fork, unsure why but lets follow them.
    mp.set_start_method("spawn")
    args = parser.parse_args()
    main(args)
