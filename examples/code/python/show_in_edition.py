#!/usr/bin/env python3
"""Show the annotations of a Gilyon collection in a chapter of a Bible translation.
No dependencies beyond the Python standard library (and the copy of verse-text beside this file).

A Gilyon annotation points at Hebrew or Greek words. To show it in a translation
this script fetches, just in time:

  1. the chapter's text, from helloAO, read with bcv-commons/bibles' verse-text;
  2. the word alignment of that translation (bcv-commons/compact-alignments, CC0),
     after checking that it was made on exactly this text (the text fingerprint);
  3. the Gilyon files for the chapter (the manifest says which);

and then puts each annotation where its anchor words are rendered.

Usage:
    python3 show_in_edition.py <BOOK> <chapter> [options]
    python3 show_in_edition.py JOS 1
    python3 show_in_edition.py GEN 1 --collection https://gilyon.org/0.1/examples/collection-parts/manifest.json --language en

Options (defaults: the Berean Standard Bible):
    --collection URL   manifest of the Gilyon collection
    --language TAG     language of the wording to show, where the collection has it
    --helloao ID       the translation's id at bible.helloao.org          (BSB)
    --alignment NAME   its folder in compact-alignments                   (eng_BSB)
    --iso CODE         its ISO 639-3 code                                 (eng)
    --scheme NAME      its verse numbering: eng, org, orgw, vul, ...      (eng)
"""
import argparse
import hashlib
import json
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "verse_text"))
from bcv_tokenize import tokenize                       # noqa: E402
from bcv_written import tokenize_written                # noqa: E402
from helloao_to_usj import merge_book_usj               # noqa: E402
from verse_text import extract_usj                      # noqa: E402

import gilyon                                           # noqa: E402

HELLOAO = "https://bible.helloao.org/api"
ALIGN = "https://huggingface.co/datasets/bcv-commons/compact-alignments/resolve/main"
ALIGN_META = "https://huggingface.co/datasets/bcv-commons/compact-alignments-meta/resolve/main"
DEFAULT = "https://gilyon.org/collections/swe_svk/manifest.json"
MARKS = "⁰¹²³⁴⁵⁶⁷⁸⁹"


