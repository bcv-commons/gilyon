#!/usr/bin/env python3
"""Validate Gilyon 0.1 documents: JSON Schema plus the cross-member rules the
schema cannot express.

Usage:  uv run --with jsonschema tools/validate.py examples/*.gilyon.json
Exit status 0 if every file is valid.

The kind of file is read from its content:

  annotation document   has `annotations`                    spec §4
  body document         has `entries`                        spec §16.2
  collection manifest   has `files`                          spec §16.1
  translation manifest  has `files` and `of`                 spec §16.3
  catalogue             has `collections` or `publishers`    spec §16.4

A manifest is checked with the files it lists: each exists, has the stated
SHA-256 and is valid, and body documents fit the annotation document they
belong to. A translation manifest is checked against the collection it names
when `ofManifest` leads to a local file. A translated body whose
`sourceDigest` no longer matches its source is reported as a warning. Files
at remote addresses are not fetched; they are reported as not checked.
"""
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema" / "gilyon-0.1.schema.json").read_text(encoding="utf-8"))
MANIFEST_SCHEMA = json.loads(
    (ROOT / "schema" / "gilyon-manifest-0.1.schema.json").read_text(encoding="utf-8"))
CATALOGUE_SCHEMA = json.loads(
    (ROOT / "schema" / "gilyon-catalogue-0.1.schema.json").read_text(encoding="utf-8"))
BODIES_SCHEMA = json.loads(
    (ROOT / "schema" / "gilyon-bodies-0.1.schema.json").read_text(encoding="utf-8"))
REGISTRY = Registry().with_resource(SCHEMA["$id"], Resource.from_contents(SCHEMA))
BASE_ONLY = {"Words", "Range", "Point"}
WARNINGS = []


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def check_bodies(bodies, where, errors, inherited_from=None, fixed_language=None):
    """Rules of spec §9 for one array of body objects."""
    seen = set()
    for i, b in enumerate(bodies):
        lang = b.get("language")
        if fixed_language and lang and lang != fixed_language:
            errors.append(f"{where}.body[{i}]: language {lang!r} in a body document for {fixed_language!r}")
        key = (lang or fixed_language, b.get("purpose"))
        if key in seen:
            errors.append(f"{where}.body[{i}]: second body for language {key[0]!r} and purpose {key[1]!r}")
        seen.add(key)
        if "translation" in b and not (b.get("translationOf") or inherited_from):
            errors.append(f"{where}.body[{i}]: translation without translationOf")
        if "translation" in b and not inherited_from and "status" not in b["translation"]:
            errors.append(f"{where}.body[{i}]: translation without status")


def strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield k
            yield from strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from strings(v)


def selector_words(sel):
    t = sel.get("type")
    if t == "Words":
        return list(sel.get("words", []))
    if t == "Range":
        return [sel.get("first"), sel.get("last")]
    if t == "Point":
        return [w for w in (sel.get("after"), sel.get("before")) if w]
    if t == "Composite":
        return [w for item in sel.get("items", []) for w in selector_words(item)]
    return []


def check_selector(sel, role, where, errors, level):
    t = sel.get("type")
    if t == "Composite":
        for i, item in enumerate(sel.get("items", [])):
            check_selector(item, role, f"{where}.items[{i}]", errors, level)
        return
    if t in BASE_ONLY and role != "base":
        errors.append(f"{where}: {t} selector on a text whose role is {role!r}")
    if t in BASE_ONLY and level == 0:
        errors.append(f"{where}: {t} selector in a Level 0 document")
    words = selector_words(sel)
    if len({w[0] for w in words}) > 1:
        errors.append(f"{where}: Hebrew and Greek identifiers mixed")
    elif len({w[:3] for w in words}) > 1:
        errors.append(f"{where}: words from more than one book")
    if t == "Words" and words != sorted(words):
        errors.append(f"{where}: words not in canonical order")
    if t == "Range" and sel["first"] > sel["last"]:
        errors.append(f"{where}: first follows last")
    if t == "Point" and len(words) == 2 and words[0] >= words[1]:
        errors.append(f"{where}: after does not precede before")
    for key in ("check", "lexemes"):
        allowed = set(words)
        if t == "Range":
            allowed = None
        for w in sel.get(key, {}):
            if allowed is not None and w not in allowed:
                errors.append(f"{where}: {key} names {w}, which the selector does not select")
            if allowed is None and not (sel["first"] <= w <= sel["last"]):
                errors.append(f"{where}: {key} names {w}, outside the range")


