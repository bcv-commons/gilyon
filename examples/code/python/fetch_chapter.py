#!/usr/bin/env python3
"""Fetch the annotations of one chapter of a Gilyon collection.
No dependencies beyond the Python standard library.

Only the manifest and the files for that chapter are fetched, and each file is
checked against the SHA-256 the manifest states.

Usage:
    python3 fetch_chapter.py <BOOK> <chapter> [manifest address] [language]
    python3 fetch_chapter.py JOS 1
    python3 fetch_chapter.py GEN 1 https://gilyon.org/0.1/examples/collection-parts/manifest.json en
"""
import sys

import gilyon

DEFAULT = "https://gilyon.org/collections/swe_svk/manifest.json"


def describe(selector):
    t = selector["type"]
    if t == "Point":
        return f"between {selector.get('after', '(verse start)')} and {selector.get('before', '(verse end)')}"
    if t == "Words":
        return "words " + " ".join(selector["words"])
    if t == "Range":
        return f"from {selector['first']} to {selector['last']}"
    if t == "Passage":
        return "passage " + selector["ref"]
    if t == "Lexeme":
        return "lexeme " + selector["lexeme"] + " (wherever it occurs)"
    return t


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: fetch_chapter.py <BOOK> <chapter> [manifest address] [language]")
    book, chapter = sys.argv[1], int(sys.argv[2])
    manifest_url = sys.argv[3] if len(sys.argv) > 3 else DEFAULT
    language = sys.argv[4] if len(sys.argv) > 4 else None

    manifest, annotations = gilyon.chapter(manifest_url, book, [chapter], language)
    print(f"{gilyon.title(manifest)}\n{manifest['license']}, {manifest.get('attribution', '')}\n")
    for a in annotations:
        for t in gilyon.targets(a):
            sel = t.get("selector", {})
            where = sel.get("ref", "")
            anchoring = t.get("anchoring", {})
            status = anchoring.get("status", "")
            if "tier" in anchoring:
                status += f", {anchoring['tier']} confidence"
            print(f"{where:<10} {describe(sel)}   [{status}]")
        for b in a.get("body", []):
            print(f"           {b['value']}")
    print(f"\n{len(annotations)} annotations")


if __name__ == "__main__":
    main()