def optional(url):
    try:
        return gilyon.get(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def mark(n):
    return "⁽" + "".join(MARKS[int(d)] for d in str(n)) + "⁾"


# ---------------------------------------------------------------- 1. the chapter's text

def chapter_text(helloao_id, book, chapter):
    """-> {verse number: text}, the verse text every bcv-commons tool agrees on."""
    data = json.loads(gilyon.get(f"{HELLOAO}/{helloao_id}/{book}/{chapter}.json"))
    usj = merge_book_usj(book, [data])
    return {int(v["verse"]): v["text"] for v in extract_usj(usj).get(str(chapter), [])}


def chapter_fingerprint(verses):
    lines = []
    for v in sorted(verses):
        tokens = tokenize(verses[v])
        if tokens:
            lines.append(f"{v}:{' '.join(tokens)}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- 2. the alignment

def alignment(iso, name, book, chapter, fingerprint):
    """-> ({base-text verse: {word key: [token position, ...]}}, message)

    The alignment file is named by the fingerprint of the text it was made on. We
    take the latest one for the book and use it only if our chapter is that text.
    """
    folder = f"{iso[0]}/{iso}/{name}"
    listing = optional(f"{ALIGN_META}/{folder}/_fingerprints.txt")
    line = next((ln.split() for ln in (listing or b"").decode().splitlines() if ln.startswith(book + " ")), None)
    if line is None:
        return {}, f"no alignment of {book} is published for {name}"
    file_hash, chapters, n = line[1], {}, 0
    for item in line[3:]:                                  # 'da348', or '5:1ab2c' where the sequence breaks
        if ":" in item:
            n, item = int(item.split(":")[0]) - 1, item.split(":")[1]
        n += 1
        chapters[n] = item
    if chapters.get(chapter) != fingerprint[:5]:
        return {}, "the alignment was made on another wording of this chapter, so it is not used"
    keys = json.loads(gilyon.get(f"{ALIGN}/_index/{book}_keys.json"))        # verse -> the word keys, in order
    array = json.loads(gilyon.get(f"{ALIGN}/{folder}/{book}_{file_hash}.json"))
    out = {}
    for (ref, verse_keys), compact in zip(keys.items(), array):
        c, v = ref.split(" ")[1].split(":")
        words = {}
        for part in compact.split():                       # '3:5-6' = word 3 is rendered by tokens 5 and 6
            ordinal, tokens = part.split(":")
            positions = []
            for piece in tokens.split(","):
                lo, _, hi = piece.partition("-")
                positions += range(int(lo), int(hi or lo) + 1)
            for key in verse_keys[int(ordinal)].split("+"):
                words[key] = positions
        out[(int(c), int(v))] = (verse_keys, words)
    return out, f"text fingerprint {fingerprint[:5]} matches the aligned text"


def verse_map(scheme):
    """Base-text verse -> the translation's verse, where the numbering differs."""
    if scheme == "org":
        return {}
    data = optional(f"{ALIGN}/_index/_versification_{scheme}.json")
    return json.loads(data)["map"] if data else {}


def edition_place(vmap, book, chapter, verse):
    ref = vmap.get(f"{book} {chapter}:{verse}")
    if ref is None:
        return chapter, verse
    c, v = ref.split(" ")[1].split(":")
    return (int(c), None) if v == "title" else (int(c), int(v))


def base_chapters(vmap, book, chapter):
    """The chapters of the base text a chapter of the translation draws on (spec §16.5 rule 8)."""
    out = {chapter}
    for spine, edition in vmap.items():
        if spine.startswith(book + " ") and edition.startswith(f"{book} {chapter}:"):
            out.add(int(spine.split(" ")[1].split(":")[0]))
    return sorted(out)


# ---------------------------------------------------------------- 3. placing an annotation

def place(selector, aligned):
    """-> (base-text (chapter, verse), token position to put the mark after or None, how)"""
    kind = selector["type"]
    if kind == "Passage":
        _, first, _ = gilyon.span(selector["ref"])
        return first, None, "verse"
    if kind == "Point":
        ids = [selector[k] for k in ("after", "before") if k in selector]
    elif kind == "Words":
        ids = selector["words"]
    elif kind == "Range":
        ids = [selector["first"], selector["last"]]
    else:
        return None, None, "no place"
    where = gilyon.word_place(ids[0])
    verse_keys, words = aligned.get(where, ([], {}))
    content = [k for group in verse_keys for k in group.split("+")]      # the verse's content words, in order

    def tokens(word_id, side):
        """Token positions of a word; of the nearest content word on `side` if it is a function word."""
        key = word_id[1:]
        if key not in content:
            near = [k for k in content if (k < key if side < 0 else k > key)]
            if not near:
                return None
            key = near[-1] if side < 0 else near[0]
        return words.get(key)

    if kind == "Point":
        after = tokens(selector["after"], -1) if "after" in selector else None
        before = tokens(selector["before"], +1) if "before" in selector else None
        if after and before and max(after) < min(before):
            return where, max(after), "between its two anchor words"
        if after and not before:
            return where, max(after), "after its anchor word"
        if before and not after:
            return where, min(before) - 1, "before its anchor word"
        if after and before:
            return where, None, "verse (the two anchor words come in the other order here)"
        return where, None, "verse (anchor words not aligned)"
    if kind == "Range":
        lo, hi = selector["first"][1:], selector["last"][1:]
        found = [p for k in content if lo <= k <= hi for p in words.get(k, [])]
    else:
        found = [p for w in ids for p in (tokens(w, 0) or [])]
    if found:
        return where, max(found), "after the words that render it"
    return where, None, "verse (words not aligned)"


def with_marks(text, marks):
    """The verse text with a mark after each token position (-1: before the first word; None: at the end)."""
    written = tokenize_written(text)
    cut, pos = {}, 0
    for i, token in enumerate(written):                    # where each token ends in the text
        at = text.find(token, pos)
        if at < 0:
            cut = None
            break
        pos = at + len(token)
        cut[i] = pos
    out, tail = text, ""
    inserts = {}
    for position, label in marks:
        if position is None or cut is None or (position >= 0 and position not in cut):
            tail += label
        else:
            inserts.setdefault(0 if position < 0 else cut[position], []).append(label)
    for at in sorted(inserts, reverse=True):
        out = out[:at] + "".join(inserts[at]) + out[at:]
    return out + tail


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("book")
    ap.add_argument("chapter", type=int)
    ap.add_argument("--collection", default=DEFAULT)
    ap.add_argument("--language")
    ap.add_argument("--helloao", default="BSB")
    ap.add_argument("--alignment", default="eng_BSB")
    ap.add_argument("--iso", default="eng")
    ap.add_argument("--scheme", default="eng")
    a = ap.parse_args()

    verses = chapter_text(a.helloao, a.book, a.chapter)
    aligned, message = alignment(a.iso, a.alignment, a.book, a.chapter, chapter_fingerprint(verses))
    vmap = verse_map(a.scheme)
    manifest, annotations = gilyon.chapter(a.collection, a.book, base_chapters(vmap, a.book, a.chapter), a.language)

    print(f"{a.book} {a.chapter} in {a.helloao}, with: {gilyon.title(manifest)}")
    print(f"Annotations: {manifest['license']}, {manifest.get('attribution', '')}")
    print(f"Alignment: bcv-commons/compact-alignments ({a.alignment}); {message}\n")

    by_verse, notes, elsewhere = {}, [], []
    for ann in annotations:
        for target in gilyon.targets(ann):
            selector = target.get("selector", {})
            where, position, how = place(selector, aligned)
            wording = " / ".join(b["value"] for b in ann.get("body", [])) or "(no wording published)"
            status = target.get("anchoring", {}).get("status", "")
            if where is None:
                elsewhere.append(f"{selector.get('lexeme', selector.get('type'))}: {wording}")
                continue
            c, v = edition_place(vmap, a.book, *where)
            if c != a.chapter or (v is not None and v not in verses):
                continue                                   # not in the chapter shown (spec §16.5 rule 10)
            label = ann.get("source", {}).get("noteId") or ann["motivation"]
            notes.append(f"{mark(len(notes) + 1)} {label}: {wording}\n      placed {how}; anchor {status}")
            by_verse.setdefault(v, []).append((position, mark(len(notes))))

    for v in sorted(verses):
        print(f"{v:>3} {with_marks(verses[v], by_verse.get(v, []))}")
    print()
    print("\n".join(notes))
    for line in elsewhere:
        print(f"  * {line}")


if __name__ == "__main__":
    main()
