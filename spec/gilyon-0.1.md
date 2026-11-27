# Gilyon — Bible Annotation Exchange Format

**Version 0.1.0 — Working Draft, 2026-11-27**

| | |
|---|---|
| Status | Working Draft. Nothing here is stable until version 1.0. |
| This version | `spec/gilyon-0.1.md` |
| Permanent address | `https://gilyon.org/0.1/` |
| Schema | `schema/gilyon-0.1.schema.json` (JSON Schema 2020-12), `https://gilyon.org/0.1/schema.json`; also `gilyon-bodies-0.1.schema.json`, `gilyon-manifest-0.1.schema.json` and `gilyon-catalogue-0.1.schema.json` |
| Registries | `registries/*.json` |
| Licence of this text | CC BY 4.0 |
| Name | *Gilyon* (גִּלָּיוֹן): Hebrew for the margin of a page, and for a note written there. |

## Abstract

Gilyon is a JSON format for exchanging annotations on the Bible: study notes,
footnotes, translation notes, cross references, personal notes and highlights,
classified figures of speech, and structures such as chiasms and parallelism.

A Gilyon annotation is *stand-off*: it lives outside the Bible text and points
into it. Its anchor is a set of **original-language word identifiers** in a
pinned Hebrew, Aramaic or Greek base text, and nothing else: a Gilyon document
holds no position in any translation. Because the anchor does not depend on a
translation, an application can show the same annotation on any translation
for which it has a word alignment to the base text.

Gilyon defines (1) the document and annotation model, (2) the anchor model and
its canonical identifiers, (3) how the derivation and reliability of an anchor are
recorded, (4) a structure layer for multi-part patterns, (5) how the wording
of annotations is kept per language, apart from the anchors, with the state
of each translation, and (6) conformance classes.

## Table of contents

1. Introduction
2. Conformance
3. Terminology
4. Document model
5. Texts
6. Annotations
7. Targets and selectors
8. Anchoring: status, method and confidence
9. Bodies
10. Classification
11. Links, entities and relations between annotations
12. Structures
13. Use with a translation
14. Integrity, versioning and identifiers
15. Rights and provenance
16. Serialisations and packaging
17. Extensions and registries
18. Relation to other standards
19. Security and privacy considerations
- Appendix A. Canonical word identifiers
- Appendix B. Reference syntax
- Appendix C. Anchoring an annotation authored on a translation (informative)
- Appendix D. JSON-LD context and Web Annotation mapping (informative)
- Appendix E. References

---

## 1. Introduction

### 1.1 Problem

Bible annotations are today tied to the thing they were written on. A study
note is tied to a verse number of one versification; a footnote is tied to a
caller mark in one translation; a highlight is tied to character offsets in one
app. None of these survives a move to another translation, another language or
another application. Formats that exist for Scripture *text* (USFM, USX, USJ)
carry notes inline, bound to that text. The few stand-off formats in the field
either point into one translation (USFM TC Linkages draft) or cover one
annotation kind (ACAI: entities). `docs/landscape.md` surveys them.

### 1.2 Approach

Every translation of the Bible is a translation of the same Hebrew, Aramaic
and Greek words. Those words have open, published identifiers (MACULA, CC BY
4.0). Word alignments between those words and translations are also published
or can be computed. Gilyon therefore:

- anchors each annotation to original-language **word identifiers** in a
  **pinned base text**, never to character offsets or to quoted strings;
- records **how** each anchor was obtained and **how reliable** it is, because
  most existing annotations were written on a translation and their anchors
  are derived;
- holds **no position in a translation**: showing an annotation on a given
  translation is the work of the application, through an alignment it holds
  (§13);
- keeps the **wording apart from the anchor**: an annotation is anchored
  once, and its text can exist in any number of languages, each in a file of
  its own, with a record of whether a translation was made by software and
  whether a person has reviewed it (§9.1, §16.2);
- lets a publisher start with verse-level anchors and refine later, through
  conformance **levels**.

### 1.3 Design goals

1. **Translation-independent.** An annotation is usable with a translation its
   author never saw.
2. **Exact.** The annotated words are identified without ambiguity, including
   repeated words in a verse and sub-word parts in Hebrew.
3. **Honest about uncertainty.** Machine-derived anchors say so, with a method
   and a confidence.
4. **Incremental.** Verse-anchored material is valid Gilyon; word anchors and
   structures are added without a format change.
5. **Plain JSON first.** A document is readable and writable without any
   semantic-web tooling. A JSON-LD reading is available but optional.
6. **Reuse.** Existing identifiers, reference syntax, versification schemes and
   vocabularies are referenced, not reinvented.
7. **Open.** The normative anchors rest only on base texts whose licences
   permit unrestricted redistribution.

### 1.4 Non-goals

Gilyon does not define a Bible text format, a word-alignment format, a
versification-mapping format, a lexicon format, a critical apparatus, or an
API. It references existing work for each (§18).

Gilyon does not address translations. It has no selector for a place in a
translation, records no position in one, and defines no way of computing one.
A document MUST NOT carry such a position (token or character offsets, or
quoted translation text serving as an anchor) in any member, extension
members included.

## 2. Conformance

### 2.1 Requirement keywords

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT,
RECOMMENDED, MAY and OPTIONAL are to be interpreted as described in BCP 14
[RFC 2119] [RFC 8174] when, and only when, they appear in capitals.

Sections marked *(informative)* and all examples are non-normative. Where an
example and the normative text disagree, the text governs. Where the JSON
Schema and the text disagree, the text governs and the schema has a defect.

### 2.2 Document conformance levels

A Gilyon document declares one level in `conformsTo` (§4.2). Each level includes
the ones below it.

| Level | Name | A conforming document |
|---|---|---|
| 0 | **Passage** | Satisfies §4–§6, §9–§11, §14–§15. Every target uses a `Passage` selector. |
| 1 | **Word** | In addition, at least the targets that claim word anchoring use the selectors of §7.3–§7.5 on a pinned base text, with canonical identifiers (Appendix A) and an `anchoring` record (§8). |
| 2 | **Structure** | In addition, may contain structures (§12). |

A Level 0 document is a legitimate interchange document. Levels exist so that
a publisher of verse-anchored notes can adopt Gilyon now and refine anchors later
without re-issuing identifiers.

### 2.3 Processor conformance classes

| Class | Requirements |
|---|---|
| **Producer** | Emits documents that validate against the schema and satisfy every MUST that applies to the level it declares. |
| **Consumer** | Accepts every conforming document of the levels it claims, with bodies inline or in body documents (§16.2); ignores members it does not understand (§17.1); never silently drops an annotation whose target it cannot resolve, but reports it. |
| **Anchorer** | A Producer that derives original-language anchors by a procedure, for annotations that were not authored on the base text, and records `anchoring` as required by §8. |

An implementation claims conformance as, for example, "Gilyon 0.1 Consumer,
Level 1".

## 3. Terminology

**Base text** — a specific, published edition of the Hebrew/Aramaic or Greek
Scriptures in which every word has an identifier (§5.2).

**Word** — the smallest identified unit of a base text. In Hebrew this is a
*morpheme part* of an orthographic word (prefix, stem, suffix); in Greek it is
an orthographic word.

**Word identifier (word ID)** — the canonical identifier of a word (Appendix A).

**Translation** — any edition that is not a base text. Gilyon does not
address translations; the term is used only to say where an annotation came
from or where an application shows it.

**Target** — what an annotation is about.

**Selector** — the description of which part of a text a target covers.

**Anchor** — the selector of a target expressed on a base text.

**Anchoring** — the record of how the anchor was obtained.

**Annotation document** — a Gilyon document that holds annotations (§4).

**Body document** — a document that holds the bodies of the annotations of
one annotation document, in one language (§16.2).

**Source language** — the language in which the bodies of a collection were
written. Its wording governs over every translation.

**Alignment** — data that relates words of a base text to words of a
translation. Outside the scope of Gilyon (§13).

## 4. Document model

### 4.1 Encoding

A Gilyon document is a single JSON value conforming to I-JSON [RFC 7493]: UTF-8,
no duplicate member names, no byte order mark. All strings MUST be in Unicode
Normalization Form C [UAX15] (see also §7.8).

