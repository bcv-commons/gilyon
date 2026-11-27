# Gilyon in brief

An introduction for people deciding whether Gilyon fits their notes or their
application. The specification (`spec/gilyon-0.1.md`) is the authority; this
page explains it and points into it.

## What it is

Gilyon is a JSON format for Bible annotations: study notes, footnotes,
translation notes, cross references, personal notes and highlights, figures
of speech, and structures such as chiasms.

An annotation is kept outside the Bible text and points into it. What it
points at is a set of **Hebrew, Aramaic or Greek words**, named by their
published identifiers. It never points at a place in a translation.

## Why the original languages

A note written on one translation is usually tied to that translation: to a
caller mark, a character offset or a quoted phrase. It cannot be moved to
another translation or another language without someone placing it again by
hand.

Every translation renders the same Hebrew, Aramaic and Greek words. If a note
says which of those words it is about, any application that knows how its
translation corresponds to those words can show the note in the right place.
The note is written once and used with any translation.

Those words have open identifiers. The MACULA datasets of Clear Bible and
Biblica (CC BY 4.0) give every word of the Hebrew Bible and the Greek New
Testament an identifier:

| Identifier | Word |
|---|---|
| `o010010010012` | Genesis 1:1, word 1, part 2: רֵאשִׁית |
| `o010010010021` | Genesis 1:1, word 2: בָּרָא |
| `n43001001005` | John 1:1, word 5: Λόγος |

Hebrew identifiers reach the parts of a word (prefix, stem, suffix). Greek
identifiers stop at the word.

## One annotation