def check_target(tgt, doc, where, errors, top=True):
    texts = doc["texts"]
    level = doc["conformsTo"]
    if "annotation" in tgt:
        return None
    sel = tgt["selector"]
    if sel.get("type") == "Lexeme":
        return None
    name = tgt.get("text")
    if name not in texts:
        errors.append(f"{where}: text {name!r} is not declared")
        return None
    role = texts[name]["role"]
    check_selector(sel, role, f"{where}.selector", errors, level)
    word_level = bool(selector_words(sel))
    anch = tgt.get("anchoring")
    if top and word_level and not anch:
        errors.append(f"{where}: word-level selector without anchoring")
    if anch:
        if anch["status"] == "unresolved" and sel.get("type") != "Passage":
            errors.append(f"{where}: unresolved anchoring requires a Passage selector")
    return name


def expand(sel):
    """Return (lo, hi) bounds of a unit selector, or None."""
    words = selector_words(sel)
    return (min(words), max(words)) if words else None


def check_structure(ann, doc, where, errors):
    st = ann["structure"]
    if doc["conformsTo"] < 2:
        errors.append(f"{where}: structure in a document below Level 2")
    if ann["motivation"] != "classifying":
        errors.append(f"{where}: a structure requires motivation 'classifying'")
    if not any(c.startswith("gilyon:structure/") for c in ann.get("category", [])):
        errors.append(f"{where}: a structure requires a gilyon:structure/ category")
    tgt = ann["target"] if isinstance(ann["target"], dict) else ann["target"][0]
    role = doc["texts"].get(tgt.get("text"), {}).get("role", "base")
    ids = [u["id"] for u in st["units"]]
    if len(ids) != len(set(ids)):
        errors.append(f"{where}: duplicate unit ids")
    idset = set(ids)
    bounds = {}
    for i, u in enumerate(st["units"]):
        check_selector(u["selector"], role, f"{where}.units[{i}].selector", errors, 2)
        for j, k in enumerate(u.get("key", [])):
            check_selector(k, role, f"{where}.units[{i}].key[{j}]", errors, 2)
        if "parent" in u and u["parent"] not in idset:
            errors.append(f"{where}.units[{i}]: unknown parent {u['parent']!r}")
        bounds[u["id"]] = expand(u["selector"])
    parents = {u["id"]: u.get("parent") for u in st["units"]}

    def ancestors(x):
        seen = set()
        while parents.get(x) and x not in seen:
            seen.add(x)
            x = parents[x]
            yield x

    items = [(k, v) for k, v in bounds.items() if v]
    for a in range(len(items)):
        for b in range(a + 1, len(items)):
            (ia, (lo1, hi1)), (ib, (lo2, hi2)) = items[a], items[b]
            if hi1 < lo2 or hi2 < lo1:
                continue
            if ia in ancestors(ib) or ib in ancestors(ia):
                continue
            errors.append(f"{where}: units {ia!r} and {ib!r} overlap without a parent relation")
    for r in st.get("relations", []):
        for uid in r["units"]:
            if uid not in idset:
                errors.append(f"{where}: relation names unknown unit {uid!r}")
    for uid in st.get("focus", []):
        if uid not in idset:
            errors.append(f"{where}: focus names unknown unit {uid!r}")