### 4.2 Top-level members

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `gilyon` | MUST | string | Format version this document follows, `MAJOR.MINOR` (e.g. `"0.1"`). |
| `conformsTo` | MUST | integer | Document level 0, 1 or 2 (§2.2). |
| `id` | MUST | string | IRI that identifies this document. A `urn:uuid:` IRI is acceptable. |
| `meta` | MUST | object | Document metadata (§4.3). |
| `texts` | MUST | object | Declarations of the texts that targets refer to (§5). Keys are local names. |
| `annotations` | MUST | array | The annotations (§6). MAY be empty. |
| `bodies` | MAY | string | `"inline"` (default): bodies are in the annotations. `"separate"`: bodies are in body documents (§16.2). |
| `@context` | MAY | string or array | See Appendix D. Consumers that do not process JSON-LD MUST ignore it. |

Local names (keys of `texts`) MUST match `^[a-z][a-z0-9_-]*$`.
They have meaning only inside the document.

### 4.3 `meta`

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `title` | SHOULD | string or language map | Human title. |
| `description` | MAY | string or language map | |
| `language` | SHOULD | string | Default language of bodies, BCP 47 [BCP47]. |
| `license` | MUST | string | Default licence of the annotations: an SPDX licence identifier [SPDX], or `"LicenseRef-<name>"` with `licenseUrl`. Use `"LicenseRef-private"` for personal data not offered for redistribution. |
| `licenseUrl` | MAY | string | IRI of the licence text. |
| `attribution` | SHOULD | string | Credit line to display with the annotations. |
| `creator` | SHOULD | array of agents | §15.2. |
| `publisher` | MAY | agent | |
| `created`, `modified` | SHOULD | string | Timestamps, RFC 3339. |
| `status` | MAY | string | `"draft"`, `"review"`, `"approved"` or `"withdrawn"`. Default `"draft"`. |
| `source` | MAY | object | Bibliographic origin of the collection: `title`, `edition`, `date`, `url`, `isbn`. |
| `generator` | MAY | agent | Software that wrote the file. |

A *language map* is an object whose keys are BCP 47 tags and whose values are
strings, e.g. `{"en": "Notes on Joshua", "sv": "Noter till Josua"}`.

### 4.4 Minimal document *(informative)*

```json
{
  "gilyon": "0.1",
  "conformsTo": 0,
  "id": "urn:uuid:5b0f6c1e-2c0b-4d6e-9d0a-1f6a4a3b7c10",
  "meta": { "license": "CC-BY-4.0", "language": "en" },
  "texts": { "org": { "role": "reference", "versification": "org" } },
  "annotations": [
    {
      "id": "urn:uuid:0d0c3f0a-8f1b-4a52-b0f5-7b5a3d6f2e11",
      "motivation": "commenting",
      "body": [ { "value": "Joshua takes over the leadership after Moses." } ],
      "target": { "text": "org", "selector": { "type": "Passage", "ref": "JOS 1:1-2" } }
    }
  ]
}
```

## 5. Texts

Every target names a text by its local name. A text is either a **base
text**, pinned so that word identifiers can be interpreted without guessing,
or a **reference** text, which stands for the Bible as numbered by one
versification.

### 5.1 Common members

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `role` | MUST | string | `"base"` or `"reference"`. |
| `title` | MAY | string | |
| `versification` | see below | string | Name of a registered versification scheme (§5.3) or an IRI of a mapping. |
| `license` | MAY | string | SPDX identifier of the text's own licence. |
| `url` | MAY | string | Where the pinned text can be obtained. |

A text with `role` `"reference"` declares only a versification, which it MUST
give. It is the target text of `Passage` selectors that are not tied to an
edition: the targets of Level 0 documents, and Scripture references in
`links`.

### 5.2 Base texts

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `edition` | MUST | string | A base-text identifier from `registries/base-texts.json`. |
| `release` | MUST | string | Release tag of that edition as published (e.g. `"26.04.13"`). |
| `revision` | SHOULD | string | Immutable revision (e.g. a full commit hash). |
| `sha256` | MAY | string | Lowercase hex SHA-256 of the pinned artefact named in the registry entry. |

1. Word identifiers are **edition-relative**. The same identifier string can
   denote different words in two editions of the Greek New Testament. A word
   identifier therefore has meaning only together with the `edition` of the
   text its target names.
2. A base text's versification is fixed by its registry entry; `versification`
   MUST NOT be given for `role` `"base"`.
3. The registry designates **default base texts** (§17.3). A Level 1 or 2
   document SHOULD express anchors on a default base text. A document
   that uses another registered base text MUST still be accepted by Consumers,
   which MAY report that they cannot resolve it.
4. A base text is admitted to the registry as *default* only if its licence
   permits redistribution of the text and its identifiers for any purpose.
5. When `revision` is present, it identifies the pinned state, and `release`
   MUST be the latest published release that the revision contains. A
   revision that is not itself a release is permitted. Producers SHOULD pin a
   release where one exists.

Version 0.1 registers these default base texts:

| `edition` | Text | Covers | Word ID form |
|---|---|---|---|
| `WLCM` | MACULA Hebrew (Westminster Leningrad Codex) | Hebrew Bible / Old Testament, Hebrew and Aramaic | `o` + 12 digits |
| `N1904` | MACULA Greek, Nestle 1904 | New Testament | `n` + 11 digits |

`SBLGNT` (MACULA Greek, SBLGNT) is registered as a non-default base text.

### 5.3 Versification

Verse references (Appendix B) are always interpreted in the versification of
the text the target names. Registered scheme names are in
`registries/versifications.json`; version 0.1 registers `org` (the Hebrew
numbering of `WLCM` and the numbering of `N1904`), `eng`, `lxx`, `vul`, `rsc`
and `rso`, with the meaning they have in Paratext `.vrs` files and in the
Copenhagen Alliance versification specification. A custom scheme is named by
the IRI of a mapping to `org` in the Copenhagen Alliance JSON format.

Word-anchored targets need no versification mapping: the word identifier
decides. Verse references given alongside word identifiers are aids for
readers and indexes only (§7.3).

## 6. Annotations

### 6.1 Members

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `id` | MUST | string | IRI, globally unique and stable for the life of the annotation (§14.2). |
| `motivation` | MUST | string | Why the annotation exists (§10.1). |
| `category` | MAY | array of strings | Classification terms (§10.2). |
| `body` | MUST unless `motivation` is `highlighting` or `structure` is present. MUST NOT be present when the document declares `bodies` `"separate"` (§16.2) | array | §9. |
| `target` | MUST | object or array of objects | §7. An array means the annotation is about each target equally. |
| `structure` | MAY (Level 2) | object | §12. |
| `links` | MAY | array | §11. |
| `creator` | MAY | array of agents | Overrides `meta.creator`. |
| `created`, `modified` | MAY | string | RFC 3339. |
| `license`, `attribution` | MAY | string | Override the document defaults. |
| `source` | MAY | object | Citation of where this annotation was published: `title`, `page`, `date`, `url`, `noteId`. |
| `status` | MAY | string | As in `meta.status`. |
| `supersedes` | MAY | string | `id` of an annotation this one replaces. |
| `presentation` | MAY | object | Display hints (§6.2). |
| `sequence` | MAY | number | Order among annotations that share the same anchor position (§6.3). |

### 6.2 Presentation hints

`presentation` carries hints a Consumer MAY use and MAY ignore:

- `color` — a CSS color keyword or `#rrggbb`, for highlights;
- `caller` — the caller mark used in the source publication (e.g. `"a"`, `"*"`);
- `placement` — `"inline"`, `"footnote"`, `"margin"`, `"sidebar"` or
  `"introduction"`: how the source publication placed it.

Presentation hints MUST NOT carry meaning that is needed to understand the
annotation.

### 6.3 Order

Annotations in a document SHOULD be listed in canonical order of their first
target (base-text order, then document order for ties). When several
annotations have identical point anchors (§7.5), `sequence` gives their
reading order; without it, array order applies.

## 7. Targets and selectors

### 7.1 Target

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `text` | MUST unless `annotation` is given | string | Local name in `texts`. |
| `selector` | MUST unless `annotation` is given | object | One selector (§7.2). |
| `anchoring` | MUST for word-level selectors on a base text | object | §8. |
| `fallback` | MAY | object | A `Passage` selector, in the versification of `text`, to use if the selector cannot be resolved. |
| `annotation` | MAY | string | `id` of another annotation: the target is that annotation itself (§11.3). |

