"""Reading Gilyon collections: a small client, standard library only.

    catalogue(index_url)                       the catalogue's index
    chapter(manifest_url, book, chapters)      the annotations a passage needs (spec §16.5)
    bodies(...)                                is done inside chapter(): pass language="en"

Nothing here knows about a Bible translation. Placing an annotation in a
translation needs that translation's text and a word alignment; see
show_in_edition.py.
"""
import hashlib
import json
import re
import urllib.parse
import urllib.request

CATALOGUE = "https://gilyon.org/collections/index.json"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "gilyon-example"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def get_json(url, sha256=None):
    """Fetch JSON; with `sha256`, refuse a file that is not the one the manifest states."""
    data = get(url)
    if sha256 and hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError(f"{url}: not the file the manifest states (SHA-256 differs)")
    return json.loads(data)


def join(base, ref):
    return urllib.parse.urljoin(base, ref)


# ---------------------------------------------------------------- references (spec Appendix B)

_REF = re.compile(r"^([A-Z0-9]{3})(?: (\d{1,3})(?:[:.](\d{1,3}|title)[a-z]?)?(?:-(?:(\d{1,3})[:.])?(\d{1,3}|title)[a-z]?)?)?$")


def span(ref):
    """'JOS 1:1-2:5' -> ('JOS', (1, 1), (2, 5)); a whole chapter runs from verse 0 to 999."""
    m = _REF.match(ref)
    if not m:
        raise ValueError(f"not a reference: {ref!r}")
    book, c1, v1, c2, e = m.groups()
    num = lambda v: 0 if v == "title" else int(v)   # noqa: E731
    if c1 is None:
        return book, (0, 0), (999, 999)
    c1 = int(c1)
    if v1 is None:
        return book, (c1, 0), (int(e) if e else c1, 999)
    if e is None:
        return book, (c1, num(v1)), (c1, num(v1))
    return book, (c1, num(v1)), (int(c2) if c2 else c1, num(e))


def overlaps(ref, book, chapters):
    b, first, last = span(ref)
    return b == book and any(first[0] <= c <= last[0] for c in chapters)


# ---------------------------------------------------------------- the catalogue (spec §16.4)

def catalogue(index_url=CATALOGUE, language=None):
    """The collections of a catalogue: all of them, or those readable in one language."""
    index = get_json(index_url)
    if language:
        entry = index["languages"].get(language)
        slices = [entry["path"]] if entry else []
    else:
        slices = [p["path"] for p in index["publishers"]]
    seen, out = set(), []
    for path in slices:
        url = join(index_url, path)
        for c in get_json(url)["collections"]:
            if c["id"] not in seen:
                seen.add(c["id"])
                out.append(dict(c, manifest=join(url, c["manifest"])))   # absolute address
    return out


# ---------------------------------------------------------------- one passage of a collection (spec §16.5)

def files_for(manifest_url, book, chapters):
    """-> (manifest, [(file entry, address its paths resolve against), ...])

    Only the files whose stated coverage (`ref`) overlaps the chapters, and the
    files of the book that state none. `chapters` are chapters of the base text.
    """
    manifest = get_json(manifest_url)
    listed = [(e, manifest_url) for e in manifest.get("files", [])]
    for part in manifest.get("parts", []):
        if book in part["books"]:                          # read only the part for this book
            url = join(manifest_url, part["path"])
            listed += [(e, url) for e in get_json(url, part["sha256"])["files"]]
    wanted = []
    for entry, base in listed:
        if book not in entry["books"]:
            continue
        refs = entry.get("ref")
        refs = [refs] if isinstance(refs, str) else refs
        if refs is None or any(overlaps(r, book, chapters) for r in refs):
            wanted.append((entry, base))
    return manifest, wanted


def chapter(manifest_url, book, chapters, language=None):
    """The annotations for `chapters` of `book`, each with its wording where there is one.

    -> (manifest, [annotation, ...]). An annotation gets `body` from the body
    document of `language`, else of the collection's source language (spec §16.2).
    """
    manifest, wanted = files_for(manifest_url, book, chapters)
    source = manifest.get("sourceLanguage")
    out = []
    for entry, base in wanted:
        doc = get_json(join(base, entry["path"]), entry["sha256"])
        wording = {}
        for tag in (source, language):                     # the requested language wins
            b = entry.get("bodies", {}).get(tag) if tag else None
            if b:
                for e in get_json(join(base, b["path"]), b["sha256"])["entries"]:
                    if "unit" not in e:
                        wording[e["annotation"]] = (tag, e["body"])
        for a in doc["annotations"]:
            if "body" not in a and a["id"] in wording:
                tag, body = wording[a["id"]]
                a = dict(a, body=[dict(x, language=x.get("language", tag)) for x in body])
            out.append(a)
    return manifest, out


def title(obj, language="en"):
    t = obj.get("title", "")
    if isinstance(t, dict):
        return t.get(language) or next(iter(t.values()), "")
    return t


def targets(annotation):
    t = annotation.get("target")
    return t if isinstance(t, list) else [t] if t else []


def word_place(word_id):
    """'o060010010051' -> (chapter, verse) of the base text."""
    return int(word_id[3:6]), int(word_id[6:9])