def validate(path):
    errors = []
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [f"not valid JSON: {exc}"]
    for e in sorted(Draft202012Validator(SCHEMA).iter_errors(doc), key=lambda e: list(e.absolute_path)):
        errors.append("schema: /" + "/".join(map(str, e.absolute_path)) + ": " + e.message[:200])
    if errors:
        return errors
    for s in strings(doc):
        if unicodedata.normalize("NFC", s) != s:
            errors.append(f"string not in NFC: {s[:40]!r}")
    seen = set()
    separate = doc.get("bodies") == "separate"
    for i, ann in enumerate(doc["annotations"]):
        where = f"annotations[{i}]"
        if ann["id"] in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(ann["id"])
        targets = ann["target"] if isinstance(ann["target"], list) else [ann["target"]]
        for j, tgt in enumerate(targets):
            check_target(tgt, doc, f"{where}.target[{j}]", errors)
        for j, link in enumerate(ann.get("links", [])):
            if "target" in link:
                check_target(link["target"], doc, f"{where}.links[{j}].target", errors, top=False)
        if "structure" in ann:
            check_structure(ann, doc, where, errors)
        units = ann.get("structure", {}).get("units", [])
        rels = ann.get("structure", {}).get("relations", [])
        if separate:
            if "body" in ann or any("body" in x for x in units + rels):
                errors.append(f"{where}: body in a document that declares bodies 'separate'")
        else:
            if "body" not in ann and "structure" not in ann and ann["motivation"] != "highlighting":
                errors.append(f"{where}: no body")
            if "body" in ann:
                check_bodies(ann["body"], where, errors)
            for x in units + rels:
                if "body" in x:
                    check_bodies(x["body"], where + ".structure", errors)
    return errors