### 7.2 Selector types

| `type` | Applies to | Selects |
|---|---|---|
| `Passage` | any text | Whole verses or a range of them. |
| `Words` | base text | An explicit set of words. |
| `Range` | base text | All words from one word to another, inclusive. |
| `Point` | base text | A position between two words. |
| `Lexeme` | (no text position) | A lexeme, sense or name as such, wherever it occurs. |
| `Composite` | any | Several selectors that together form one target. |

Every selector MAY carry `ref`, a verse reference (Appendix B) for the verse or
verses it lies in. For `Passage` it is REQUIRED.

### 7.3 `Words`

```json
{ "type": "Words", "ref": "PHP 1:1", "words": ["n50001001001", "n50001001004"] }
```

- `words` MUST be a non-empty array of distinct canonical word IDs
  (Appendix A), in ascending canonical order.
- The words need not be adjacent and MAY lie in several verses of one book.
- A selector that includes only some parts of a Hebrew orthographic word
  selects only those parts (for example the stem without its conjunction).

`check` (OPTIONAL) is an object that maps a word ID to the surface form the
author saw, NFC-normalised. A Consumer SHOULD compare it with its copy of the
base text, after NFC normalisation and ignoring cantillation marks, and report
a mismatch. `check` never selects anything; identifiers do.

```json
"check": { "n50001001001": "Παῦλος", "n50001001004": "δοῦλοι" }
```

`lexemes` (OPTIONAL) maps a word ID to a lexeme identifier (§7.6). It is a
convenience for indexing and for Consumers without the base text; the base
text governs.

### 7.4 `Range`

```json
{ "type": "Range", "ref": "MAT 6:24", "first": "n40006024001", "last": "n40006024005" }
```

Selects every word whose identifier `w` satisfies `first ≤ w ≤ last` in
canonical order (Appendix A.4). `first` and `last` MUST belong to the same
book and `first` MUST NOT follow `last`. `check` and `lexemes` MAY be used as
in §7.3.

A `Range` is exactly equivalent to the `Words` selector that lists the same
words. Producers SHOULD use `Range` for contiguous spans of more than three
words.

### 7.5 `Point`

A point is a position *between* words. It is the correct anchor for a
footnote caller, an inline comment, an ellipsis, a line break or any annotation
that attaches to a place and not to words.

```json
{ "type": "Point", "ref": "EXO 32:32", "after": "o020320320042", "before": "o020320320051" }
```

- At least one of `after` and `before` MUST be present.
- `after` is the last word that precedes the point; `before` is the first word
  that follows it.
- When both are present and the two words are adjacent in canonical order, the
  point is **exact**.
- When both are present and other words lie between them, the point is a
  **gap**: the author's position is somewhere in that interval and could not be
  narrowed. `anchoring.confidence` and `anchoring.tier` (§8) SHOULD reflect it.
- When only one is present, the point is immediately after, or immediately
  before, that word, and nothing is claimed about the other side. This is the
  form to use at the start and end of a book, and when only one neighbour could
  be established.

### 7.6 `Lexeme`

Selects a lexical unit as such, not a place in the text. It is used for
annotations about a word in general (a dictionary-style note, a key-term note).

```json
{ "type": "Lexeme", "lexeme": "hbo:0871a" }
```

- `lexeme` MUST be `<language>:<id>`, where `<language>` is `hbo` (Biblical
  Hebrew), `arc` (Biblical Aramaic) or `grc` (Greek) and `<id>` is a Strong's
  number as extended by the base text's lexeme inventory: for Hebrew and
  Aramaic four digits, zero-padded, with an optional lowercase homograph letter
  (`hbo:0430`, `hbo:0871a`); for Greek the number without padding, with an
  optional letter (`grc:26`, `grc:1722`).
- `sense` (OPTIONAL) is a sense identifier within a named sense inventory:
  `{ "inventory": "<registered name or IRI>", "id": "..." }`.
- A target with a `Lexeme` selector has no `text`; `text` MAY be omitted.

Other vocabularies of lexical or encyclopaedic identity (dStrong, SDBH,
Louw-Nida, TIPNR, ACAI) are referenced through `links` (§11), not through
`Lexeme`.

### 7.7 `Passage`

```json
{ "type": "Passage", "ref": "JOS 1:1-2" }
```

Selects the whole of the verses named by `ref`, in the versification of the
target's text. `ref` MAY name a verse, a verse range within or across chapters
of one book, a chapter, a chapter range or a book (Appendix B).

### 7.8 `Composite`

```json
{ "type": "Composite", "items": [ { "type": "Range", ... }, { "type": "Range", ... } ] }
```

`items` MUST contain two or more selectors, none of them `Composite`, all on
the same text. Together they form one discontinuous target. (Several *separate*
targets are expressed as an array of targets, §6.1.)

Normalisation: the values of `check` entries (§7.3) MUST be NFC like every
other string; Consumers comparing them with Hebrew base text MUST normalise
both sides, because the order of Hebrew combining marks differs between
sources.

## 8. Anchoring: status, method and confidence

Most existing annotations were written on a translation. Their
original-language anchors are derived, by people or by software, with varying
reliability. Gilyon requires that this be stated. It does not record where in
the translation the annotation stood.

### 8.1 The `anchoring` object

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `status` | MUST | string | `"authored"`, `"reviewed"`, `"derived"` or `"unresolved"`. |
| `method` | MUST if `status` is `"derived"` | string | Identifier of the procedure, registered or an IRI (e.g. `"bcv-lexeme-anchor/1"`). |
| `confidence` | MAY | number | Probability in [0, 1] that the anchor is the intended one, when the method yields one. |
| `tier` | MAY | string | `"high"`, `"medium"` or `"low"`: a coarse grade for methods that yield rules, not probabilities. |
| `detail` | MAY | string | Method-specific code (e.g. `"LOW_GAP"`, `"REVERSED"`). |
| `reviewer` | MAY | agent | Who confirmed it, for `"reviewed"`. |
| `date` | MAY | string | RFC 3339 date or timestamp. |

### 8.2 Status values

- **`authored`** — the author chose these original-language words directly.
- **`reviewed`** — the anchor was derived by a procedure and a person
  competent in the source language confirmed or corrected it.
- **`derived`** — the anchor was derived by a procedure and has not been
  confirmed by a person.
- **`unresolved`** — no word-level anchor could be derived. The target's
  selector MUST then be a `Passage` selector.

A Consumer SHOULD make the status available to its users, and MAY filter on it.
A Consumer MUST NOT present a `derived` anchor as editorially confirmed.

```json
"target": {
  "text": "heb",
  "selector": { "type": "Point", "ref": "JOS 1:1",
                "after": "o060010010051", "before": "o060010010072" },
  "anchoring": { "status": "derived", "method": "bcv-lexeme-anchor/1",
                 "tier": "low", "detail": "LOW_GAP" },
  "fallback": { "type": "Passage", "ref": "JOS 1:1" }
}
```

### 8.3 Rules for Anchorers

An Anchorer:

1. MUST set `status` to `"derived"` on every anchor it derives;
2. MUST record `method`;
3. MUST NOT narrow a position beyond what its evidence supports: where it
   establishes only the neighbours of a position, it emits a gap `Point` (§7.5),
   and where it establishes nothing it emits `unresolved`;
4. MUST NOT write the position in the translation from which it worked
   (§1.4);
5. MUST leave annotation `id` values unchanged when it refines the anchors of
   an existing document.

Appendix C describes one procedure.

## 9. Bodies

`body` is an array of body objects. Several bodies are several renderings or
components of the same annotation (typically the same note in several
languages).

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `value` | MUST | string | The content. |
| `language` | SHOULD | string | BCP 47; defaults to `meta.language`. |
| `format` | MAY | string | `"text/plain"` (default), `"text/markdown"` or `"text/html"`. |
| `purpose` | MAY | string | Role of this body when it differs from the annotation's motivation, e.g. `"tagging"`, `"describing"`, `"title"`. |
| `translationOf` | MAY | string | Language tag of the body this one translates. |
| `translation` | MAY | object | How this translation was made and whether it was reviewed (§9.1). |
| `creator` | MAY | array of agents | e.g. the translator of this body. |
| `license` | MAY | string | Overrides the annotation's licence for this body. |

Rules:

