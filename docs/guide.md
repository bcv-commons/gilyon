# Implementer's guide

How to produce and consume Gilyon 0.1 documents. This page is informative.
Where it and the specification disagree, the specification governs. Section
numbers refer to `spec/gilyon-0.1.md`.

## Part 1. Producing a document

### 1. Choose a level

| You have | Level | Selectors you will use |
|---|---|---|
| Notes tied to verses | 0 | `Passage` |
| Notes tied to Hebrew or Greek words, by hand or by a procedure | 1 | `Words`, `Range`, `Point`, `Lexeme`, `Composite`, and `Passage` where nothing finer is known |
| Analyses of structure | 2 | The above, plus `structure` |

Write the level in `conformsTo`. A Level 1 document may still contain verse
targets.

### 2. Declare the texts

Every target names a text by a local name declared in `texts` (§5).

For verse-level targets, declare a reference text. It stands for the Bible as
numbered by one versification:

```json
"texts": { "org": { "role": "reference", "versification": "org" } }
```

For word-level targets, declare a base text and pin its release:

```json
"texts": {
  "heb": { "role": "base", "edition": "WLCM",  "release": "26.04.13" },
  "grc": { "role": "base", "edition": "N1904", "release": "24.06.17" }
}
```

| `edition` | Text | Source of the identifiers |
|---|---|---|
| `WLCM` | MACULA Hebrew | https://github.com/Clear-Bible/macula-hebrew |
| `N1904` | MACULA Greek, Nestle 1904 | https://github.com/Clear-Bible/macula-greek |
| `SBLGNT` | MACULA Greek, SBLGNT (not a default) | the same repository |

If you work from a state of the dataset between two releases, give its commit
as `revision` and the latest release it contains as `release` (§5.2).

### 3. Write word identifiers

Take the `xml:id` of the MACULA word, unchanged, with its prefix: `o` and 12
digits for Hebrew, `n` and 11 digits for Greek (Appendix A). Do not build
identifiers from a verse reference and a word count of your own; look them up
in the dataset.

In `Words`, list the identifiers in ascending order without repeats.

Add `check` for anchors a person chose. It records the surface form the
author saw, so that a Consumer holding a different text can detect it:

```json
{ "type": "Words", "ref": "GEN 1:1",
  "words": ["o010010010021"],
  "check": { "o010010010021": "בָּרָ֣א" } }
```

All strings in a document are in Unicode Normalization Form C.

### 4. Pick the selector that says what you know

| Situation | Selector |
|---|---|
| The note is about one word or a few words | `Words` |
| The note is about a continuous stretch of more than three words | `Range` |
| The note sits at a place between words (a footnote caller, an inline remark) | `Point` with `after` and `before` |
| You know the word before the place but not the one after, or the reverse | `Point` with one of them |
| You know the place only to within a few words | `Point` whose `after` and `before` are not adjacent (a gap) |
| You know only the verse | `Passage`, with `anchoring.status` `unresolved` if a word anchor was attempted |
| The note is about a word as a dictionary entry | `Lexeme` |

Do not narrow a position beyond your evidence (§8.3).

### 5. Record the anchoring

Every word-level target carries `anchoring` (§8):

```json
"anchoring": { "status": "authored" }
```

```json
"anchoring": { "status": "derived", "method": "bcv-lexeme-anchor/1", "tier": "medium" }
```

`method` is required for `derived`. Use a name from
`registries/methods.json`, or an IRI that describes your procedure. When a
person who reads the language confirms a derived anchor, change `status` to
`reviewed` and keep the annotation `id`.

Give a `fallback` verse on word-level targets, so that a Consumer that cannot
resolve the words can still show the annotation.

### 6. Classify

`motivation` says what kind of act the annotation is; exactly one value
(§10.1). `category` says what it is about; any number of terms (§10.2).

| Material | `motivation` | `category` |
|---|---|---|
| Study note | `commenting` | `gilyon:note/study` |
| "Or: …", "Literally: …" | `describing` | `gilyon:note/alternative`, `gilyon:note/literal` |
| Cross reference | `linking` | `gilyon:crossref/see-also` and others |
| Figure of speech | `classifying` | `gilyon:figure/…` |
| Chiasm, parallelism | `classifying` | `gilyon:structure/…` |
| Who or what is meant | `identifying` | `gilyon:entity/…` |
| Highlight | `highlighting` | none needed |

The category list is in `registries/categories.json`. Other registered
vocabularies can be used beside it.

### 7. Write bodies and links