def validate_bodies(path):
    """A body document on its own (spec §16.2)."""
    errors = []
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [f"not valid JSON: {exc}"]
    v = Draft202012Validator(BODIES_SCHEMA, registry=REGISTRY)
    for e in sorted(v.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        errors.append("schema: /" + "/".join(map(str, e.absolute_path)) + ": " + e.message[:200])
    if errors:
        return errors
    for s in strings(doc):
        if unicodedata.normalize("NFC", s) != s:
            errors.append(f"string not in NFC: {s[:40]!r}")
    if doc["id"] == doc["of"]:
        errors.append("id equals of")
    if "translation" in doc and "translationOf" not in doc:
        errors.append("translation without translationOf")
    if "translation" in doc and "status" not in doc["translation"]:
        errors.append("translation without status")
    if doc.get("translationOf") == doc["meta"]["language"]:
        errors.append("translationOf names the document's own language")
    seen = set()
    for i, e in enumerate(doc["entries"]):
        key = (e["annotation"], e.get("unit"))
        if key in seen:
            errors.append(f"entries[{i}]: second entry for the same annotation and unit")
        seen.add(key)
        check_bodies(e["body"], f"entries[{i}]", errors, doc.get("translationOf"), doc["meta"]["language"])
        software = any(c.get("type") == "Software" for c in doc["meta"].get("creator", []))
        for j, b in enumerate(e["body"]):
            status = b.get("translation", {}).get("status") or doc.get("translation", {}).get("status")
            if status == "machine" and not software and not any(
                    c.get("type") == "Software" for c in b.get("creator", [])):
                errors.append(f"entries[{i}].body[{j}]: machine translation without a creator of type Software")
    return errors


def is_remote(ref):
    return "://" in ref or ref.startswith("//")


FETCH = None   # a tool that fetches remote files sets this to a function (base, ref) -> Path


def locate(base, ref):
    """The local file a URL reference leads to, or None when it is remote and nothing fetches it."""
    if FETCH is not None:
        return FETCH(base, ref)
    if is_remote(ref):
        return None
    return Path(base) / ref


def load_body_file(w, tag, b, base, version, doc, doc_name, errors):
    """One listed body document: file, checksum, validity, fit with its annotation document."""
    f = locate(base, b["path"])
    if f is None:
        WARNINGS.append(f"{b['path']}: remote, not checked")
        return None
    if not f.is_file():
        errors.append(f"{w}: {b['path']} not found")
        return None
    data = f.read_bytes()
    if hashlib.sha256(data).hexdigest() != b["sha256"]:
        errors.append(f"{w}: SHA-256 of {b['path']} differs from the manifest")
    errs = validate_bodies(f)
    errors.extend(f"{w}: {b['path']}: {e}" for e in errs)
    if errs:
        return None
    bd = json.loads(data)
    if bd["gilyon"] != version:
        errors.append(f"{w}: format version differs from the manifest")
    if bd["meta"]["language"] != tag:
        errors.append(f"{w}: meta.language is {bd['meta']['language']!r}")
    if "id" in b and b["id"] != bd["id"]:
        errors.append(f"{w}: id differs from the document's id")
    if doc is not None:
        if bd["of"] != doc["id"]:
            errors.append(f"{w}: 'of' is not the id of {doc_name}")
        units = {a["id"]: {u["id"] for u in a.get("structure", {}).get("units", [])} for a in doc["annotations"]}
        for i, e in enumerate(bd["entries"]):
            if e["annotation"] not in units:
                errors.append(f"{w}: entries[{i}] names an annotation that is not in {doc_name}")
            elif "unit" in e and e["unit"] not in units[e["annotation"]]:
                errors.append(f"{w}: entries[{i}] names unknown unit {e['unit']!r}")
    return bd


def is_translation(bd):
    return "translationOf" in bd or all("translationOf" in x for e in bd["entries"] for x in e["body"])


def warn_stale(source_bd, source, bd, path):
    src = {}
    for e in (source_bd or {}).get("entries", []):
        for x in e["body"]:
            src[(e["annotation"], e.get("unit"), x.get("purpose"))] = digest(x["value"])
    for e in bd["entries"]:
        for x in e["body"]:
            d = x.get("translation", {}).get("sourceDigest")
            frm = x.get("translationOf") or bd.get("translationOf")
            if d and frm == source and src.get((e["annotation"], e.get("unit"), x.get("purpose"))) != d:
                WARNINGS.append(f"{path}: translation of {e['annotation']} "
                                f"was made from another wording of the source (stale)")


def check_dirs(man, errors):
    dirs = [v["dir"] for v in man.get("languages", {}).values()]
    if len(dirs) != len(set(dirs)):
        errors.append("two languages share a folder")


def check_language_files(man, entry, doc, base, where, errors):
    """The body documents of one annotation document (spec §16.1, §16.2)."""
    source = man["sourceLanguage"]
    loaded = {}
    for tag, b in entry.get("bodies", {}).items():
        w = f"{where}.bodies[{tag}]"
        if tag not in man["languages"]:
            errors.append(f"{w}: language is not declared in languages")
            continue
        if not is_remote(b["path"]) and not b["path"].startswith(man["languages"][tag]["dir"] + "/"):
            errors.append(f"{w}: {b['path']} is not in folder {man['languages'][tag]['dir']!r}")
        bd = load_body_file(w, tag, b, base, man["gilyon"], doc, entry["path"], errors)
        if bd is None:
            continue
        if tag == source and ("translationOf" in bd or "translation" in bd):
            errors.append(f"{w}: the source language is marked as a translation")
        if tag != source and not is_translation(bd):
            errors.append(f"{w}: bodies in a language other than the source language without translationOf")
        loaded[tag] = bd
    if doc.get("bodies") != "separate":
        errors.append(f"{where}: {entry['path']} does not declare bodies 'separate'")
    need = [a["id"] for a in doc["annotations"] if "structure" not in a and a["motivation"] != "highlighting"]
    if source in loaded:
        have = {e["annotation"] for e in loaded[source]["entries"] if "unit" not in e}
        for a in need:
            if a not in have:
                errors.append(f"{where}: no body in the source language for {a}")
    elif need and (source not in entry.get("bodies", {}) or locate(base, entry["bodies"][source]["path"]) is not None):
        errors.append(f"{where}: no body document in the source language {source!r}")
    for tag, bd in loaded.items():
        warn_stale(loaded.get(source), source, bd, entry["bodies"][tag]["path"])


def load_json(path, schema, errors):
    try:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"not valid JSON: {exc}")
        return None
    v = Draft202012Validator(schema, registry=REGISTRY)
    for e in sorted(v.iter_errors(obj), key=lambda e: list(e.absolute_path)):
        errors.append("schema: /" + "/".join(map(str, e.absolute_path)) + ": " + e.message[:200])
    return None if errors else obj