1. `text/markdown` means CommonMark [COMMONMARK] without raw HTML. Consumers
   MUST treat raw HTML in such a body as text.
2. `text/html` bodies MUST be restricted to phrasing and simple block content:
   `p`, `br`, `em`, `strong`, `i`, `b`, `sup`, `sub`, `span`, `q`, `blockquote`,
   `ul`, `ol`, `li`, `a`, `cite`. Consumers MUST sanitise HTML before display
   (§19).
3. At most one body per `language` and `purpose` pair. The body without
   `translationOf` is the original.
4. Scripture references inside a body SHOULD also be given as structured
   `links` (§11) so that they survive translation of the body. In Markdown and
   HTML bodies a reference MAY be written as a link whose address is
   `bible:` followed by a reference of Appendix B with spaces replaced by `.`,
   for example `[4 Mos 33:48–50](bible:NUM.33:48-50)`.
5. A body MUST NOT embed the annotated Scripture text as its way of saying
   what it is about; the target says that.

### 9.1 Translated bodies

A body that translates another body states so with `translationOf`. Its
`translation` object records the state of the translation, as `anchoring`
(§8) records the state of an anchor.

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `status` | MUST | string | `"machine"`, `"reviewed"` or `"human"`. |
| `sourceDigest` | SHOULD | string | Lowercase hex SHA-256 of the UTF-8 encoding of the `value` of the body that was translated. |
| `method` | MAY | string | The software that made the translation, with its version. |
| `reviewer` | MAY | agent | Who confirmed it, for `"reviewed"`. |
| `date` | MAY | string | RFC 3339 date or timestamp of the translation or of its review. |

Status values:

- **`machine`** — made by software and not confirmed by a person.
- **`reviewed`** — made by software, then confirmed or corrected by a person
  competent in both languages.
- **`human`** — made by a person.

Rules:

1. A body with `translation` MUST have `translationOf`. In a body document
   both MAY be given once for the whole document (§16.2); members given on a
   body override those of the document one by one.
2. `sourceDigest` identifies the wording that was translated. When the source
   body is edited, its digest changes and the translation is **stale**. A
   Producer that edits a source body SHOULD NOT alter the `sourceDigest` of
   its translations until they have been brought up to date. A stale
   translation of status `reviewed` is no longer a reviewed translation of
   the current wording.
3. A Consumer SHOULD make the status available to its users. It MUST NOT
   present a `machine` translation as reviewed. When it can tell that a
   translation is stale, it SHOULD say so or show the source body instead.
4. A person who corrects a `machine` translation sets `status` to
   `"reviewed"`, records `reviewer`, and leaves the annotation `id`
   unchanged.
5. The requirement of §15.3 applies: a `machine` body has a `creator` of
   `type` `"Software"`, on the body or on the document that holds it.
6. Translating a body makes a derivative of it. A body under a licence that
   forbids derivatives MUST NOT be translated without permission (§15.1).

## 10. Classification

Two members classify an annotation. They answer different questions.

### 10.1 `motivation` — what kind of act the annotation is

Exactly one of:

| Value | Use |
|---|---|
| `commenting` | Notes of every sort: study, exegetical, devotional, personal. |
| `describing` | A neutral description or gloss of the target (literal renderings, "Hebrew: …"). |
| `classifying` | Assigns a category to the target (a figure of speech, a genre, a discourse function). The category is in `category`. |
| `linking` | Relates the target to something else (cross reference, quotation, parallel). The other end is in `links`. |
| `identifying` | States which entity (person, place, event) the target denotes. The entity is in `links`. |
| `highlighting` | Marks the target, with no content required. |
| `questioning` | Asks a question about the target. |
| `replying` | Responds to another annotation (the target is that annotation). |
| `assessing` | Rates or reviews another annotation. |
| `editing` | Proposes a change to the target text (translation review). |

These values, where they coincide, have the meaning of the same-named
motivations of the W3C Web Annotation Vocabulary.

### 10.2 `category` — what the annotation is about

`category` is an array of terms `<vocabulary>:<path>`, where `<vocabulary>` is
registered (§17.3) and `<path>` is a `/`-separated path from general to
specific. A Consumer that does not know a term SHOULD fall back to the longest
prefix it knows.

Version 0.1 defines the vocabulary `gilyon` in `registries/categories.json`. Its
top level:

| Term | Meaning |
|---|---|
| `gilyon:note/study` | Explanatory note for readers. |
| `gilyon:note/translation` | Note about how the passage is or can be translated. |
| `gilyon:note/textual` | Note about the wording of the source text and its witnesses. |
| `gilyon:note/literal` | A more literal rendering. |
| `gilyon:note/alternative` | An alternative rendering ("Or: …"). |
| `gilyon:note/background` | Historical, geographical or cultural background. |
| `gilyon:note/chronology` | Dating of an event. |
| `gilyon:note/devotional` | Devotional or applicational comment. |
| `gilyon:note/personal` | A user's own note. |
| `gilyon:note/introduction` | Introduction to a book or section. |
| `gilyon:crossref/quotation`, `/allusion`, `/parallel`, `/see-also` | Kinds of cross reference. |
| `gilyon:figure/...` | Figures of speech and rhetorical devices. |
| `gilyon:structure/chiasm`, `/parallelism`, `/inclusio`, `/acrostic`, `/refrain` | Structures (§12). |
| `gilyon:entity/person`, `/place`, `/group`, `/event` | Entity mentions. |
| `gilyon:discourse/speaker`, `/quotation` | Who speaks; quoted speech. |

The `gilyon:figure` subtree is deliberately shallow in 0.1 (`comparison`,
`omission`, `addition`, `substitution`, `arrangement`, each with a few leaves
such as `gilyon:figure/omission/aposiopesis`). A full taxonomy is future work
(`docs/open-issues.md` §7). Other vocabularies MAY be used alongside, for
example the unfoldingWord `figs-*` support references as `uw:figs-metaphor`.

## 11. Links, entities and relations between annotations

### 11.1 `links`

`links` relates the annotation to passages, entities and external resources.
Each link has:

| Member | Req. | Meaning |
|---|---|---|
| `rel` | MUST | The relation (table below, or a registered or IRI-valued relation). |
| `target` | one of | A target object (§7.1): a place in a text. |
| `entity` | one of | An entity identifier `<authority>:<id>`. |
| `url` | one of | An IRI of an external resource. |
| `label` | MAY | Human-readable label (string or language map). |

| `rel` | Meaning |
|---|---|
| `crossReference` | See also this passage. |
| `quotes` / `quotedBy` | The annotated text quotes, or is quoted by, the linked passage. |
| `alludesTo` | Allusion. |
| `parallel` | Parallel account or parallel wording. |
| `denotes` | The annotated words refer to this entity. |
| `speaker` / `addressee` | The annotated speech is spoken by, or addressed to, this entity. |
| `about` | The annotation as a whole concerns this entity or resource. |
| `citation` | Bibliographic source for the claim made. |

Registered entity authorities in 0.1 (`registries/authorities.json`):
`acai` (e.g. `acai:person:Joshua`), `tipnr`, `openbible` (places),
`pleiades`, `wikidata`, `strong` (as a de facto name identifier where no
better one exists).

### 11.2 Cross references *(informative)*

A cross reference is an annotation with `motivation` `"linking"`, a target for
the place it is attached to and one or more `crossReference` links. A note
that merely *contains* references keeps `motivation` `"commenting"` and lists
them in `links`.

### 11.3 Annotations on annotations

A target MAY name another annotation by `annotation`. This expresses replies
(`replying`), ratings (`assessing`, with a body of `purpose` `"rating"` whose
`value` is a number as a string) and editorial review. The referenced
annotation need not be in the same document.

A `supersedes` member (§6.1) expresses revision. Annotation identifiers are
never reused for a different annotation (§14.2).

## 12. Structures

A structure is one annotation that divides a stretch of text into labelled
units and states how the units relate. Chiasm, parallelism, inclusio,
acrostics and refrains are structures.

### 12.1 The `structure` object

An annotation with `structure` has `motivation` `"classifying"`, a `category`
in `gilyon:structure/…`, and a `target` that covers the whole extent of the
structure.

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `units` | MUST | array | The units, in text order (§12.2). |
| `relations` | MAY | array | Relations between units (§12.3). |
| `focus` | MAY | array of unit ids | The unit or units that carry the emphasis (the centre of a chiasm). |
| `notation` | MAY | string | The conventional formula, for display only (e.g. `"A-B-C-C'-B'-A'"`). |