A translation note attached to a position in Genesis 1:2, after בֹהוּ and
before the next word:

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
  },
  "presentation": { "placement": "footnote" }
}
```

| Member | What it says |
|---|---|
| `id` | A permanent name for this annotation. It never changes and is never reused. |
| `motivation` | What kind of act this is: a comment, a classification, a link, a highlight. |
| `category` | What the annotation is about, from a registered vocabulary. |
| `body` | The content. In a collection it is usually kept in a separate file per language (below). |
| `target` | Which words, in which text. |
| `anchoring` | How the anchor was obtained and how far it can be trusted. |
| `fallback` | The verse to use if the words cannot be resolved. |

The complete file is `examples/01-word-notes-gen-1-1.gilyon.json`.

## A document

Annotations travel in a document, which states once what all of them share:

```json
{
  "gilyon": "0.1",
  "conformsTo": 1,
  "id": "urn:uuid:…",
  "meta": { "title": "…", "language": "en", "license": "CC-BY-4.0" },
  "texts": {
    "heb": { "role": "base", "edition": "WLCM", "release": "26.04.13" }
  },
  "annotations": [ … ]
}
```

`texts` is where the base text is pinned. A word identifier has meaning only
together with an edition and a release of it: the same identifier string can
name different words in two editions of the Greek New Testament. Version 0.1
registers MACULA Hebrew (`WLCM`) and MACULA Greek Nestle 1904 (`N1904`) as
default base texts, and MACULA Greek SBLGNT as an alternative.

## Six ways to point

| Selector | Selects | Typical use |
|---|---|---|
| `Passage` | Whole verses, a chapter or a book | Verse-level notes; introductions |
| `Words` | A set of words, adjacent or not | A note on one word or a phrase; a highlight |
| `Range` | Every word from one word to another | A clause; a unit of a structure |
| `Point` | A position between two words | A footnote caller; a break in a sentence |
| `Lexeme` | A lexeme wherever it occurs | A glossary or key-term note |
| `Composite` | Several of the above as one target | A discontinuous phrase |

A `Point` can be given with one neighbour only, and its two neighbours need
not be adjacent. This lets a publisher say exactly as much as is known about
a position and no more.

## Saying how an anchor was obtained

Most existing notes were written on a translation. Their Hebrew or Greek
anchors are worked out afterwards, by a person or by software, and some are
more certain than others. Gilyon requires every word-level anchor to say
which it is:

| `status` | Meaning |
|---|---|
| `authored` | The author chose these words directly. |
| `reviewed` | Derived by a procedure, then confirmed by a person who reads the language. |
| `derived` | Derived by a procedure, not yet confirmed. The procedure is named in `method`. |
| `unresolved` | No word-level anchor could be found; the target is the verse. |

A derived anchor can also carry a `confidence` or a `tier` (high, medium,
low). An application must not present a derived anchor as editorially
confirmed.

## Three levels of adoption

| Level | A document at this level | Who starts here |
|---|---|---|
| 0, Passage | Points at verses only | A publisher with verse-anchored notes |
| 1, Word | Points at words of a pinned base text | A publisher with word-exact notes, or with derived anchors |
| 2, Structure | Also describes structures | Analyses of chiasm, parallelism, inclusio |

A publisher can issue Level 0 today and refine the anchors later. The
annotation identifiers stay the same.

## Structures

A structure is one annotation that divides a stretch of text into labelled
units and says how they relate: which units correspond, which contrast, which
one carries the emphasis. `examples/02-structure-jhn-1-1.gilyon.json` shows
the three linked clauses of John 1:1.

## What Gilyon leaves out

- **Translations.** A document holds no position in a translation: no token
  or character offsets and no quoted translation text as an anchor. Showing
  an annotation in a translation is the application's work, through a word
  alignment it holds (spec §13).
- **Bible text, alignments, versification maps, lexicons, a critical
  apparatus, an API.** Existing work is referenced for each (spec §18).
- **Books outside the 66**, at word level: no open word identifiers were
  found for the Septuagint or the deuterocanonical books. They can be
  annotated at verse level.

## One anchor, many languages

The anchor of a note does not depend on the language the note is written in.
Gilyon therefore lets a collection keep the two apart:

```
manifest.json
gen001.gilyon.json              the annotations: anchors, categories, links
eng/gen001.gilyon-bodies.json   the wording, in the source language
swe/gen001.gilyon-bodies.json   the wording, translated
```

The annotation file is written once and holds no note text. Each language has
a folder, named by its ISO 639-3 code, with one file of wording per
annotation file. Nothing is copied between them: a corrected anchor is
corrected in one place, and a reviewer of the Swedish text edits only the
Swedish file.

Every translated body says how it came about:

| `status` | Meaning |
|---|---|
| `machine` | Made by software, not confirmed by a person. |
| `reviewed` | Made by software, then confirmed or corrected by a person who knows both languages. |
| `human` | Made by a person. |

It also carries a digest of the wording it was translated from. When the
source note is edited, the digest no longer matches and the translation is
known to be stale. This is what makes machine-drafted translations workable:
they can be published as drafts, reviewed one by one, and re-queued when the
source changes.

A small document can still carry its bodies inline, in one language or
several (spec §9, §16.2).

## Translating someone else's collection

A translator does not need the publisher's cooperation, only a licence that
permits translation. The translator publishes the translated text files on a
server of their own, with a short manifest that names the collection they
belong to (spec §16.3):

```
publisher.example/notes/manifest.json        the collection
translator.example/notes-de/manifest.json    "a translation of that collection"
translator.example/notes-de/deu/…            the German wording, nothing else
```

A reading application takes the anchors from the publisher and the German
text from the translator. When the publisher edits a note, the translator's
version of it shows as stale. `examples/translation-elsewhere/` is such a
translation of `examples/collection/`.

## The catalogue

Applications find collections, and the translations others have made of
them, through a catalogue: manifest addresses with the result of the checks
made on each (spec §16.4). It is published in slices, so that an application
fetches a short index and the one file for its language, however many
collections exist.

The Gilyon catalogue will be at `https://gilyon.org/collections/`. It points
to collections where their publishers host them. Publishers are registered
once, each with a named person who answers for its listings; what they
publish is then read from their own manifests. `docs/catalogue.md` describes
this.

`examples/collection/` is a collection in English with a machine-drafted
Swedish translation.

## Large collections

A collection can be one file, or it can be split by book or chapter. A
`manifest.json` lists the files with their checksums, and the languages
(spec §16.1). A reading application then fetches only the chapter on screen,
in the language it shows.

## Relation to the W3C Web Annotation model

Gilyon is shaped as a profile of the W3C Web Annotation Data Model: `id`,
`motivation`, `body`, `target` and `selector` mean what they mean there.
Gilyon adds what that model leaves open: selectors for Bible words, the
anchoring record, and structures. A document is plain JSON and needs no
semantic-web tooling. A first draft of a JSON-LD context that maps it to the
W3C vocabulary is in `context/` (spec Appendix D).

## Status

Working Draft 0.1, 2026-11-27. It has not been reviewed outside the
bcv-commons team, and anything may change before 1.0. `docs/open-issues.md`
lists what is undecided.

## Where to go next

| To | Read |
|---|---|
| Write or read Gilyon documents | `docs/guide.md` |
| See the exact rules | `spec/gilyon-0.1.md` |
| Use a collection with a particular Bible edition | `docs/bible-editions.md` |
| Get a collection or a translation listed | `docs/catalogue.md` |
| See how Gilyon relates to other standards | `docs/landscape.md` |
| See what is still open | `docs/open-issues.md` |