_REF = re.compile(r"^([A-Z0-9]{3})(?: (\d{1,3})(?:[:.](\d{1,3}|title)[a-z]?)?(?:-(?:(\d{1,3})[:.])?(\d{1,3}|title)[a-z]?)?)?$")


def span(ref):
    """A reference (Appendix B) as (book, (chapter, verse), (chapter, verse)), or None."""
    m = _REF.match(ref) if isinstance(ref, str) else None
    if not m:
        return None
    book, c1, v1, c2, e = m.groups()
    num = lambda v: 0 if v == "title" else int(v)   # noqa: E731
    if c1 is None:
        return book, (0, 0), (999, 999)
    c1 = int(c1)
    if v1 is None:                       # JOS 1, JOS 1-3
        return book, (c1, 0), (int(e) if e else c1, 999)
    if e is None:                        # JOS 1:1
        return book, (c1, num(v1)), (c1, num(v1))
    return book, (c1, num(v1)), (int(c2) if c2 else c1, num(e))


def places(node):
    """The places the selectors under `node` point at: (book or None, first, last)."""
    if isinstance(node, list):
        for x in node:
            yield from places(x)
    elif isinstance(node, dict):
        if isinstance(node.get("ref"), str) and node.get("type") in ("Passage", "Words", "Range", "Point"):
            sp = span(node["ref"])
            if sp:
                yield sp
        elif node.get("type") in ("Words", "Range", "Point"):
            for w in selector_words(node):
                if isinstance(w, str) and re.fullmatch(r"[on]\d{11,12}", w):
                    cv = (int(w[3:6]), int(w[6:9]))
                    yield None, cv, cv
        for k, v in node.items():
            if k not in ("links", "body"):
                yield from places(v)


def check_coverage(entry, doc, where, errors):
    """`ref` covers every place the file's annotations target (spec §16.1)."""
    if "ref" not in entry:
        return
    refs = entry["ref"] if isinstance(entry["ref"], list) else [entry["ref"]]
    spans = [span(r) for r in refs]
    if None in spans:
        errors.append(f"{where}: ref is not a reference (Appendix B)")
        return
    for sp in spans:
        if sp[0] not in entry["books"]:
            errors.append(f"{where}: ref names {sp[0]}, which is not listed in books")
    for a in doc.get("annotations", []):
        for book, first, last in places([a.get("target"), a.get("structure")]):
            if not any((book is None or book == b) and lo <= first and last <= hi for b, lo, hi in spans):
                errors.append(f"{where}: {a.get('id')} targets a place outside ref")
                break


def check_files(man, files, base, prefix, seen, errors):
    """The annotation documents one manifest lists, with their body documents."""
    seen_paths, seen_ids = seen[0], seen[1]
    home, about = (seen[2], seen[3]) if len(seen) > 2 else ({}, [])
    for i, entry in enumerate(files):
        where = f"{prefix}files[{i}]"
        f = locate(Path(base), entry["path"])
        key = entry["path"] if f is None else str(f)
        if key in seen_paths:
            errors.append(f"{where}: path listed twice")
        seen_paths.add(key)
        if f is None:
            WARNINGS.append(f"{entry['path']}: remote, not checked")
            continue
        if not f.is_file():
            errors.append(f"{where}: {entry['path']} not found")
            continue
        data = f.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            errors.append(f"{where}: SHA-256 of {entry['path']} differs from the manifest")
        for e in validate(f):
            errors.append(f"{where}: {entry['path']}: {e}")
        try:
            doc = json.loads(data)
        except Exception:  # noqa: BLE001
            continue
        if doc.get("gilyon") != man["gilyon"]:
            errors.append(f"{where}: format version differs from the manifest")
        if doc.get("texts") != man["texts"]:
            errors.append(f"{where}: text declarations differ from the manifest")
        if doc.get("id") in seen_ids or doc.get("id") == man["id"]:
            errors.append(f"{where}: document id is not unique in the collection")
        seen_ids.add(doc.get("id"))
        if "id" in entry and entry["id"] != doc.get("id"):
            errors.append(f"{where}: id differs from the document's id")
        books = {t["selector"]["ref"].split(" ")[0]
                 for a in doc.get("annotations", [])
                 for t in (a["target"] if isinstance(a["target"], list) else [a["target"]])
                 if "ref" in t.get("selector", {})}
        if not books <= set(entry["books"]):
            errors.append(f"{where}: annotates {sorted(books - set(entry['books']))}, not listed in books")
        check_coverage(entry, doc, where, errors)
        for a in doc.get("annotations", []):
            home[a.get("id")] = key
            for t in (a["target"] if isinstance(a.get("target"), list) else [a.get("target")]):
                if isinstance(t, dict) and "annotation" in t:
                    about.append((where, key, a.get("id"), t["annotation"]))
        if "languages" in man:
            check_language_files(man, entry, doc, Path(base), where, errors)
        elif "bodies" in entry:
            errors.append(f"{where}: bodies listed, but the manifest declares no languages")
        # bodies 'separate' and no languages: a collection of anchors only (spec §16.2 rule 5)