### 12.2 Units

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `id` | MUST | string | Unique within the structure; `^[A-Za-z0-9._'-]+$`. |
| `label` | MUST | string | The label to display (`"A"`, `"B′"`, `"1a"`). |
| `selector` | MUST | selector | The words of the unit, on the text named by the annotation's target. |
| `key` | MAY | array of selectors | Key words within the unit on which the correspondence rests. |
| `level` | MAY | integer | Indentation depth for display, from 0. |
| `parent` | MAY | string | `id` of the enclosing unit, for nested structures. |
| `body` | MAY | array | Comment on this unit (§9). |

Units MUST NOT partially overlap one another: any two units are either
disjoint or one contains the other, in which case the inner one names the
outer as `parent` (directly or through intermediate units).

### 12.3 Relations

Each relation is `{ "type": ..., "units": [id, id, ...] }`, with an optional
`body`.

| `type` | Meaning |
|---|---|
| `corresponds` | The units mirror or answer one another (A and A′). |
| `parallel` | The units are parallel lines or cola. |
| `contrasts` | The units stand in antithesis. |
| `intensifies` | A later unit heightens an earlier one. Order of `units` is significant. |
| `repeats` | The units repeat the same wording (refrain, inclusio). |
| `sequence` | The units form an ordered series (acrostic). Order is significant. |

A chiasm with a single unpaired centre has that unit in `focus` and in no
`corresponds` relation.

### 12.4 Competing analyses

Two analyses of the same passage are two annotations. One MAY reference the
other with a `links` entry of `rel` `"about"` or by an annotation target with
`motivation` `"replying"`. A Consumer MUST NOT merge structures.

### 12.5 Example *(informative)*

See `examples/02-structure-jhn-1-1.gilyon.json`.

## 13. Use with a translation *(informative)*

Gilyon stops at the original-language words. An application that shows an
annotation in a translation finds, through a word alignment it holds for that
translation, the words of the translation that render the anchored words. How
it does so, and which alignment it uses, is outside this specification.

Three properties of anchors matter to such an application:

1. A `Point` can be a gap (§7.5), and it can be one-sided. The place in the
   translation is then an interval, or is bounded on one side only.
2. A translation can reorder, merge or omit the anchored words. The place
   found can therefore be partial, discontinuous or absent, and the
   `fallback` verse is then the place to show the annotation.
3. The `anchoring` status says how far the anchor itself is to be trusted
   (§8.2). An application that shows a `derived` anchor at an exact place in
   a translation overstates what is known.

## 14. Integrity, versioning and identifiers

### 14.1 Format version

`gilyon` carries `MAJOR.MINOR` of this specification [SEMVER]. From 1.0 onward a
MINOR version only adds optional members and registry entries; a document of
version *M.n* is processable by a Consumer of *M.m* for any *m*. Before 1.0,
MINOR versions MAY break compatibility.

### 14.2 Annotation identifiers

1. `id` MUST be an IRI. Publishers SHOULD mint IRIs under a domain they
   control (e.g. `https://example.org/notes/a/JOS.1.1.1`); `urn:uuid:` is
   acceptable, and RECOMMENDED for personal annotations.
2. An `id` identifies the annotation through all its revisions: body edits,
   added translations and improved anchors do not change it.
3. An `id` MUST NOT be reused for a different annotation. A withdrawn
   annotation keeps its `id` with `status` `"withdrawn"`.

### 14.3 Base-text revisions

Word identifiers are stable only within a pinned release of a base text.
Therefore:

1. Level 1 and 2 documents MUST pin `release` for every base text (§5.2).
2. The registry entry of a base text SHALL state its identifier-stability
   policy and, when a release changes any identifier, publish a migration map
   from the previous release. A release without such a map cannot be
   registered.
3. A Consumer that holds a different release MUST apply the migration maps
   between the two, or report that it cannot.
4. `check` (§7.3) is the per-annotation safeguard: Producers SHOULD include it
   for `authored` and `reviewed` anchors.

### 14.4 Cross-edition mapping

A Consumer MAY resolve anchors on a non-default base text through a published
word mapping between editions (for example N1904 ↔ SBLGNT). It MUST NOT
present an anchor resolved in this way as authored on the edition it was
mapped to.

### 14.5 Document integrity

A detached digest of a document, when needed, is the SHA-256 of its canonical
form under the JSON Canonicalization Scheme [RFC 8785], expressed as lowercase
hex. Because all strings are NFC (§4.1), no further normalisation is applied.

## 15. Rights and provenance

### 15.1 Licence

Every annotation has exactly one effective licence: its own `license`, else
`meta.license`. A document MAY mix licences. Aggregators MUST preserve
`license` and `attribution` per annotation, and MUST NOT redistribute
annotations whose effective licence does not permit it (in particular
`LicenseRef-private`).

A licence that forbids derivatives (for example CC BY-ND) governs the *body*.
It forbids translating the body (§9.1). A licence that requires derivatives
to be shared alike (for example CC BY-SA) applies to its translations.
Adding or refining anchors does not alter a body; whether it constitutes a
derivative of the collection is a legal question this specification does not
decide. Publishers SHOULD state their position in `meta.description` or grant
explicit permission.

The licence of an annotation is independent of the licence of the base text.

### 15.2 Agents

An agent is an object with `name` (SHOULD), `id` (MAY; an IRI such as an ORCID
or an organisation URL), `type` (MAY; `"Person"`, `"Organization"` or
`"Software"`) and, for software, `version`. An `email` member is permitted and
is personal data (§19).

### 15.3 Machine-generated content

A body that was written or translated by software MUST have a `creator` of
`type` `"Software"`. An anchor derived by software is marked by `anchoring`
(§8).

## 16. Serialisations and packaging

1. **Single document.** File name `*.gilyon.json`. This is the basic form.
2. **Line-delimited.** File name `*.gilyon.jsonl`: the first line is the document
   object without `annotations`; each further line is one annotation object.
   It is equivalent to the single document with those annotations in that
   order.
3. **Collections.** A publisher MAY split a collection by book or chapter.
   Every annotation document of a split collection is a complete document. A
   split collection SHOULD carry a manifest (§16.1).
4. **Bodies by language.** The bodies MAY be kept apart from the annotations,
   in one body document per annotation document and language, each language
   in a folder of its own (§16.2). A collection in more than one language
   SHOULD be published in this form. It requires a manifest.
5. **Scripture Burrito.** A Gilyon collection MAY be an ingredient of a Scripture
   Burrito. A dedicated flavor is proposed in `docs/open-issues.md` §9.

Media type: `application/json`. A dedicated media type will be requested with
version 1.0.

### 16.1 Manifest

The manifest of a collection is a JSON object in a file named
`manifest.json` (schema: `schema/gilyon-manifest-0.1.schema.json`).

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `gilyon` | MUST | string | Format version of every file in the collection. |
| `id` | MUST | string | IRI of the collection. It differs from the `id` of every file. |
| `title` | SHOULD | string or language map | |
| `license` | MUST | string | Default licence, as `meta.license` (§4.3). |
| `attribution` | SHOULD | string | Credit line. |
| `texts` | MUST | object | The text declarations (§5) shared by every file. |
| `created`, `modified` | MAY | string | RFC 3339. |
| `sourceLanguage` | MUST if `languages` is present | string | BCP 47 tag of the source language. |
| `languages` | MUST if any file lists `bodies` | object | The languages of the collection (below). Keys are BCP 47 tags. |
| `files` | MUST | array | One entry per annotation document, in canonical order of content. |

Each entry of `files`:

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `path` | MUST | string | Location of the file: a URL reference [RFC 3986], resolved against the location of the manifest. Normally relative. |
| `sha256` | MUST | string | Lowercase hex SHA-256 of the file's bytes. |
| `books` | MUST | array of strings | USFM codes of the books whose text the file's annotations target. |
| `id` | SHOULD | string | The `id` of the document in the file. |
| `ref` | MAY | string | A reference (Appendix B) that covers the file's targets, e.g. `"JOS 1"`. |
| `annotations` | MAY | integer | Number of annotations in the file. |
| `bodies` | MAY | object | The body documents of this file (§16.2). Keys are BCP 47 tags declared in `languages`; each value has `path` (MUST), `sha256` (MUST), `id` (SHOULD) and `entries` (MAY, the number of entries). |

