#!/usr/bin/env python3
"""Build the gilyon.org site into `_site/`.

Usage:  uv run --with markdown --with jsonschema tools/build_site.py
        (or: pip install -r requirements.txt && python3 tools/build_site.py)

Every file is laid out at its permanent address. The table below is the single
place where those addresses are decided:

  /                           README.md
  /0.1/                       spec/gilyon-0.1.md
  /0.1/spec.md                the same, as written
  /0.1/schema.json            schema/gilyon-0.1.schema.json
  /0.1/manifest.schema.json   schema/gilyon-manifest-0.1.schema.json
  /0.1/bodies.schema.json     schema/gilyon-bodies-0.1.schema.json
  /0.1/catalogue.schema.json  schema/gilyon-catalogue-0.1.schema.json
  /0.1/context.jsonld         context/gilyon-0.1.context.jsonld
  /0.1/examples/...           examples/...
  /registries/<name>.json     registries/<name>.json
  /ns                         site/ns.md
  /docs/<name>                docs/<name>.md
  /governance                 GOVERNANCE.md
  /collections/               site/collections/index.md
  /collections/index.json     the catalogue: an index of its slices, built from
  /collections/lang/..., /publisher/..., /c/...    catalogue/ by tools/build_catalogue.py
  /collections/<name>/...     collections/<name>/... (collections hosted on this site)
  /LICENSE.txt, /LICENSES/... LICENSE, LICENSES/

The build fails if a schema's `$id` differs from the address it is served at,
or if a link between pages points at a file that is not part of the site.
"""
import html
import json
import posixpath
import re
import shutil
import sys
from pathlib import Path

import markdown

import build_catalogue

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
ORIGIN = "https://gilyon.org"
VERSION = "0.1"

# source (relative to the repository) -> address on the site
PAGES = {
    "README.md": "/",
    f"spec/gilyon-{VERSION}.md": f"/{VERSION}/",
    "GOVERNANCE.md": "/governance",
    "site/ns.md": "/ns",
    "site/collections/index.md": "/collections/",
}
FILES = {
    f"spec/gilyon-{VERSION}.md": f"/{VERSION}/spec.md",
    f"schema/gilyon-{VERSION}.schema.json": f"/{VERSION}/schema.json",
    f"schema/gilyon-manifest-{VERSION}.schema.json": f"/{VERSION}/manifest.schema.json",
    f"schema/gilyon-bodies-{VERSION}.schema.json": f"/{VERSION}/bodies.schema.json",
    f"schema/gilyon-catalogue-{VERSION}.schema.json": f"/{VERSION}/catalogue.schema.json",
    f"context/gilyon-{VERSION}.context.jsonld": f"/{VERSION}/context.jsonld",
    "site/_headers": "/_headers",
    "site/_redirects": "/_redirects",
    "LICENSE": "/LICENSE.txt",
}

NAV = [("Gilyon", "/"), ("Specification", f"/{VERSION}/"), ("Overview", "/docs/overview"),
       ("Guide", "/docs/guide"), ("Collections", "/collections/"), ("Open issues", "/docs/open-issues")]