def check_part(man, part, f, prefix, seen, errors):
    """One part manifest of a collection (spec §16.1, Parts). -> its file entries"""
    errs = []
    pm = load_json(f, MANIFEST_SCHEMA, errs)
    errors.extend(f"{prefix}{e}" for e in errs)
    if pm is None:
        return []
    if "partOf" not in pm:
        errors.append(f"{prefix}not a part manifest (no partOf)")
        return []
    if pm["partOf"] != man["id"]:
        errors.append(f"{prefix}partOf is not the id of the collection")
    if pm["gilyon"] != man["gilyon"]:
        errors.append(f"{prefix}format version differs from the collection's")
    for i, e in enumerate(pm["files"]):
        if not set(e["books"]) <= set(part["books"]):
            errors.append(f"{prefix}files[{i}]: books {sorted(set(e['books']) - set(part['books']))} "
                          f"are not listed for this part")
    if "files" in part and part["files"] != len(pm["files"]):
        errors.append(f"{prefix}the collection states {part['files']} files, the part lists {len(pm['files'])}")
    check_files(man, pm["files"], Path(f).parent, prefix, seen, errors)
    return pm["files"]


def all_files(man, base):
    """Every (file entry, folder its paths resolve against) of a collection, through its parts.
    Parts that cannot be read are skipped."""
    for e in man.get("files", []):
        yield e, Path(base)
    for part in man.get("parts", []):
        f = locate(Path(base), part["path"]) if isinstance(part, dict) and "path" in part else None
        if f is None or not f.is_file():
            continue
        try:
            pm = json.loads(f.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        for e in pm.get("files", []) if isinstance(pm, dict) else []:
            yield e, f.parent


def validate_manifest(path):
    errors = []
    man = load_json(path, MANIFEST_SCHEMA, errors)
    if man is None:
        return errors
    if "of" in man:
        return validate_translation_manifest(path, man)
    if "partOf" in man:
        return validate_part_alone(path, man)
    base = Path(path).parent
    seen = (set(), set(), {}, [])
    check_files(man, man.get("files", []), base, "", seen, errors)
    part_paths = set()
    for i, part in enumerate(man.get("parts", [])):
        where = f"parts[{i}]"
        if part["path"] in part_paths:
            errors.append(f"{where}: path listed twice")
        part_paths.add(part["path"])
        f = locate(base, part["path"])
        if f is None:
            WARNINGS.append(f"{part['path']}: remote, not checked")
            continue
        if not f.is_file():
            errors.append(f"{where}: {part['path']} not found")
            continue
        if hashlib.sha256(f.read_bytes()).hexdigest() != part["sha256"]:
            errors.append(f"{where}: SHA-256 of {part['path']} differs from the manifest")
        files = check_part(man, part, f, f"{where}: {part['path']}: ", seen, errors)
        n = sum(e.get("annotations", 0) for e in files)
        if "annotations" in part and files and all("annotations" in e for e in files) and part["annotations"] != n:
            errors.append(f"{where}: states {part['annotations']} annotations, its files state {n}")
    for where, key, aid, target in seen[3]:       # spec §16.5 rule 7
        if target in seen[2] and seen[2][target] != key:
            errors.append(f"{where}: {aid} targets an annotation that is in another file of the collection")
    if "languages" in man and man["sourceLanguage"] not in man["languages"]:
        errors.append("sourceLanguage is not declared in languages")
    check_dirs(man, errors)
    return errors


def validate_part_alone(path, pm):
    """A part manifest given on its own: checked with the collection manifest it names."""
    errors = []
    ref = pm.get("partOfManifest")
    cm = locate(Path(path).parent, ref) if ref else None
    if cm is None or not cm.is_file():
        WARNINGS.append("the collection's manifest is not available; the files were not checked")
        return errors
    man = json.loads(cm.read_text(encoding="utf-8"))
    mine = [p for p in man.get("parts", [])
            if (lambda f: f is not None and f.resolve() == Path(path).resolve())(locate(cm.parent, p["path"]))]
    if not mine:
        errors.append(f"{ref} does not list this part")
        return errors
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != mine[0]["sha256"]:
        errors.append("SHA-256 differs from the one the collection's manifest states")
    check_part(man, mine[0], path, "", (set(), set()), errors)
    return errors


def validate_translation_manifest(path, man):
    """A manifest that adds languages to a collection published elsewhere (spec §16.3)."""
    errors = []
    base = Path(path).parent
    check_dirs(man, errors)
    # the collection, when it can be read locally
    coll, coll_base, docs, source_bodies = None, None, {}, {}
    ref = man.get("ofManifest")
    cm = locate(base, ref) if ref else None
    if cm is not None and cm.is_file():
        coll_base = cm.parent
        coll = json.loads(cm.read_text(encoding="utf-8"))
        if "ofSha256" in man and man["ofSha256"] != hashlib.sha256(cm.read_bytes()).hexdigest():
            WARNINGS.append("the collection's manifest has changed since this translation was made (ofSha256)")
        if coll.get("id") != man["of"]:
            errors.append(f"'of' is not the id of the collection at {ref}")
        if "of" in coll:
            errors.append(f"{ref} is itself a translation manifest")
        if coll.get("gilyon") != man["gilyon"]:
            errors.append("format version differs from the collection's")
        for e, fbase in all_files(coll, coll_base):
            f = locate(fbase, e["path"])
            if f is None or not f.is_file():
                continue
            d = json.loads(f.read_text(encoding="utf-8"))
            docs[d["id"]] = (d, e["path"])
            sb = e.get("bodies", {}).get(coll.get("sourceLanguage"))
            sf = locate(fbase, sb["path"]) if sb else None
            if sf is not None and sf.is_file():
                source_bodies[d["id"]] = json.loads(sf.read_text(encoding="utf-8"))
        for tag in man["languages"]:
            if tag in coll.get("languages", {}):
                WARNINGS.append(f"language {tag!r} is also published by the collection itself")
    else:
        WARNINGS.append("the collection is not available locally; entries were not checked against it")
    seen = set()
    for i, entry in enumerate(man["files"]):
        where = f"files[{i}]"
        if entry["id"] in seen:
            errors.append(f"{where}: annotation document listed twice")
        seen.add(entry["id"])
        doc, doc_name = docs.get(entry["id"], (None, entry["id"]))
        if coll is not None and doc is None:
            errors.append(f"{where}: {entry['id']} is not an annotation document of the collection")
        for tag, b in entry["bodies"].items():
            w = f"{where}.bodies[{tag}]"
            if tag not in man["languages"]:
                errors.append(f"{w}: language is not declared in languages")
                continue
            if not is_remote(b["path"]) and not b["path"].startswith(man["languages"][tag]["dir"] + "/"):
                errors.append(f"{w}: {b['path']} is not in folder {man['languages'][tag]['dir']!r}")
            bd = load_body_file(w, tag, b, base, man["gilyon"], doc, doc_name, errors)
            if bd is None:
                continue
            if bd["of"] != entry["id"]:
                errors.append(f"{w}: 'of' is not {entry['id']}")
            if not is_translation(bd):
                errors.append(f"{w}: bodies of a translation without translationOf")
            if coll is not None:
                if tag == coll.get("sourceLanguage"):
                    errors.append(f"{w}: {tag!r} is the source language of the collection")
                warn_stale(source_bodies.get(entry["id"]), coll.get("sourceLanguage"), bd, b["path"])
    return errors


def validate_catalogue(path):
    """A catalogue: a list of collections, or an index of slices (spec §16.4)."""
    errors = []
    cat = load_json(path, CATALOGUE_SCHEMA, errors)
    if cat is None:
        return errors
    base = Path(path).parent
    seen = set()

    def listed(entry, where, parent=None):
        if entry["id"] in seen:
            errors.append(f"{where}: id listed twice")
        seen.add(entry["id"])
        ref = entry["manifest"]
        f = locate(base, ref)
        if f is None:
            WARNINGS.append(f"{ref}: remote, not checked")
            return
        if not f.is_file():
            errors.append(f"{where}: {ref} not found")
            return
        saved = list(WARNINGS)
        errs = validate_manifest(f)
        WARNINGS[:] = saved + [f"{ref}: {w}" for w in WARNINGS[len(saved):]]
        errors.extend(f"{where}: {ref}: {e}" for e in errs)
        if errs:
            return
        man = json.loads(f.read_text(encoding="utf-8"))
        if man["id"] != entry["id"]:
            errors.append(f"{where}: id differs from the manifest's id")
        if man["license"] != entry["license"]:
            errors.append(f"{where}: license differs from the manifest's")
        if "languages" in entry and set(entry["languages"]) != set(man.get("languages", {})):
            errors.append(f"{where}: languages differ from the manifest's")
        if parent is None and ("of" in man):
            errors.append(f"{where}: a translation manifest is listed as a collection")
        if parent is not None and man.get("of") != parent:
            errors.append(f"{where}: the manifest does not translate {parent}")
        if entry.get("sourceLanguage") not in (None, man.get("sourceLanguage")):
            errors.append(f"{where}: sourceLanguage differs from the manifest's")
        m = entry.get("checked", {}).get("manifestSha256")
        if m and m != hashlib.sha256(f.read_bytes()).hexdigest():
            WARNINGS.append(f"{ref}: changed since it was last checked")

    for i, c in enumerate(cat.get("collections", [])):
        listed(c, f"collections[{i}]")
        for j, t in enumerate(c.get("translations", [])):
            listed(t, f"collections[{i}].translations[{j}]", parent=c["id"])

    # an index names its slices; each slice is a catalogue of its own
    slices = [(f"languages[{k}]", v) for k, v in cat.get("languages", {}).items()]
    slices += [(f"publishers[{i}]", v) for i, v in enumerate(cat.get("publishers", []))]
    for where, v in slices:
        f = locate(base, v["path"])
        if f is None:
            WARNINGS.append(f"{v['path']}: remote, not checked")
        elif not f.is_file():
            errors.append(f"{where}: {v['path']} not found")
        else:
            saved = list(WARNINGS)
            errs = validate_catalogue(f)
            WARNINGS[:] = saved + [w for w in WARNINGS[len(saved):] if w not in saved]
            errors.extend(f"{where}: {v['path']}: {e}" for e in errs)
            n = len(json.loads(f.read_text(encoding="utf-8")).get("collections", []))
            if not errs and "collections" in v and v["collections"] != n:
                errors.append(f"{where}: states {v['collections']} collections, the slice has {n}")
    return errors


def kind(path):
    try:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return validate
    if isinstance(obj, dict):
        if "files" in obj or "parts" in obj:
            return validate_manifest
        if "collections" in obj or "publishers" in obj:
            return validate_catalogue
        if "entries" in obj:
            return validate_bodies
    return validate


def main(paths):
    bad = 0
    for p in paths:
        WARNINGS.clear()
        errs = kind(p)(p)
        print(("FAIL " if errs else "ok   ") + str(p))
        for e in errs:
            print("     " + e)
        for w in WARNINGS:
            print("     warning: " + w)
        bad += bool(errs)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
