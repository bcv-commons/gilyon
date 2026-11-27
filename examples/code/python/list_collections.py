#!/usr/bin/env python3
"""List the annotation collections in the Gilyon catalogue.
No dependencies beyond the Python standard library.

Usage:
    python3 list_collections.py            every collection
    python3 list_collections.py sv         those that can be read in Swedish (a BCP 47 tag)
"""
import sys

import gilyon


def main():
    language = sys.argv[1] if len(sys.argv) > 1 else None
    collections = gilyon.catalogue(language=language)
    if not collections:
        print("No collection" + (f" in {language!r}." if language else "."))
    for c in collections:
        print(gilyon.title(c))
        print(f"  manifest:    {c['manifest']}")
        print(f"  licence:     {c['license']}" + (f"  ({c['attribution']})" if c.get("attribution") else ""))
        print(f"  books:       {' '.join(c.get('books', []))}   annotations: {c.get('annotations', '?')}")
        print(f"  languages:   {', '.join(c.get('languages', [])) or 'none: anchors only, no wording'}")
        for t in c.get("translations", []):
            print(f"  translation: {', '.join(t['languages'])} by {t.get('publisher', {}).get('name', '?')} ({t.get('by', '?')})")
        checked = c.get("checked", {})
        print(f"  checked:     {checked.get('date', '?')} {checked.get('result', '?')}; status {c.get('status', 'listed')}")


if __name__ == "__main__":
    main()