Each value of `languages`:

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `dir` | MUST | string | The folder, relative to the manifest, that holds the body documents of this language. |
| `title` | MAY | string or language map | Title of the collection in this language. |
| `license`, `attribution` | MAY | string | Where they differ from the collection's. |
| `translation` | MAY | object | Summary for a translated language: `status` (`"machine"`, `"reviewed"`, `"human"` or `"mixed"`) and `method`. The body documents govern. |

The name of a language folder (`dir`) MUST be the ISO 639-3 code of the
language in lower case, followed, where the tag has them, by `-` and the
script, region and variant subtags of the BCP 47 tag: `swe`, `eng`,
`srp-Cyrl`, `por-BR`. Two languages MUST NOT share a folder. The key of the
entry is the BCP 47 tag itself (`sv`, `en`, `sr-Cyrl`, `pt-BR`), which is
also the `meta.language` of the body documents in the folder.

The `texts` of every listed annotation document MUST equal those of the
manifest, and every listed file MUST have the manifest's `gilyon` version. A
Consumer SHOULD verify `sha256` before using a file.

```
manifest.json
gen001.gilyon.json              annotations: anchors, categories, links
jhn001.gilyon.json
eng/gen001.gilyon-bodies.json   the wording, source language
eng/jhn001.gilyon-bodies.json
swe/gen001.gilyon-bodies.json   a translation
swe/jhn001.gilyon-bodies.json
```

### 16.2 Body documents

When an annotation document declares `"bodies": "separate"`, it holds
everything about its annotations that does not depend on a language:
identifiers, targets, anchoring, categories, links and structures. The
wording is in body documents, one per language. Nothing is repeated between
them, and a corrected anchor is corrected in one place.

In such an annotation document, no annotation, structure unit or structure
relation has a `body`.

A body document is a JSON object in a file named `*.gilyon-bodies.json`
(schema: `schema/gilyon-bodies-0.1.schema.json`):

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `gilyon` | MUST | string | Format version. |
| `id` | MUST | string | IRI of this body document. |
| `of` | MUST | string | `id` of the annotation document whose bodies these are. |
| `meta` | MUST | object | As §4.3. `language` is REQUIRED here: every body in the document is in that language. `license` is the licence of these bodies. |
| `translationOf` | MAY | string | Default for every body in the document (§9.1). Absent in the source language. |
| `translation` | MAY | object | Default for every body in the document (§9.1). |
| `entries` | MUST | array | The bodies, in the order of the annotations. |

Each entry:

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `annotation` | MUST | string | `id` of an annotation in the annotation document. |
| `unit` | MAY | string | `id` of a unit of that annotation's structure: the bodies are a comment on that unit (§12.2). |
| `body` | MUST | array | Body objects (§9). `language`, when given, MUST equal `meta.language`. |

```json
{
  "gilyon": "0.1",
  "id": "https://example.org/notes/swe/gen001",
  "of": "https://example.org/notes/gen001",
  "meta": { "language": "sv", "license": "CC-BY-4.0",
            "creator": [ { "type": "Software", "name": "…" } ] },
  "translationOf": "en",
  "translation": { "status": "machine", "method": "…" },
  "entries": [
    { "annotation": "urn:uuid:31155b51-21cc-56f6-9c28-0246e3995354",
      "body": [ { "value": "De två hebreiska orden rimmar (tohu wa-bohu).",
                  "translation": { "sourceDigest": "…" } } ] }
  ]
}
```

Rules:

1. A body document has at most one entry for each pair of `annotation` and
   `unit`.
2. Every entry names an annotation of the document named by `of`, and a unit
   of that annotation where `unit` is given.
3. The body documents of the source language together hold a body for every
   annotation that requires one (§6.1). A translation MAY be incomplete.
4. The body documents of the source language carry neither `translationOf`
   nor `translation`. Every body in another language is a translation and
   has `translationOf`, its own or the document's.
5. An annotation document with separate bodies MUST be listed in a manifest
   together with its body documents (§16.1). A body document is not usable
   without its annotation document.
6. A Consumer joins the two by annotation `id`. Asked for a language, it uses
   the body in that language; where there is none, or where it will not show
   a stale or unreviewed one, it uses the body in the source language. The
   result is the annotation as it would be with those bodies inline.
7. A relation of a structure cannot be commented on in a body document in
   version 0.1; a comment on a relation is written as a comment on one of its
   units.

A document with inline bodies MAY still hold bodies in several languages
(§9). That form suits a small document and personal notes. It repeats
nothing either, but every language is fetched by every reader and a reviewer
of one language edits the file that holds the anchors.

### 16.3 Translation manifests

Anyone whom the licence permits MAY translate the bodies of a published
collection and publish the translation at another location, without any
change to the collection. The translation consists of body documents (§16.2)
and a **translation manifest**: a `manifest.json` with the member `of`.

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `gilyon` | MUST | string | Format version; that of the collection. |
| `id` | MUST | string | IRI of this translation. It differs from the `id` of the collection. |
| `of` | MUST | string | `id` of the collection that is translated. |
| `ofManifest` | SHOULD | string | Location of the collection's manifest: a URL reference, resolved against the location of this manifest. |
| `ofSha256` | MAY | string | SHA-256 of the collection's manifest as it was when the translation was made or last brought up to date. |
| `title`, `attribution`, `created`, `modified` | as §16.1 | | |
| `license` | MUST | string | Licence of the translated bodies. |
| `languages` | MUST | object | As §16.1. |
| `files` | MUST | array | One entry per annotation document for which bodies are provided. |

Each entry of `files` has `id` (MUST), the `id` of an annotation document of
the collection, and `bodies` (MUST), as in §16.1. It has no `path`, `sha256`
or `books`: those describe the annotation document, which the collection's
own manifest lists. A translation manifest has no `texts` and no
`sourceLanguage`.

```json
{
  "gilyon": "0.1",
  "id": "https://translator.example/notes-de",
  "of": "https://publisher.example/notes",
  "ofManifest": "https://publisher.example/notes/manifest.json",
  "license": "CC-BY-SA-4.0",
  "languages": { "de": { "dir": "deu", "translation": { "status": "machine" } } },
  "files": [
    { "id": "https://publisher.example/notes/gen001",
      "bodies": { "de": { "path": "deu/gen001.gilyon-bodies.json", "sha256": "…" } } }
  ]
}
```

Rules:

1. Every body in a translation is a translation in the sense of §9.1: it has
   `translationOf` and a `translation` record, its own or its document's. A
   translation manifest MUST NOT provide bodies in the source language of the
   collection.
2. The licence of the source bodies MUST permit the translation (§9.1 rule
   6, §15.1). The translation keeps the attribution of the collection and
   adds its own.
3. A translation holds nothing but bodies. It MUST NOT restate, add or
   change annotations, targets or anchors. A party that disagrees with an
   anchor publishes its own annotations.
4. The two parties need not coordinate. When the collection changes a body,
   the `sourceDigest` of its translations no longer matches and they are
   stale (§9.1). When the collection withdraws an annotation, a body that
   names it matches nothing, and a Consumer ignores it.
5. A Consumer that shows a collection in a language takes the annotations
   from the collection and the bodies from whichever manifest it has chosen
   for that language. It MUST make it possible to tell a translation
   published by the collection's own publisher from one published by another
   party.
6. A collection's manifest does not list the translations others have made
   of it. Finding them is the task of a catalogue (§16.4).

### 16.4 Catalogues

A catalogue lists collections and the translations of them, with the
locations of their manifests. It holds no annotations and no bodies. Because
a catalogue can list many collections in many languages, it is published in
**slices**, and an **index** names the slices. Both are JSON objects (schema:
`schema/gilyon-catalogue-0.1.schema.json`).

#### The index

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `gilyon` | MUST | string | Format version of the catalogue. |
| `id` | SHOULD | string | IRI of the catalogue. |
| `title`, `modified` | MAY | | |
| `counts` | MAY | object | Numbers of `collections`, `translations`, `publishers` and `languages`. |
| `languages` | MUST | object | Keys are BCP 47 tags. Each value has `path` (MUST), the location of the slice for that language, and MAY have `collections` and `translations` (numbers). |
| `publishers` | MUST | array | One object per publisher: `name` and `path` (MUST), the location of that publisher's slice; MAY `id`, `collections`, `translations`, `status`, `added`, and `maintainers` (below). |
| `collectionPath` | MAY | string | Template for the location of the slice of one collection, in which `{key}` stands for the first 16 hexadecimal digits of the SHA-256 of the collection's `id`. |