- One body per language. Mark a translated body with `translationOf` (§9).
- Plain text is the default `format`. Markdown and a restricted HTML are
  allowed.
- Give Scripture references that occur in a note as `links` as well, so that
  they survive when the note is translated (§11):

```json
"links": [
  { "rel": "crossReference",
    "target": { "text": "org", "selector": { "type": "Passage", "ref": "DEU 34:5-8" } } }
]
```

- Persons and places are linked with `denotes` and an entity identifier, for
  example `acai:person:Joshua` (`registries/authorities.json`).

### 8. Mint identifiers that last

The `id` of an annotation is permanent (§14.2). Editing the body, adding a
language or improving the anchor does not change it, and it is never reused
for another annotation. Mint IRIs under a domain you control, or use
`urn:uuid:`.

If your source gives notes no identity of their own, decide how a note keeps
its `id` across editions before you publish. A scheme that counts notes
within a verse breaks when a note is inserted.

### 9. State the licence

`meta.license` is required: an SPDX identifier, or `LicenseRef-<name>` with
`licenseUrl` (§4.3, §15). One annotation can override it. Use
`LicenseRef-private` for personal annotations that are not offered for
redistribution.

The licence of your annotations is independent of the licence of the base
text.

### 10. Validate

```
uv run --with jsonschema tools/validate.py my-notes.gilyon.json
```

A body document (`*.gilyon-bodies.json`) can be checked the same way, and a
`manifest.json` checks a whole collection.

The validator applies the JSON Schema and the rules a schema cannot express,
such as identifier order in `Words` and the agreement between selector and
text role. It exits with status 0 when every file is valid. It does not look
identifiers up in a base text.

### 11. Split a large collection

Split by book or chapter. Each file is a complete document with its own
`id`. Add a `manifest.json` beside them (§16.1):

```json
{
  "gilyon": "0.1",
  "id": "https://example.org/notes",
  "license": "CC-BY-4.0",
  "texts": { "heb": { "role": "base", "edition": "WLCM", "release": "26.04.13" } },
  "files": [
    { "path": "jos001.gilyon.json", "sha256": "…", "books": ["JOS"], "ref": "JOS 1", "annotations": 31 }
  ]
}
```

The `texts` of every file equal those of the manifest. Validate the whole
collection by passing the manifest:

```
uv run --with jsonschema tools/validate.py my-collection/manifest.json
```

### 12. Publish in more than one language

Keep the wording apart from the annotations (§16.2). In each annotation
document, declare `"bodies": "separate"` and leave out every `body`. Put the
wording in body documents, one per annotation document and language:

```json
{
  "gilyon": "0.1",
  "id": "https://example.org/notes/eng/gen001",
  "of": "https://example.org/notes/gen001",
  "meta": { "language": "en", "license": "CC-BY-4.0" },
  "entries": [
    { "annotation": "urn:uuid:31155b51-21cc-56f6-9c28-0246e3995354",
      "body": [ { "value": "The two Hebrew words rhyme (tohu wa-bohu)." } ] }
  ]
}
```

Name each language folder by the ISO 639-3 code, with script, region or
variant subtags where the language tag has them: `eng`, `swe`, `srp-Cyrl`,
`por-BR`. Declare the languages and the source language in the manifest, and
list each body document under its annotation document:

```json
"sourceLanguage": "en",
"languages": {
  "en": { "dir": "eng" },
  "sv": { "dir": "swe", "translation": { "status": "machine" } }
},
"files": [
  { "path": "gen001.gilyon.json", "sha256": "…", "books": ["GEN"],
    "bodies": {
      "en": { "path": "eng/gen001.gilyon-bodies.json", "sha256": "…" },
      "sv": { "path": "swe/gen001.gilyon-bodies.json", "sha256": "…" }
    } }
]
```

The source language must have a body for every annotation that needs one. A
translation may be incomplete.

### 13. Draft, review and maintain translations

A translated body document states `translationOf` and `translation` once for
the whole file. Each body adds the digest of the wording it was made from
(§9.1):

```json
"translationOf": "en",
"translation": { "status": "machine", "method": "<software and version>" },
"entries": [
  { "annotation": "urn:uuid:…",
    "body": [ { "value": "…", "translation": { "sourceDigest": "<sha256 of the source value>" } } ] }
]
```

| Step | What changes |
|---|---|
| Software drafts a translation | `status` `machine`; a `creator` of type `Software`; `sourceDigest` of the source wording. |
| A person confirms or corrects a body | On that body: `status` `reviewed`, `reviewer`, `date`. The annotation `id` does not change. |
| The source wording is edited | Nothing in the translation. Its `sourceDigest` no longer matches, so it is stale. |
| The stale translation is redone | New `value`, new `sourceDigest`, and the status it now has. |

