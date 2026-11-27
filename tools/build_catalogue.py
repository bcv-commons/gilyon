#!/usr/bin/env python3
"""The Gilyon catalogue: from registered publishers to the published slices.

People register publishers; everything else is derived (docs/catalogue.md).

  catalogue/config.json              id, title, admins (GitHub accounts)
  catalogue/publishers/<name>.json   one publisher: who answers for it, and
                                     where its manifests are            [edited by people]
  catalogue/state/<name>.json        what was found at those addresses, and
                                     the result of the checks           [written by `discover`]

Commands:

  discover [--date D] [--only NAME] [--offline]
        Read every manifest a publisher names, check the collection or
        translation behind it (tools/validate.py), and write
        catalogue/state/<name>.json. Remote files are fetched into a cache
        unless --offline is given.

  build --out DIR        Write the published catalogue into DIR:
                           index.json              languages and publishers, with counts
                           lang/<folder>.json      what can be read in one language
                           publisher/<name>.json   what one publisher provides
                           c/<key>.json            one collection with all its translations
                         <key> is the first 16 hex digits of the SHA-256 of the collection's id.
  build --check DIR      Fail if DIR is not what would be written.

  codeowners --out FILE | --check FILE
        The CODEOWNERS file: each publisher file is owned by its maintainers.

  owner-check --author LOGIN --base REF PATH...
        Whether LOGIN may make this change. Maintainers are read from the
        files at git revision REF, not from the proposed change.
        Exit 0 allowed, 1 refused, 2 allowed only with a catalogue admin.

  --dir DIR   the catalogue folder (default: catalogue)

Needs jsonschema (uv run --with jsonschema tools/build_catalogue.py ...).
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from jsonschema import Draft202012Validator

import validate as V

ROOT = Path(__file__).resolve().parent.parent
NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*\.json$")
LOGIN = r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$"
MAX_BYTES = 16 * 1024 * 1024

PUBLISHER_SCHEMA = {
    "type": "object",
    "required": ["name", "maintainers", "sources"],
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "id": {"type": "string", "pattern": r"^[A-Za-z][A-Za-z0-9+.-]*:\S+$"},
        "added": {"type": "string"},
        "status": {"enum": ["listed", "flagged", "withdrawn"]},
        "note": {"type": "string"},
        "maintainers": {
            "type": "array", "minItems": 1,
            "items": {"type": "object", "required": ["github"], "additionalProperties": False,
                      "properties": {"github": {"type": "string", "pattern": LOGIN},
                                     "name": {"type": "string"},
                                     "role": {"enum": ["publisher", "delegate"]},
                                     "since": {"type": "string"},
                                     "delegation": {"type": "string", "minLength": 1}}}},
        "sources": {
            "type": "array",
            "items": {"oneOf": [
                {"type": "object", "required": ["type", "manifests"], "additionalProperties": False,
                 "properties": {"type": {"const": "manifests"},
                                "hosting": {"enum": ["publisher", "republished"]},
                                "manifests": {"type": "array", "items": {"type": "string", "minLength": 1},
                                              "uniqueItems": True}}},
                # accommodated, not implemented: repositories of an owner that carry a topic
                {"type": "object", "required": ["type", "owner"], "additionalProperties": False,
                 "properties": {"type": {"const": "github"},
                                "owner": {"type": "string", "pattern": LOGIN},
                                "topic": {"type": "string"}}}]}},
    },
}


def dump(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


# ---------------------------------------------------------------- reading

def load(d):
    """-> (config, {name: publisher}, {name: state}, errors)"""
    d = Path(d)
    errors = []
    config = json.loads((d / "config.json").read_text(encoding="utf-8"))
    for a in config.get("admins", []):
        if not re.match(LOGIN, a):
            errors.append(f"config.json: admin {a!r} is not a GitHub account name")
    publishers, states = {}, {}
    for f in sorted((d / "publishers").glob("*")):
        if f.name.startswith("."):
            continue
        if not NAME.match(f.name):
            errors.append(f"publishers/{f.name}: file name must be lower-case letters, digits, '-' or '_', and end in .json")
            continue
        try:
            pub = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"publishers/{f.name}: not valid JSON: {exc}")
            continue
        errs = ["/" + "/".join(map(str, e.absolute_path)) + ": " + e.message[:160]
                for e in sorted(Draft202012Validator(PUBLISHER_SCHEMA).iter_errors(pub),
                                key=lambda e: list(e.absolute_path))]
        errors.extend(f"publishers/{f.name}: {e}" for e in errs)
        if not errs:
            publishers[f.stem] = pub
    for f in sorted((d / "state").glob("*.json")):
        if f.stem in publishers:
            states[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        else:
            errors.append(f"state/{f.name}: no publisher of that name")
    seen = {}
    for name, pub in publishers.items():
        for src in pub["sources"]:
            for m in src.get("manifests", []):
                if m in seen:
                    errors.append(f"publishers/{name}.json: {m} is also named by {seen[m]}")
                seen[m] = name
    return config, publishers, states, errors


# ---------------------------------------------------------------- fetching

class Mirror:
    """Remote files, fetched once into a folder laid out by address."""

    def __init__(self, root, offline=False):
        self.root = Path(root).resolve()
        self.offline = offline
        self.headers = {}
        self.failed = {}

    def url_of(self, path):
        try:
            parts = Path(path).resolve().relative_to(self.root).parts
        except ValueError:
            return None
        return f"{parts[0]}://{parts[1]}/" + "/".join(parts[2:]) if len(parts) >= 2 else None

    def path_of(self, url):
        u = urllib.parse.urlsplit(url)
        return self.root / u.scheme / u.netloc / urllib.parse.unquote(u.path.lstrip("/"))

    def locate(self, base, ref):
        if V.is_remote(ref):
            url = ref
        else:
            here = self.url_of(base)
            if here is None:
                return Path(base) / ref            # an ordinary local file
            url = urllib.parse.urljoin(here.rstrip("/") + "/", ref)
        u = urllib.parse.urlsplit(url)
        if u.scheme not in ("http", "https") or not u.netloc or ".." in u.path.split("/"):
            return None
        path = self.path_of(url)
        if not path.is_file() and not self.offline and url not in self.failed:
            self.fetch(url, path)
        return path

    def fetch(self, url, path):
        req = urllib.request.Request(url, headers={"User-Agent": "gilyon-catalogue-check",
                                                   "Origin": "https://gilyon.org"})
        data = None
        for attempt in (1, 2):   # one retry: a first request to a host sometimes times out
            try:
                with urllib.request.urlopen(req, timeout=20) as r:   # noqa: S310 (scheme checked above)
                    data = r.read(MAX_BYTES + 1)
                    if len(data) > MAX_BYTES:
                        raise ValueError("larger than 16 MB")
                    self.headers[url] = {k.lower(): v for k, v in r.headers.items()}
                break
            except urllib.error.HTTPError as exc:
                self.failed[url] = f"HTTP {exc.code}"
                return
            except Exception as exc:  # noqa: BLE001
                self.failed[url] = str(exc)[:200]
                data = None
        if data is None:
            return
        self.failed.pop(url, None)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def cors(self, url):
        h = self.headers.get(url)
        return None if h is None else h.get("access-control-allow-origin") in ("*", "https://gilyon.org")


# ---------------------------------------------------------------- discovery

def body_counts(man, base):
    counts = {"source": 0, "machine": 0, "reviewed": 0, "human": 0}
    source = man.get("sourceLanguage")
    for entry, fbase in V.all_files(man, base):
        for tag, b in entry.get("bodies", {}).items():
            f = V.locate(fbase, b["path"])
            if f is None or not f.is_file():
                continue
            try:
                bd = json.loads(f.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            default = bd.get("translation", {}).get("status")
            for e in bd.get("entries", []):
                for x in e.get("body", []):
                    if tag == source and "of" not in man:
                        counts["source"] += 1
                    else:
                        st = x.get("translation", {}).get("status") or default
                        if st in counts:
                            counts[st] += 1
    return {k: v for k, v in counts.items() if v}


def describe(ref, hosting, d, date, previous, mirror):
    """One manifest -> one entry of the state file."""
    old = previous.get(ref, {})
    f = V.locate(d, ref)
    remote = V.is_remote(ref)
    if f is None or not f.is_file():
        reason = (mirror.failed.get(ref) if mirror else None) or ("not fetched" if remote else "not found")
        entry = dict(old) if old.get("id") else {"manifest": ref}
        entry["manifest"] = ref
        entry["checked"] = {"date": date, "result": "unreachable", "note": reason}
        return flagged(entry, old, date, f"unreachable: {reason}")
    V.WARNINGS.clear()
    errors = V.validate_manifest(f)
    warnings = list(V.WARNINGS)
    data = f.read_bytes()
    try:
        man = json.loads(data)
    except Exception:  # noqa: BLE001
        man = {}
    entry = {"manifest": ref}
    for k in ("id", "of", "title", "license", "attribution", "sourceLanguage"):
        if isinstance(man, dict) and k in man:
            entry[k] = man[k]
    if not entry.get("id") or not entry.get("license"):
        entry["checked"] = {"date": date, "result": "failed", "note": (errors or ["not a manifest"])[0][:300]}
        return flagged(entry, old, date, entry["checked"]["note"])
    langs = man.get("languages", {})
    entry["languages"] = sorted(langs)
    entry["folders"] = {t: v["dir"] for t, v in sorted(langs.items())}
    listed = [(e, b) for e, b in V.all_files(man, f.parent) if isinstance(e, dict)] if isinstance(man, dict) else []
    files = [e for e, _ in listed]
    if "of" in man:
        status = {v.get("translation", {}).get("status") for v in langs.values()} - {None}
        if status:
            entry["translation"] = {"status": status.pop() if len(status) == 1 else "mixed", "evidence": "claimed"}
    else:
        entry["books"] = sorted({b for e in files for b in e.get("books", [])})
        entry["annotations"] = sum(e.get("annotations", 0) for e in files)
        levels = []
        for e, fbase in listed:
            df = V.locate(fbase, e["path"]) if "path" in e else None
            if df is not None and df.is_file():
                try:
                    levels.append(json.loads(df.read_text(encoding="utf-8")).get("conformsTo", 0))
                except Exception:  # noqa: BLE001
                    pass
        if levels:
            entry["level"] = max(levels)
        entry["hosting"] = hosting
    checks = ["reachable"]
    if not errors:
        checks += ["checksums", "valid"] + (["translation"] if "of" in man else [])
    cors = mirror.cors(ref) if (mirror and remote) else None
    if cors:
        checks.append("cors")
    checked = {"date": date, "result": "failed" if errors else "ok",
               "manifestSha256": hashlib.sha256(data).hexdigest(), "checks": checks}
    stale = sum("(stale)" in w for w in warnings)
    if stale:
        checked["stale"] = stale
    if not errors:
        bodies = body_counts(man, f.parent)
        if bodies:
            checked["bodies"] = bodies
    unchecked = [w for w in warnings if "not checked" in w or "not available" in w]
    if errors:
        checked["note"] = errors[0][:300]
    elif cors is False:
        checked["note"] = "the server does not allow cross-origin requests"
    elif unchecked:
        checked["note"] = f"{len(unchecked)} file(s) could not be checked: {unchecked[0][:160]}"
    entry["checked"] = checked
    if errors:
        return flagged(entry, old, date, errors[0][:300])
    if cors is False:
        return flagged(entry, old, date, checked["note"])
    entry["status"] = "listed"
    entry["added"] = old.get("added", date)
    return entry


def flagged(entry, old, date, reason):
    entry["status"] = "flagged"
    entry["flag"] = {"since": old.get("flag", {}).get("since", date), "reason": reason}
    entry["added"] = old.get("added", date)
    return entry


def discover(d, date, only=None, offline=False, cache=None):
    d = Path(d)
    config, publishers, states, errors = load(d)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    mirror = Mirror(cache or (ROOT / ".cache" / "catalogue"), offline=offline)
    V.FETCH = mirror.locate
    (d / "state").mkdir(exist_ok=True)
    for name, pub in publishers.items():
        if only and name != only:
            continue
        previous = {e["manifest"]: e for e in states.get(name, {}).get("entries", [])}
        entries, notes = [], []
        for src in pub["sources"]:
            if src["type"] != "manifests":
                notes.append(f"source of type {src['type']!r} is not implemented yet; nothing was read from it")
                continue
            for ref in src["manifests"]:
                entries.append(describe(ref, src.get("hosting", "publisher"), d, date, previous, mirror))
        state = {"publisher": name, "discovered": date, "entries": entries}
        if notes:
            state["notes"] = notes
        (d / "state" / f"{name}.json").write_bytes(dump(state))
        ok = sum(e["status"] == "listed" for e in entries)
        print(f"{name}: {len(entries)} manifest(s), {ok} listed, {len(entries) - ok} flagged")
        for e in entries:
            if e["status"] != "listed":
                print(f"   flagged {e['manifest']}: {e['flag']['reason'][:140]}")
    V.FETCH = None
    return 0


# ---------------------------------------------------------------- building

def key_of(collection_id):
    return hashlib.sha256(collection_id.encode("utf-8")).hexdigest()[:16]


def build(d, out_dir):
    """-> ({path relative to out_dir: bytes}, warnings)"""
    d, out_dir = Path(d), Path(out_dir).resolve()
    config, publishers, states, errors = load(d)
    if errors:
        raise SystemExit("\n".join(errors))
    warnings = []
    colls, trans, folders = {}, [], {}
    for name, pub in publishers.items():
        who = {"name": pub["name"], "type": "Organization"}
        if "id" in pub:
            who["id"] = pub["id"]
        for e in states.get(name, {}).get("entries", []):
            if "id" not in e:
                warnings.append(f"{name}: {e['manifest']} has never been read; not listed")
                continue
            e = dict(e, publisher=who, _pub=name)
            if pub.get("status", "listed") == "withdrawn":
                e["status"] = "withdrawn"
            for tag, folder in e.pop("folders", {}).items():
                if folders.setdefault(tag, folder) != folder:
                    warnings.append(f"{name}: {e['id']} keeps {tag!r} in folder {folder!r}; "
                                    f"the catalogue uses {folders[tag]!r}")
            if "of" in e:
                trans.append(e)
            elif e["id"] in colls:
                warnings.append(f"{name}: {e['id']} is already listed by {colls[e['id']]['_pub']}; ignored")
            else:
                colls[e["id"]] = e
    by_coll = {}
    for t in trans:
        if t["of"] not in colls:
            warnings.append(f"{t['_pub']}: {t['id']} translates a collection that is not in the catalogue; not listed")
            continue
        t["by"] = "publisher" if t["_pub"] == colls[t["of"]]["_pub"] else "third-party"
        by_coll.setdefault(t["of"], []).append(t)
    keys = {}
    for cid in colls:
        k = key_of(cid)
        if k in keys:
            raise SystemExit(f"two collection ids share the key {k}: {keys[k]} and {cid}")
        keys[k] = cid

    def manifest_from(ref, here):
        """A manifest reference as seen from a file in folder `here` of the output."""
        if V.is_remote(ref):
            return ref
        return Path(os.path.relpath((d / ref).resolve(), here)).as_posix()

    def public(e, here, with_translations=None):
        out = {k: v for k, v in e.items() if not k.startswith("_") and k != "of"}
        out["manifest"] = manifest_from(e["manifest"], here)
        if with_translations:
            out["translations"] = [public(t, here) for t in sorted(with_translations, key=lambda t: t["id"])]
        return out

    dates = [e["checked"]["date"][:10] for e in list(colls.values()) + trans if "checked" in e]
    head = {"gilyon": "0.1"}
    modified = max(dates) if dates else None

    def catalogue(cid, slice_by, value, items):
        cat = dict(head, id=cid, slice={"by": slice_by, "value": value})
        if modified:
            cat["modified"] = modified
        cat["collections"] = items
        return dump(cat)

    base_id = config["id"].rsplit("/", 1)[0]
    out = {}
    # one collection with all its translations
    for k, cid in sorted(keys.items()):
        out[f"c/{k}.json"] = catalogue(f"{base_id}/c/{k}.json", "collection", cid,
                                       [public(colls[cid], out_dir / "c", by_coll.get(cid))])
    # languages
    lang_index = {}
    tags = sorted({t for e in list(colls.values()) + trans for t in e.get("languages", [])})
    for tag in tags:
        folder = folders.get(tag, tag.lower())
        items = []
        n_trans = 0
        for cid in sorted(colls):
            ts = [t for t in by_coll.get(cid, []) if tag in t.get("languages", [])]
            if tag in colls[cid].get("languages", []) or ts:
                items.append(public(colls[cid], out_dir / "lang", ts))
                n_trans += len(ts)
        out[f"lang/{folder}.json"] = catalogue(f"{base_id}/lang/{folder}.json", "language", tag, items)
        lang_index[tag] = {"path": f"lang/{folder}.json", "collections": len(items), "translations": n_trans}
    # publishers
    pub_index = []
    for name, pub in sorted(publishers.items()):
        items, n_trans = [], 0
        for cid in sorted(colls):
            own = colls[cid]["_pub"] == name
            ts = by_coll.get(cid, []) if own else [t for t in by_coll.get(cid, []) if t["_pub"] == name]
            if own or ts:
                items.append(public(colls[cid], out_dir / "publisher", ts))
            n_trans += sum(t["_pub"] == name for t in by_coll.get(cid, []))
        out[f"publisher/{name}.json"] = catalogue(f"{base_id}/publisher/{name}.json", "publisher", pub["name"], items)
        row = {"name": pub["name"], "path": f"publisher/{name}.json",
               "collections": len(items), "translations": n_trans,
               "maintainers": pub["maintainers"], "status": pub.get("status", "listed")}
        for k in ("id", "added"):
            if k in pub:
                row[k] = pub[k]
        pub_index.append(row)
    index = dict(head, id=config["id"])
    if "title" in config:
        index["title"] = config["title"]
    if modified:
        index["modified"] = modified
    index["counts"] = {"collections": len(colls), "translations": sum(len(v) for v in by_coll.values()),
                       "publishers": len(publishers), "languages": len(tags)}
    index["collectionPath"] = "c/{key}.json"
    index["languages"] = lang_index
    index["publishers"] = pub_index
    out["index.json"] = dump(index)
    return out, warnings


def write_or_check(files, out_dir, check):
    out_dir = Path(out_dir)
    if check:
        have = {p.relative_to(out_dir).as_posix() for p in out_dir.rglob("*.json")} if out_dir.is_dir() else set()
        bad = [p for p, data in files.items() if not (out_dir / p).is_file() or (out_dir / p).read_bytes() != data]
        extra = sorted(have - set(files))
        for p in bad:
            print(f"{out_dir / p} is not what the catalogue gives; rebuild", file=sys.stderr)
        for p in extra:
            print(f"{out_dir / p} is no longer part of the catalogue; rebuild", file=sys.stderr)
        return 1 if bad or extra else 0
    for sub in ("c", "lang", "publisher"):
        if (out_dir / sub).is_dir():
            for old in (out_dir / sub).glob("*.json"):
                old.unlink()
    for p, data in files.items():
        (out_dir / p).parent.mkdir(parents=True, exist_ok=True)
        (out_dir / p).write_bytes(data)
    return 0


# ---------------------------------------------------------------- ownership

def codeowners(d):
    config, publishers, _, errors = load(d)
    if errors:
        raise SystemExit("\n".join(errors))
    rel = Path(d).resolve().relative_to(ROOT).as_posix()
    admins = " ".join("@" + a for a in config.get("admins", []))
    lines = ["# Generated by tools/build_catalogue.py codeowners. Do not edit by hand.",
             "# The last matching line decides. Catalogue admins own the folder; each publisher",
             "# file is owned by its maintainers and the admins.", ""]
    if admins:
        lines.append(f"/{rel}/ {admins}")
    for name, pub in sorted(publishers.items()):
        owners = " ".join("@" + m["github"] for m in pub["maintainers"])
        lines.append(f"/{rel}/publishers/{name}.json {owners} {admins}".rstrip())
    return ("\n".join(lines) + "\n").encode("utf-8")


def at_revision(ref, path):
    r = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, cwd=ROOT)
    return r.stdout if r.returncode == 0 else None


def owner_check(d, author, base, paths):
    """0 allowed, 1 refused, 2 needs an admin."""
    rel = Path(d).resolve().relative_to(ROOT).as_posix()
    raw = at_revision(base, f"{rel}/config.json")
    admins = {a.lower() for a in (json.loads(raw).get("admins", []) if raw else [])}
    low = author.lower()
    if low in admins:
        print(f"{author} is a catalogue admin")
        return 0
    worst = 0

    def say(level, word, p, why):
        nonlocal worst
        print(f"{word:<8}{p}: {why}")
        if level == 1 or (level == 2 and worst == 0):   # a refusal outweighs "needs an admin"
            worst = level

    for p in paths:
        p = Path(p).as_posix()
        if not p.startswith(rel + "/"):
            continue
        inner = p[len(rel) + 1:]
        if not inner.startswith("publishers/") or inner.endswith(".gitkeep"):
            say(1, "REFUSED", p, "written by the catalogue or its admins only")
            continue
        before = at_revision(base, p)
        if before is None:
            say(2, "ADMIN", p, "registering a publisher needs a catalogue admin")
            continue
        old = json.loads(before)
        if low not in {m["github"].lower() for m in old.get("maintainers", [])}:
            say(1, "REFUSED", p, f"{author} is not a maintainer of this publisher")
            continue
        f = ROOT / p
        if not f.is_file():
            say(2, "ADMIN", p, "removing a publisher needs a catalogue admin (set status 'withdrawn' instead)")
            continue
        new = json.loads(f.read_text(encoding="utf-8"))
        rest = lambda x: {k: v for k, v in x.items() if k not in ("sources", "note")}   # noqa: E731
        if rest(new) != rest(old):
            changed = sorted(k for k in set(rest(new)) | set(rest(old)) if rest(new).get(k) != rest(old).get(k))
            if changed == ["status"] and new.get("status") == "withdrawn":
                say(0, "ok", p, "withdrawn by its maintainer")
            else:
                say(2, "ADMIN", p, f"a change of {', '.join(changed)} needs a catalogue admin")
        else:
            say(0, "ok", p, "sources changed by a maintainer")
    return worst


# ---------------------------------------------------------------- command line

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("command", choices=["discover", "build", "codeowners", "owner-check"])
    ap.add_argument("--dir", default="catalogue")
    ap.add_argument("--out")
    ap.add_argument("--check")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--only")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--cache")
    ap.add_argument("--author")
    ap.add_argument("--base")
    ap.add_argument("paths", nargs="*")
    a = ap.parse_args()
    d = (ROOT / a.dir) if not Path(a.dir).is_absolute() else Path(a.dir)

    if a.command == "discover":
        return discover(d, a.date, a.only, a.offline, a.cache)
    if a.command == "owner-check":
        if not (a.author and a.base):
            ap.error("owner-check needs --author and --base")
        return owner_check(d, a.author, a.base, a.paths)
    if a.command == "codeowners":
        data = codeowners(d)
        if a.check:
            if not Path(a.check).is_file() or Path(a.check).read_bytes() != data:
                print(f"{a.check} is not what the publisher files give; rebuild it", file=sys.stderr)
                return 1
            return 0
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_bytes(data)
        else:
            sys.stdout.write(data.decode("utf-8"))
        return 0
    target = a.check or a.out
    files, warnings = build(d, target or ".")
    for w in warnings:
        print("warning: " + w, file=sys.stderr)
    if a.check:
        return write_or_check(files, a.check, True)
    if a.out:
        return write_or_check(files, a.out, False)
    sys.stdout.write(files["index.json"].decode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