Locations are URL references, resolved against the location of the index.

#### A slice

A slice is a catalogue of its own: it has `gilyon` and `collections` (MUST),
and SHOULD have `slice`, an object with `by` (`"language"`, `"publisher"` or
`"collection"`) and `value`.

| Slice | Holds |
|---|---|
| by language | Every collection that can be read in that language: those that provide it themselves, and those for which a listed translation provides it. Under each collection, only the translations that provide that language. |
| by publisher | The collections of that publisher, each with all its translations; and the collections of others that the publisher has translated, each with that publisher's translations only. |
| by collection | One collection with all its translations. |

A small catalogue MAY be published as a single slice without an index.

#### An entry of `collections`

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `id` | MUST | string | `id` of the collection, as in its manifest. |
| `manifest` | MUST | string | Location of the collection's manifest: a URL reference, resolved against the location of the slice. |
| `license` | MUST | string | As in the manifest. |
| `title`, `attribution`, `licenseUrl` | MAY | | |
| `publisher` | SHOULD | agent | §15.2. |
| `sourceLanguage` | SHOULD | string | As in the manifest. |
| `languages` | SHOULD | array of strings | The languages the collection's own manifest provides. |
| `books` | MAY | array of strings | USFM codes of the books annotated. |
| `level` | MAY | integer | Highest conformance level among its documents. |
| `annotations` | MAY | integer | Number of annotations. |
| `hosting` | MAY | string | `"publisher"`: the manifest is where its publisher put it. `"republished"`: the catalogue's operator hosts a copy. |
| `repository` | MAY | string | Location of a version-controlled repository that holds the files, when there is one. |
| `status` | MAY | string | `"listed"` (default), `"flagged"` (a check failed; see `flag`) or `"withdrawn"`. |
| `flag` | MAY | object | For `"flagged"`: `since` and `reason`. |
| `added` | MAY | string | Date of first listing. |
| `checked` | SHOULD | object | The last verification (below). |
| `translations` | MAY | array | Translations of this collection published under translation manifests (§16.3). |

Each entry of `translations` has `id`, `manifest`, `license` and `languages`
(all MUST), and MAY have `title`, `publisher`, `attribution`, `repository`,
`status`, `flag`, `added`, `checked`, `translation` and `by`. `translation`
is an object with the summary `status` of §16.1 and `evidence`: `"recorded"`
when the operator has verified, from a record such as the history of a
repository, who reviewed the bodies marked `reviewed`; `"claimed"` when the
status rests on the translator's statement alone. `by` is `"publisher"` when
the translation comes from the publisher of the collection, `"third-party"`
otherwise.

