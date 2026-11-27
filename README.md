# Gilyon

**An open format for Bible annotations, anchored to the Hebrew and Greek
words.**

Gilyon is a JSON format for exchanging study notes, footnotes, translation
notes, cross references, highlights, figures of speech and structures such as
chiasms. Each annotation points at original-language words by their published
identifiers, and at nothing else. It is written once and can be shown with
any translation.

**Status: Working Draft 0.1 (2026-11-27).** Not yet reviewed outside the
bcv-commons team. Anything may change before 1.0.

*Gilyon* (גִּלָּיוֹן) is the Hebrew word for the margin of a page, and for a
note written there.

## The idea

A note written on one translation is tied to it: to a caller mark, a
character offset or a quoted phrase. Moving it to another translation means
placing it again by hand.

Every translation renders the same Hebrew, Aramaic and Greek words, and those
words have open identifiers in the MACULA datasets (Clear Bible / Biblica,
CC BY 4.0). A Gilyon annotation names the words it is about. An application
that knows how its translation corresponds to those words can then put the
annotation in the right place.

A Gilyon document holds no position in any translation.

## One annotation

A note at a position in Genesis 1:2, between two Hebrew words:

```json
{
  "id": "urn:uuid:31155b51-21cc-56f6-9c28-0246e3995354",
  "motivation": "commenting",
  "category": ["gilyon:note/translation"],
  "body": [
    { "value": "The two Hebrew words rhyme (tohu wa-bohu). Few translations keep the sound." }
  ],
  "target": {
    "text": "heb",
    "selector": { "type": "Point", "ref": "GEN 1:2",
                  "after": "o010010020042", "before": "o010010020051" },
    "anchoring": { "status": "authored" },
    "fallback": { "type": "Passage", "ref": "GEN 1:2" }
  }
}
```

`heb` is declared once per document as MACULA Hebrew at a pinned release.
`anchoring` says how the anchor was obtained: chosen by the author, derived
by software, or confirmed by a reviewer.

## What the format covers

| | |
|---|---|
| **Anchors** | Verses, sets of words, ranges, positions between words, lexemes, and combinations of these. |
| **Reliability** | Every word-level anchor states whether it was authored, derived or reviewed, with the method and a confidence. |
| **Content** | Bodies as plain text, Markdown or restricted HTML. |
| **Languages** | The wording is kept apart from the anchors: one annotation file, and one text file per language in a folder named by its ISO 639-3 code. Nothing is copied. |
| **Translations** | Each translated body says whether it is machine-made, reviewed or human, and which wording it was made from, so stale translations are detected. |
| **Classification** | A motivation and categories from registered vocabularies. |
| **Links** | Cross references, quotations, persons and places. |
| **Structures** | Labelled units and the relations between them: chiasm, parallelism, inclusio. |
| **Adoption in steps** | Level 0 is verse-anchored, Level 1 adds words, Level 2 adds structures. Identifiers survive the move from one level to the next. |
| **Translations by others** | Anyone the licence permits can publish a translation of a collection on a server of their own, as text files plus a manifest that names the collection. The publisher changes nothing. |
| **Catalogue** | Collections and their translations by manifest address, with the result of the checks made on each. It is published in slices by language, publisher and collection, so an application fetches only its language. |
| **Packaging** | One file, or a collection split by book or chapter and by language, with a manifest. |

It does not define a Bible text format, an alignment format or an API.

## Read

| Document | For |
|---|---|
| [`docs/overview.md`](docs/overview.md) | A ten-minute introduction. |
| [`docs/guide.md`](docs/guide.md) | Producing and consuming documents, step by step. |
| [`spec/gilyon-0.1.md`](spec/gilyon-0.1.md) | **The specification.** Normative. |
| [`docs/bible-editions.md`](docs/bible-editions.md) | How a collection is used with the Bible editions catalogued in `bcv-commons/bibles`. |
| [`docs/catalogue.md`](docs/catalogue.md) | Getting a collection or a translation listed, and what the catalogue verifies. |
| [`docs/roadmap.md`](docs/roadmap.md) | What is built, and what the design leaves room for. |
| [`docs/landscape.md`](docs/landscape.md) | Related standards and how Gilyon relates to each. |
| [`docs/open-issues.md`](docs/open-issues.md) | What is undecided. |
| [`GOVERNANCE.md`](GOVERNANCE.md) | How the specification changes. A proposal. |

## Repository

| Path | Contents |
|---|---|
| `spec/` | The specification. |
| `schema/` | JSON Schema 2020-12 for an annotation document, a body document, a manifest and a catalogue. |
| `registries/` | Base texts, versifications, categories, entity authorities, anchoring methods. |
| `examples/` | Documents that validate, a collection in two languages (`collection/`), the same collection with its manifest in one part per book (`collection-parts/`), a translation of it published separately (`translation-elsewhere/`), a catalogue that lists both (`catalogue/`, published form in `catalogue/published/`), and in `invalid/` cases that must fail. They are the test suite. |
| `collections/` | Collections hosted on `gilyon.org`, each under its own licence. So far one: anchors only, for the notes of a Swedish study Bible on Joshua. |
| `catalogue/` | The catalogue's source: one file per registered publisher, and the state read from their manifests. |
| `context/` | JSON-LD context (draft). |
| `tools/` | The validator, the catalogue tool (discovery, checks, slices, ownership) and the site build. |
| `site/` | Site-only files: headers, redirects, vocabulary page, catalogue page. |
| `docs/` | Introduction, guide, landscape, open issues. |

## Permanent addresses

| Address | Content |
|---|---|
| `https://gilyon.org/0.1/` | The specification |
| `https://gilyon.org/0.1/schema.json` | Document schema |
| `https://gilyon.org/0.1/manifest.schema.json` | Manifest schema |
| `https://gilyon.org/0.1/bodies.schema.json` | Body-document schema |
| `https://gilyon.org/0.1/context.jsonld` | JSON-LD context (draft) |
| `https://gilyon.org/registries/<name>.json` | Registries |
| `https://gilyon.org/ns#` | Vocabulary namespace |
| `https://gilyon.org/collections/index.json` | The catalogue's index; slices under `lang/`, `publisher/`, `c/` |

The site is built from this repository with `tools/build_site.py`
(`uv run --with markdown --with jsonschema tools/build_site.py`). It is
served by Cloudflare as static files; `wrangler.jsonc` names the built folder.

## Validate a document

```
uv run --with jsonschema tools/validate.py examples/*.gilyon.json examples/catalogue/published/index.json
```

The validator needs Python 3 and the `jsonschema` package; `uv` fetches the
package for the run. It applies the schema and the rules a schema cannot
express, and exits with status 0 when every file is valid. Pass a
manifest to check a collection or a translation with its checksums, or a
catalogue to check everything it lists that is stored locally. Remote files
are not fetched.

## Planned

- **The first registered publishers** (`docs/catalogue.md`).
- **A JSON-LD context** beyond the first draft in `context/`, which maps a
  document to the W3C Web Annotation vocabulary.

## Take part

Gilyon is meant to be used by more than one organisation, and it has had one
author so far. Review is the most useful contribution now: of the anchor
model, of the registries, and of whether your notes or your application fit.
Open an issue on this repository.

## Licence

Specification, schemas, registries, examples and documentation: CC BY 4.0.
Tools: MIT. Copyright the bcv-commons team. See [`LICENSE`](LICENSE).

Word identifiers come from MACULA Hebrew and MACULA Greek, Clear Bible /
Biblica, CC BY 4.0.