CSS = """
:root{--bg:#fbfaf7;--fg:#1d1c1a;--muted:#6a665e;--line:#dedad0;--accent:#7a3b12;--code:#f1eee6}
@media (prefers-color-scheme:dark){:root{--bg:#171614;--fg:#e9e6df;--muted:#a09a8e;--line:#3a372f;--accent:#e0a36a;--code:#24221e}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.6 Georgia,'Iowan Old Style','Times New Roman',serif}
header{border-bottom:1px solid var(--line)}
nav{max-width:52rem;margin:0 auto;padding:.8rem 1.2rem;display:flex;flex-wrap:wrap;gap:.3rem 1.2rem;font:15px/1.4 system-ui,sans-serif}
nav a{color:var(--muted);text-decoration:none}nav a:first-child{color:var(--fg);font-weight:600}
nav a:hover{color:var(--accent)}
main{max-width:52rem;margin:0 auto;padding:1.5rem 1.2rem 4rem}
.draft{font:14px/1.4 system-ui,sans-serif;color:var(--muted);border:1px solid var(--line);border-radius:6px;padding:.5rem .8rem;margin-bottom:1.5rem}
h1,h2,h3,h4{font-family:system-ui,sans-serif;line-height:1.25;margin:2em 0 .6em}
h1{font-size:1.9rem;margin-top:.5em}h2{font-size:1.35rem;border-bottom:1px solid var(--line);padding-bottom:.25em}h3{font-size:1.1rem}
a{color:var(--accent)}
code,pre{font:14px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--code);border-radius:4px}
code{padding:.1em .3em}pre{padding:.8rem 1rem;overflow-x:auto}pre code{padding:0;background:none}
table{border-collapse:collapse;display:block;overflow-x:auto;margin:1em 0;font-size:.93em}
th,td{border:1px solid var(--line);padding:.4em .7em;text-align:left;vertical-align:top}
th{font-family:system-ui,sans-serif;font-size:.9em;background:var(--code)}
footer{max-width:52rem;margin:0 auto;padding:1rem 1.2rem 3rem;color:var(--muted);font:14px/1.5 system-ui,sans-serif;border-top:1px solid var(--line)}
"""

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="canonical" href="{canonical}">
<style>{css}</style>
</head>
<body>
<header><nav>{nav}</nav></header>
<main>
<div class="draft">Working Draft {version}. Not yet reviewed outside the bcv-commons team; anything may change before 1.0.</div>
{body}
</main>
<footer>Gilyon, the bcv-commons team. Text: CC BY 4.0. Tools: MIT.
<a href="/LICENSE.txt">Licence</a> · <a href="https://github.com/bcv-commons/gilyon">Source</a></footer>
</body>
</html>
"""


def out_path(address):
    """File under _site that serves `address`."""
    if address.endswith("/"):
        return OUT / address.lstrip("/") / "index.html"
    if posixpath.splitext(address)[1]:
        return OUT / address.lstrip("/")
    return OUT / (address.lstrip("/") + ".html")   # Cloudflare Pages serves /x from /x.html


def main():
    pages, files = dict(PAGES), dict(FILES)
    for p in sorted((ROOT / "docs").glob("*.md")):
        pages[f"docs/{p.name}"] = f"/docs/{p.stem}"
    for p in sorted((ROOT / "registries").glob("*.json")):
        files[f"registries/{p.name}"] = f"/registries/{p.name}"
    for p in sorted((ROOT / "examples").rglob("*.json")):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith("examples/code/"):               # scripts, read on GitHub
            continue
        files[rel] = f"/{VERSION}/{rel}"
    for p in sorted((ROOT / "collections").rglob("*.json")):      # collections hosted here
        rel = p.relative_to(ROOT).as_posix()
        files[rel] = f"/{rel}"
    for p in sorted((ROOT / "LICENSES").glob("*")):
        files[f"LICENSES/{p.name}"] = f"/LICENSES/{p.name}"

    errors = []

    # a schema is served at the address it names
    for src, address in files.items():
        if src.startswith("schema/"):
            sid = json.loads((ROOT / src).read_text(encoding="utf-8")).get("$id")
            if sid != ORIGIN + address:
                errors.append(f"{src}: $id {sid!r} is not {ORIGIN + address!r}")

    # where a link to a repository file leads on the site: a page wins over the raw file
    built = {"site/collections/index.json": "/collections/index.json"}   # made by build_catalogue
    linkable = {"site/" + src: address for src, address in files.items() if src.startswith("collections/")}
    address_of = {**files, **built, **linkable, **pages}

    def rewrite(src):
        base = posixpath.dirname(src)

        def repl(m):
            href = m.group(2)
            if re.match(r"^(?:[a-z][a-z0-9+.-]*:|#|/)", href):
                return m.group(0)
            path, _, frag = href.partition("#")
            target = posixpath.normpath(posixpath.join(base, path))
            if target not in address_of:
                errors.append(f"{src}: link to {href!r}, which is not part of the site")
                return m.group(0)
            return f'{m.group(1)}{address_of[target]}{"#" + frag if frag else ""}"'
        return repl

    if OUT.exists():
        shutil.rmtree(OUT)

    nav = "".join(f'<a href="{a}">{html.escape(t)}</a>' for t, a in NAV)
    for src, address in pages.items():
        text = (ROOT / src).read_text(encoding="utf-8")
        md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"])
        body = md.convert(text)
        body = re.sub(r'(<a\s[^>]*?href=")([^"]+)"', rewrite(src), body)
        m = re.search(r"^#\s+(.+)$", text, re.M)
        title = m.group(1).strip() if m else "Gilyon"
        if "Gilyon" not in title:
            title += " · Gilyon"
        dest = out_path(address)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(TEMPLATE.format(title=html.escape(title), canonical=ORIGIN + address, css=CSS,
                                        nav=nav, version=VERSION, body=body), encoding="utf-8")

    for src, address in files.items():
        dest = OUT / address.lstrip("/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / src, dest)

    cat_files, cat_warnings = build_catalogue.build(ROOT / "catalogue", OUT / "collections")
    for w in cat_warnings:
        print("catalogue: " + w, file=sys.stderr)
    build_catalogue.write_or_check(cat_files, OUT / "collections", False)

    for _, a in NAV:
        if not out_path(a).exists():
            errors.append(f"navigation: nothing is built for {a}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    for address in sorted(set(pages.values()) | set(built.values()) | {a for a in files.values() if not a.startswith("/_")}):
        print(ORIGIN + address)
    return 0


if __name__ == "__main__":
    sys.exit(main())
