# Code examples

Small, runnable scripts that read Gilyon collections and show their
annotations in a Bible translation. Each exists in Python and in JavaScript
and gives the same output. Nothing needs to be installed: Python uses the
standard library, JavaScript the built-in `fetch()` (Node 20 or later, or a
browser).

They continue the examples of
[bcv-commons/bibles](https://github.com/bcv-commons/bibles/tree/main/doc/examples),
which show how to read the text of a Bible edition. These add the
annotations.

```
cd python                      # or: cd js
python3 show_in_edition.py JOS 1          # node show_in_edition.mjs JOS 1
```

| Script | What it does |
|---|---|
| `list_collections` | Lists the collections in the Gilyon catalogue, all of them or those readable in one language. |
| `fetch_chapter` | Fetches the annotations of one chapter of a collection: the manifest, then only the files for that chapter, each checked against its SHA-256. |
| `show_in_edition` | Shows a chapter of a translation with the annotations placed in its text. |
| `gilyon.py`, `gilyon.mjs` | The shared reader the three scripts use: catalogue, manifest (also in parts), choosing files by their coverage, joining the wording to the anchors. About 150 lines. |

## Annotations in a translation

A Gilyon annotation points at Hebrew or Greek words, not at a translation.
`show_in_edition` puts it into a translation with three things it fetches
when asked, none of which is in the Gilyon collection:

| Step | From |
|---|---|
| The chapter's text | [helloAO](https://bible.helloao.org), read with the verse-text tools of bcv-commons/bibles |
| Which word of the translation renders which Hebrew or Greek word | [bcv-commons/compact-alignments](https://huggingface.co/datasets/bcv-commons/compact-alignments) (CC0) |
| The annotations for the chapter | The Gilyon collection |

```
$ python3 show_in_edition.py JOS 1
JOS 1 in BSB, with: The Swedish Core Bible: anchors of the notes on Joshua
Alignment: bcv-commons/compact-alignments (eng_BSB); text fingerprint da348 matches the aligned text

  1 Now after the death of His servant⁽¹⁾ Moses, the LORD spoke to Joshua son of Nun, …
```

The same notes in a French Bible, with no change to the collection:

```
python3 show_in_edition.py JOS 1 --helloao fra_lsg --alignment fra_lsg --iso fra --scheme orgw
  1 Après la mort de Moïse, serviteur⁽¹⁾ de l’Éternel, l’Éternel dit à Josué, …
```

A collection that has its wording, in the language asked for:

```
python3 show_in_edition.py GEN 1 --language en \
    --collection https://gilyon.org/0.1/examples/collection-parts/manifest.json
```

The Joshua collection is published as anchors only, so its notes appear as
marks without wording.

### What the script takes care of

- **The alignment must fit the text.** An alignment names words by their
  position in a verse, so it is only valid for the exact wording it was made
  on. The script computes the fingerprint of the chapter it fetched and uses
  the alignment only when the two agree. Otherwise every note is shown at
  the end of its verse.
- **Only the needed files are fetched.** The manifest says which chapters
  each file covers (specification §16.5).
- **Verse numbering.** Annotations use the numbering of the Hebrew and Greek
  text. Where a translation numbers verses differently, the verse map of its
  scheme (`--scheme`) is applied.
- **A note with no exact place** falls back to its verse: when its anchor
  words are not aligned in this translation, or come in an order that leaves
  no place between them.

### What it does not do

- It reads translations from helloAO only. The catalogue of bcv-commons/bibles
  describes other routes.
- The four options that describe a translation (`--helloao`, `--alignment`,
  `--iso`, `--scheme`) are typed by hand. They are in the `manifest.json` of
  compact-alignments; the script does not look them up.
- It uses the content-word alignment. An anchor on a function word (an
  article, a preposition) is placed by the nearest content word.
- Structures (a chiasm, an outline) are not drawn, and a `Lexeme` note is
  listed under the chapter, not marked at each occurrence.
- Psalms from helloAO have their titles inside verse 1, so their fingerprint
  does not match and their notes fall back to the verse.

## Licence

The scripts are under the MIT licence, like `tools/`. The files in
`python/verse_text/` and `js/verse_text/` are unchanged copies from
bcv-commons/bibles, version 2.0.0, CC0 1.0. The annotations, the translations
and the alignments each keep their own licence; the scripts print the
licence of the collection they show.