`maintainers`, on a publisher in the index, names the persons answerable to
the catalogue's operator for that publisher's listings: each an object with
`github` (MUST, an account name), and MAY `name`, `role` (`"publisher"`: a
member of the publishing organisation; `"delegate"`: someone the publisher
has asked to act for it), `since`, and `delegation` (the location of the
publisher's statement that appoints a delegate). A catalogue MAY require
them.

`checked` records what the catalogue's operator verified and when:

| Member | Req. | Type | Meaning |
|---|---|---|---|
| `date` | MUST | string | RFC 3339 date or timestamp of the check. |
| `result` | MUST | string | `"ok"`, `"failed"` or `"unreachable"`. |
| `manifestSha256` | SHOULD | string | SHA-256 of the manifest as it was when checked. |
| `checks` | MAY | array of strings | Names of the checks that were made. |
| `revision` | MAY | string | The revision of `repository` that was checked. |
| `stale` | MAY | integer | Number of translated bodies found stale (§9.1). |
| `bodies` | MAY | object | Number of bodies by state: `source`, `machine`, `reviewed`, `human`. |
| `note` | MAY | string | |

Rules:

1. The manifest governs. What an entry repeats from a manifest (`license`,
   `languages`, `sourceLanguage`, `title`) is there for search and MUST agree
   with the manifest at the time of the check. A catalogue SHOULD derive
   these members from the manifests and not accept them from a person.
2. A catalogue states what it checked, not more. A member that reports a
   claim of the publisher which the operator did not verify (that a
   translation was reviewed, that an anchor was authored) is the publisher's
   claim. A Consumer MUST NOT present a listing as an endorsement of the
   content.
3. An entry is never reused for another collection. A collection that is no
   longer available keeps its entry with `status` `"withdrawn"`.
4. A Consumer that needs one language fetches the index and that language's
   slice. It SHOULD NOT need any other part of the catalogue to show the
   collections available in that language.
5. How a catalogue is maintained (who may register a publisher, how
   manifests are found and checked) is outside this specification.

## 17. Extensions and registries

### 17.1 Unknown members

A Consumer MUST ignore members it does not recognise and MUST preserve them
when it rewrites a document it has not otherwise changed in that part.

### 17.2 Extension members

Members whose names begin with `x-` are private extensions. A specification
member will never begin with `x-`. An extension that two independent
implementations exchange is a candidate for the next MINOR version.

### 17.3 Registries

The registries are versioned JSON files under `registries/`:

| File | Registers |
|---|---|
| `base-texts.json` | Base texts, their identifier form, pinned artefact, licence, stability policy, default flag. |
| `versifications.json` | Versification scheme names. |
| `categories.json` | The `gilyon` category vocabulary and registered external vocabularies. |
| `authorities.json` | Entity and identifier authorities for `links`. |
| `methods.json` | Anchoring methods. |

An entry is added by the process in `GOVERNANCE.md`. Entries are never removed;
they are marked deprecated.

## 18. Relation to other standards

*(informative; detailed in `docs/landscape.md`)*

| Standard | Relation |
|---|---|
| W3C Web Annotation Data Model | Gilyon is shaped as a profile: `id`, `motivation`, `body`, `target`, `selector`, `creator`, `created`, `modified` carry the same meaning. Gilyon adds word-identifier selectors, which that model anticipates as an extension. Appendix D gives the mapping. |
| MACULA Hebrew / Greek | Source of the default base texts and word identifiers. |
| Scripture Burrito Alignment Format | Not used by Gilyon. An alignment format an application can use to show annotations on a translation (§13); Gilyon word identifiers correspond to its `BCVWP` scheme with the edition as `docid`. |
| USFM Scripture Referencing Standard (U23003) | Appendix B is a subset of its verse-level syntax. Its word-level references address a translation and have no counterpart in Gilyon. |
| USFM TC Linkages (draft) | Complementary: a pointer file bound to one translation, which Gilyon does not address. A Gilyon annotation `id` is a suitable link target. |
| USFM / USX / USJ | Rendering targets: an application that has placed annotations in a translation (§13) can write them as `\f`, `\x`, `\ef`, `\esb`. |
| unfoldingWord Translation Notes | Convertible: quote + occurrence resolves to a `Words` selector; `SupportReference` becomes a `category`. |
| ACAI | Convertible: entity mentions become `identifying` annotations with `denotes` links. |
| Copenhagen Alliance versification, Paratext `.vrs`, TVTMS | Source of versification scheme names and mappings. |
| TEI, CTS URN, STAM, ISO LAF | Informative mappings only. |

## 19. Security and privacy considerations

1. **Active content.** Bodies come from untrusted sources. Consumers MUST
   sanitise HTML, MUST NOT execute scripts, and SHOULD NOT fetch remote
   resources referenced from a body without the user's consent.
2. **Personal data.** Personal annotations reveal religious belief and
   practice, which many jurisdictions treat as specially protected. A Producer
   exporting a user's annotations MUST NOT include creator names, e-mail
   addresses or timestamps unless the user has chosen to. `LicenseRef-private`
   documents MUST NOT be aggregated or published.
3. **Size.** Consumers SHOULD bound the size of bodies and the number of words
   in a selector they will process.
4. **Integrity.** A document that pins a base text by `sha256` lets a Consumer
   detect that it holds a different text. It does not authenticate the
   publisher; signatures are out of scope for 0.1.

---

## Appendix A. Canonical word identifiers (normative)

### A.1 Form

| Base text family | Form | Regular expression |
|---|---|---|
| Hebrew Bible (`WLCM`) | `o` `BB` `CCC` `VVV` `WWW` `P` | `^o[0-9]{12}$` |
| Greek New Testament (`N1904`, `SBLGNT`) | `n` `BB` `CCC` `VVV` `WWW` | `^n[0-9]{11}$` |

`BB` is the book number, `CCC` chapter, `VVV` verse, `WWW` the position of the
orthographic word in the verse from 001, and `P` the position of the morpheme
part within that word from 1. These are the `xml:id` values of the MACULA
datasets, unchanged.

Examples: `o010010010011` (Genesis 1:1, word 1, part 1: בְּ),
`o010010010012` (Genesis 1:1, word 1, part 2: רֵאשִׁית),
`n40001001001` (Matthew 1:1, word 1: Βίβλος).

### A.2 Canonical spelling

Producers MUST write word identifiers with the `o` or `n` prefix. Consumers
SHOULD accept, on input from other systems, the same digits without the
prefix, and MUST write the prefixed form.

### A.3 Book numbers

`BB` is 01–39 for the books of the Hebrew Bible in the order of the
Protestant Old Testament (01 Genesis … 39 Malachi) and 40–66 for the New
Testament (40 Matthew … 66 Revelation). The correspondence with USFM book
codes is given in `registries/base-texts.json`. Books outside this range are
not addressable in 0.1 (`docs/open-issues.md` §5).

### A.4 Canonical order

Within one edition, the canonical order of words is the numeric order of the
digit strings. Hebrew identifiers (12 digits) and Greek identifiers (11
digits) are never compared with one another.

### A.5 Interpretation

The components of an identifier are *not* to be parsed to obtain a verse
reference for display or versification purposes; the base text's own data
gives the reference. Identifiers are opaque names whose only guaranteed
property is the order of A.4.

## Appendix B. Reference syntax (normative)

```
reference   = book [ SP chapter-part ]
chapter-part= chapter [ ":" verse-part ] [ "-" range-end ]
range-end   = chapter ":" verse-part / verse-part / chapter
verse-part  = verse [ subverse ]
book        = 3(ALPHA / DIGIT)        ; USFM book code, upper case
chapter     = 1*3DIGIT
verse       = 1*3DIGIT / "title"
subverse    = %x61-7A                 ; a-z
```

Examples: `JOS`, `JOS 1`, `JOS 1-3`, `JOS 1:1`, `JOS 1:1-3`, `1SA 20:42-21:1`,
`PSA 3:title`, `LUK 11:2b`.

1. Book codes are the USFM 3-character book identifiers, in upper case.
2. A range end without `:` is a verse if the range start has a verse, else a
   chapter.
3. A reference never crosses books. Use an array of targets.
4. `PSA 3:title` denotes a psalm superscription where the versification does
   not number it; `PSA 3:0` (the U23003 form) is accepted as equivalent on
   input.
5. This syntax is a subset of the USFM Scripture Referencing Standard at verse
   level. Consumers SHOULD accept `.` in place of `:` on input.

## Appendix C. Anchoring an annotation authored on a translation (informative)

The following procedure is implemented in the `bcv-commons` tooling and was
used to anchor the 292 inline notes of a Swedish study Bible on the book of
Joshua. It is registered as method `bcv-lexeme-anchor/1`.

1. Locate the note in the verse of the translation. This position is used
   only while the procedure runs; it is not written to the document.
2. From the alignment between the base text and that translation, find the
   nearest aligned *content* word before the position and the nearest after
   it. A content word of the alignment can consist of more than one word of
   the base text (a compound name such as בֵּית אָוֶן); the last of them is
   used on the side before the position and the first on the side after it.
3. Emit a `Point` with those two words as `after` and `before`.
4. Grade it:
   - **high** — the two words are consecutive among content words and their
     tokens are adjacent to the position;
   - **medium** — the two words are consecutive among aligned content words,
     with only function words or unaligned material between them;
   - **low** — content words that could not be aligned lie between them (a
     gap), or no word was found on one side although the verse continues;
   - a note at the end of its verse has no following word in that verse: emit
     a one-sided point with `after` only, graded **high** or **medium** by
     the same rules applied to the preceding side;
   - when the two sides come out in contradictory order, emit a one-sided
     point with `after` only, `detail` `"REVERSED"` and tier **low**.
5. When no word is found before the position, emit `unresolved` with a
   `Passage` selector.

Function words lie between most pairs of consecutive content words, so most
points of this method are gaps in the sense of §7.5 even at tier **high**.

On Joshua this gave 22% high and 86% high or medium; 163 notes received a
two-sided point (16 of them exact), 120 a one-sided point and 9 were
unresolved. Low and unresolved anchors are the review queue for a person, who
sets `status` to `reviewed`. Because the document holds no position in the
translation, a reviewer works from the publication itself.

Known limits of this method: it uses content words only, it produces points
and not spans, and several notes in one verse can receive the same point (use
`sequence`, §6.3).

## Appendix D. JSON-LD context and Web Annotation mapping (informative)

A Gilyon document is plain JSON. A document MAY carry
`"@context": "https://gilyon.org/0.1/context.jsonld"`. A draft of that
context is in `context/gilyon-0.1.context.jsonld`; its limits are listed in
`docs/open-issues.md` §8. The intended mapping is:

| Gilyon | Web Annotation |
|---|---|
| annotation object | `oa:Annotation` |
| `motivation` | `oa:motivatedBy`; Gilyon-only values are `skos:broader` existing ones (`identifying` and `classifying` → `oa:identifying`, `oa:classifying`). |
| `body[].value`, `language`, `format`, `purpose` | `oa:TextualBody` with `rdf:value`, `dc:language`, `dc:format`, `oa:hasPurpose` |
| `target` with `text` and `selector` | `oa:SpecificResource` with `oa:hasSource` (the base text edition IRI) and `oa:hasSelector` |
| `Words`, `Range`, `Point`, `Passage`, `Lexeme`, `Composite` | subclasses of `oa:Selector` in the `gilyon:` namespace |
| `creator`, `created`, `modified`, `license` | `dcterms:creator`, `dcterms:created`, `dcterms:modified`, `dcterms:rights` |
| `anchoring`, `structure`, `links` | terms in the `gilyon:` namespace |

The Web Annotation specifications are cited and profiled, not reproduced.

## Appendix E. References

### Normative

- [RFC 2119] Key words for use in RFCs to Indicate Requirement Levels. [RFC 8174] Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words.
- [RFC 3986] Uniform Resource Identifier (URI): Generic Syntax.
- [RFC 7493] The I-JSON Message Format.
- [RFC 3339] Date and Time on the Internet: Timestamps.
- [RFC 8785] JSON Canonicalization Scheme (JCS).
- [BCP47] Tags for Identifying Languages (RFC 5646, RFC 4647).
- [UAX15] Unicode Standard Annex #15, Unicode Normalization Forms.
- [SPDX] SPDX License List, https://spdx.org/licenses/
- [SEMVER] Semantic Versioning 2.0.0, https://semver.org/
- [COMMONMARK] CommonMark Spec, https://spec.commonmark.org/
- [JSON-SCHEMA] JSON Schema, draft 2020-12.
- MACULA Hebrew, Clear Bible / Biblica, https://github.com/Clear-Bible/macula-hebrew (CC BY 4.0).
- MACULA Greek, Clear Bible / Biblica, https://github.com/Clear-Bible/macula-greek (CC BY 4.0).
- USFM book identifiers, https://docs.usfm.bible/

### Informative

- W3C Web Annotation Data Model, Vocabulary and Protocol, W3C Recommendations, 23 February 2017.
- Scripture Burrito Alignment Format 0.4, https://github.com/bible-technology/alignment-spec
- USFM Scripture Referencing Standard 1.0 and Linkages File draft, USFM Technical Committee, https://github.com/usfm-bible/tcdocs
- Copenhagen Alliance versification specification, https://github.com/Copenhagen-Alliance/versification-specification
- STEPBible TVTMS, https://github.com/STEPBible/STEPBible-Data
- unfoldingWord Translation Notes; ACAI (Bible Aquifer); TIPNR; OpenBible.info geocoding.
- STAM, Stand-off Text Annotation Model; ISO 24612 Linguistic Annotation Framework; Text-Fabric.
