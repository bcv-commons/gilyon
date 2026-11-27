# Gilyon and Bible editions

How a Gilyon collection is used with the Bible editions catalogued in
[bcv-commons/bibles](https://github.com/bcv-commons/bibles). This page is
informative. Statements about the catalogue reflect its documentation on
2026-11-27; the catalogue's own documentation governs.

## The short answer

A Gilyon document names no Bible edition other than its base text. It points
at Hebrew, Aramaic and Greek words, so it is not written *for* any of the
catalogued editions and it works with all of them in principle.

What connects an annotation to a given edition is held by the application,
outside the document:

| The application needs | It comes from |
|---|---|
| The annotation and its anchor (original-language words) | The Gilyon collection |
| The text of the edition, read the same way by everyone | The `bibles` catalogue and its `tools/verse-text` |
| Which words of the edition render which original words | A word alignment for that edition |
| The numbering of the edition's verses | The catalogue's versification data |

Gilyon defines the first row only.

## What the catalogue provides

`bcv-commons/bibles` lists Bible editions from many sources (helloAO,
eBible.org, Biblica's openbible, Door43, CrossWire, the Digital Bible
Platform and others), compares them by their actual text, and says how to
read each one. The parts that matter here:

| Catalogue part | What it gives | Used for |
|---|---|---|
| Source identifiers (`h:eng_kjv`, `e:engoebus`, `o:OCCB-CEB`) | One name per edition per source | Saying which edition an application shows |
| `text-route.json` | The one canonical text of each edition and the route to read it | Getting the verse text |
| `tools/verse-text` | One extraction rule, one tokenizer and one text fingerprint, in Python and JavaScript | Counting the words of a verse the same way as the alignment does |
| `edition-struct.json` | Licence, script, direction, whether words are spaced, Unicode normalisation | Display, and knowing what can be redistributed |
| Versification files and `_vrs/map` | The numbering scheme of an edition and verse-precise maps between schemes | Resolving `Passage` targets and Scripture references |

The catalogue is served from `https://cdn.bibel.wiki/catalog/`. Its
`doc/README.md` is the place to start.

## Showing an annotation in an edition

Take the note in the README: a position in Genesis 1:2 after
`o010010020042` and before `o010010020051`. To show it in, say, an English
edition, an application:

1. **Picks the edition** in the catalogue and reads the text of Genesis 1:2
   through the route given in `text-route.json`.
2. **Tokenizes the verse** with `tools/verse-text`. The words of the verse
   are now numbered.
3. **Looks up the alignment** of that edition for that verse. It says which
   numbered words of the edition render which original-language words.
4. **Finds the words** that render the two anchor words. The note belongs
   between them.
5. **Falls back to the verse** when the alignment has nothing for the anchor
   words, or when they come out in an order that leaves no place between
   them.

Step 3 depends on the alignment having been made on the same text the
application holds. The text fingerprint of `tools/verse-text` is the check:
an alignment keyed to one fingerprint does not apply to a text with another.
An alignment made on a slightly different state of an edition can name word
positions that do not exist in the text at hand.

## Where alignments come from

Gilyon does not define or carry alignments (spec §13). Within bcv-commons
there are two sources:

- **[lexeme-aligner](https://github.com/bcv-commons/lexeme-aligner)**
  computes word alignments between translations and the Hebrew and Greek. Its
  per-verse alignments address the words of a translation by their position
  among the tokens of `tools/verse-text`. It can also align a text of your
  own on your own machine. Which editions have a published per-verse
  alignment is stated in that repository, not here.
- **Door43 Gateway Language texts**, which the catalogue republishes, carry
  word alignments made by their translators.

Two points to check before relying on an alignment:

- **How it names original-language words.** Gilyon uses MACULA word
  identifiers. An alignment that names original words another way (by
  lexeme, or by a count of content words in the verse) needs a lookup to
  MACULA identifiers before it can be joined to a Gilyon anchor. The lookup
  must be made against the same release of the base text that the Gilyon
  document pins.
- **Which Greek text it was made on.** An alignment to SBLGNT or another
  Greek text does not apply directly to anchors on Nestle 1904. A published
  word map between the two editions is needed (spec §14.4).

## Verse numbering

A `Passage` target, a `fallback` and a Scripture reference in `links` are
verse references in the versification of the text they name (spec §5.3). The
default is `org`: the Hebrew numbering of MACULA Hebrew and the numbering of
Nestle 1904.

Many editions number some verses differently. Psalm titles are the common
case: verse 1 in the Hebrew numbering, unnumbered in most English editions.
An application showing a verse-level annotation in such an edition converts
the reference with the catalogue's versification maps.

Word-level targets need no conversion. The word identifier decides, and the
alignment leads to the right verse of the edition whatever its number is
there.

## Collections that began on one edition

Most existing notes were written on one translation. When such notes are
converted to Gilyon, their anchors are derived from that edition and an
alignment of it (spec §8, Appendix C), and the result no longer depends on
the edition:

| | |
|---|---|
| **In the document** | Original-language anchors, with `anchoring.status` `derived` and the method. |
| **Not in the document** | Where the note stood in the edition. No token positions, no quoted text. |
| **Allowed** | Naming the edition as the origin of the collection, in `meta.source` or `meta.description`. That is a citation, not an anchor. |

Shown again in the edition it came from, a note lands where its anchor words
are rendered, which is where it stood if the anchor is right. The party that
derives the anchors can use exactly this as a check before publishing: place
every note back into the original edition and compare with where it actually
stands.

## Licences

Three licences are in play and they are independent:

| Thing | Licence |
|---|---|
| The annotations | Stated in the Gilyon document, per collection or per annotation. |
| The base text and its word identifiers | MACULA: CC BY 4.0. |
| The edition shown to the reader | Stated in the catalogue (`edition-struct.json`) and by its publisher. |

A Gilyon collection contains no text of any edition, so the edition's
licence does not restrict the distribution of the collection. It does govern
what an application may do with the edition's text. The licence of an
alignment is a fourth matter, stated by whoever publishes it.

## Two catalogues

| | `bcv-commons/bibles` | `bcv-commons/gilyon` |
|---|---|---|
| Lists | Bible editions: text and audio | Annotation collections published in Gilyon (planned) |
| Keyed by | Language and source identifier | Collection IRI |
| Points at | Where the text is, and how to read it | Where the publisher hosts the collection |

The two are joined by the base text, not by entries that refer to each
other. An annotation collection applies to every edition that has an
alignment. A catalogue entry for a collection may state the edition its
notes were first written on, as information for readers.

## What does not exist yet

- A published reference implementation of the five steps above.
- A statement, per edition in the catalogue, of whether an alignment
  suitable for Gilyon anchors is available.
- The Gilyon catalogue itself (`docs/open-issues.md` §21).