The validator reports stale translations as warnings when it checks the
manifest. Translating is making a derivative: check that the licence of the
source bodies allows it.

### 14. Translate a collection published by someone else

Check first that the licence of its bodies permits translation. Then publish,
at an address of your own:

- one body document per annotation document you translate, in a folder named
  for your language, each with `translationOf`, a `translation` record and a
  `sourceDigest` per body (step 13);
- a translation manifest (§16.3): a `manifest.json` with `of`, the `id` of
  the collection, and `ofManifest`, the address of its manifest.

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

Publish bodies only. Do not copy or change the annotations. Keep the
publisher's attribution and add your own. To be found, register as a
publisher in the catalogue and name your manifest there
(`docs/catalogue.md`).

## Part 2. Consuming a document

A Consumer (§2.3):

1. **Accepts every conforming document** of the levels it claims.
2. **Ignores members it does not know** and keeps them when it rewrites a
   document (§17.1). Members that begin with `x-` are private extensions.
3. **Resolves word identifiers only together with the edition** named by the
   target's text. `n40001001001` in `N1904` and in `SBLGNT` are not the same
   claim.
4. **Checks the pin.** If it holds another release of the base text, it
   applies the published migration maps or reports that it cannot (§14.3).
   It compares `check` values with its text, after NFC normalisation and
   ignoring cantillation marks, and reports a mismatch.
5. **Never drops an annotation silently.** When a target cannot be resolved,
   it uses `fallback` if present and reports the failure.
6. **Shows the anchoring status**, or lets users filter on it. It does not
   present a `derived` anchor as confirmed.
7. **Finds collections through a catalogue** by fetching its index and the
   slice of the language it shows (§16.4), not the whole catalogue.
8. **Joins bodies to annotations** when a document declares
   `"bodies": "separate"`: it reads the body document of the language it
   shows from the manifest and matches entries to annotations by `id`
   (§16.2). Where that language has no body, it uses the source language. It
   does not present a `machine` translation as reviewed. When the bodies
   come from a translation manifest of another party (§16.3), it lets the
   user see that.
9. **Sanitises bodies** before display and does not run scripts or fetch
   remote resources from them without the user's consent (§19).
10. **Respects licences per annotation**, and does not aggregate or publish
   `LicenseRef-private` documents (§15.1).

### Showing annotations in a translation

Gilyon ends at the original-language words. To place an annotation in a
translation, an application needs a word alignment between that translation
and the base text, from any source. It looks up which words of the
translation render the anchored words (§13). Expect three cases:

- The anchored words map to one continuous place. Show the annotation there.
- They map to a discontinuous or partial place, because the translation
  reorders or merges words. Mark what is found, or fall back to the verse.
- They map to nothing, because the translation omits them. Use `fallback`.

A `Point` with a gap, or with one neighbour, gives an interval in the
translation, not an exact position. Do not show more precision than the
anchor has.

## Part 3. Deriving anchors

An Anchorer is a Producer that works out original-language anchors for
annotations written on a translation (§8.3). It:

1. sets `status` to `derived` and names its `method`;
2. emits a gap `Point`, a one-sided `Point` or `unresolved` where its
   evidence is incomplete;
3. does not write the position in the translation it worked from;
4. keeps annotation identifiers unchanged when it refines an existing
   document.

Appendix C describes one such procedure, `bcv-lexeme-anchor/1`. It places a
note between the nearest aligned content words on either side.

A derived collection cannot be corrected from the document alone, since the
document holds no translation. Keep the translation and the alignment beside
your pipeline and check the anchors against them before publishing: locate
each note in the translation and confirm that it stands between the words
the alignment gives for its anchor. Such a check does not show that the
alignment itself is right.

## Converting existing material

| Source | Conversion |
|---|---|
| Verse-anchored notes in any format | Level 0: one annotation per note, `Passage` selector. |
| USFM `\f`, `\x`, `\ef` | The note text becomes a body; the caller position needs an alignment to become a `Point`, or stays a `Passage`. |
| unfoldingWord Translation Notes | Quote plus occurrence resolves to `Words` or `Range` (method `quote-occurrence/1`); `SupportReference` becomes a `category`. |
| ACAI entity mentions | `identifying` annotations with `denotes` links. |

These are outlines. No converter for them is published here yet.
