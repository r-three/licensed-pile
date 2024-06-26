"""Shared utilities like string processing."""

import os


# We don't use snake case as the string methods added in PIP616 are named like this.
def removeprefix(s: str, prefix: str) -> str:
    """In case we aren't using python >= 3.9"""
    if s.startswith(prefix):
        return s[len(prefix) :]
    return s[:]


# We don't use snake case as the string methods added in PIP616 are named like this.
def removesuffix(s: str, suffix: str) -> str:
    """In case we aren't using python >= 3.9"""
    # Check for suffix to avoid calling s[:-0] for an empty string.
    if suffix and s.endswith(suffix):
        return s[: -len(suffix)]
    return s[:]


def dolma_input(input_path: str, filepattern: str) -> str:
    if os.path.exists(input_path) and os.path.isfile(input_path):
        return input_path
    return os.path.join(input_path, "documents", filepattern)


def dolma_output(output_path: str):
    if os.path.basename(output_path) != "documents":
        return os.path.join(output_path, "documents")
    return output_path
