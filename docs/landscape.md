# Landscape: what exists and how Gilyon relates to it

Researched 2026-11-27. Statements about other standards reflect their
published state on that date. Corrections are welcome.

## The gap

No existing format carries note, commentary, highlight or
rhetorical-structure content anchored to original-language word identifiers.
The pieces around that gap exist and Gilyon reuses them.

| What exists | Anchored to | Limitation |
|---|---|---|
| Study notes in circulation (Bible Aquifer, Tyndale, USFM `\ef`) | verse ranges | Not word-exact. |
| unfoldingWord Translation Notes | original-language quote + occurrence number | A string, not a stable identifier; breaks under normalisation and edition differences. |
| ACAI | MACULA word identifiers | Entities, referents and speeches only. |
| USFM TC Linkages draft | word positions in one translation | No content, no original-language anchor. |
| App notes and highlights (Logos, YouVersion) | proprietary | No open export format found. |

## Closest existing work

| Work | Maintainer, status | What it is | Gilyon's relation |
|---|---|---|---|
| **W3C Web Annotation Data Model** | W3C Recommendation, 2017; group closed, stable | Generic annotation model: body, target, selector, motivation | Gilyon is shaped as a profile and adds word-identifier selectors. Its licence forbids derivative specifications, so Gilyon cites it and does not copy its text. |
| **MACULA Hebrew / Greek** | Clear Bible / Biblica, CC BY 4.0 | Open word identifiers: `o010010010011` (Hebrew, 12 digits with a morpheme part), `n40001001001` (Greek, 11 digits) | Gilyon's default base texts. |
| **Scripture Burrito Alignment Format 0.4** | J. Tauber, 2024 | Alignment exchange: `scheme` / `docid` / selectors; registers a `BCVWP` scheme | Not used by Gilyon; a format applications can use to show annotations on a translation. |
| **USFM Scripture Referencing Standard ("U23003")** | USFM Technical Committee, v1.0 in the file, "In Discussion" in the roadmap | `MAT 2:1!3` = third word of the verse in a translation | Gilyon's reference syntax is its verse-level subset; its word-level references address a translation, which Gilyon does not. |
| **USFM TC Linkages File ("U25005")** | draft | Stand-off JSON pointing from a translation to external data | Complementary. The nearest thing to a competitor. |
| **Scripture Burrito 1.0** | Scripture Burrito Committee | Packaging; `parascriptural` and `peripheral` reserved, no notes flavor | An annotations flavor is an open slot. |
| **unfoldingWord Translation Notes** | unfoldingWord, CC BY-SA 4.0 | TSV: `Reference ID Tags SupportReference Quote Occurrence Note` | Convertible to Gilyon; largest existing corpus. |
| **Bible Aquifer** | Mission Mutual / BiblioNexus | Open notes and dictionaries in JSON; a "Linking Specification" is announced | Potential adopter or parallel inventor. |
| **STAM** | Stand-off Text Annotation Model | Modern general stand-off model with composite selectors and annotations on annotations | Closest general analogue; informed the structure layer. |
| **TEI, CTS URN, ISO LAF, NIF, CoNLL-U** | various | Scholarly and linguistic annotation | Informative mappings only. CTS URNs identify a word by its spelling plus an occurrence count and define no normalisation, so they cannot serve as word identifiers. |
| **OSIS** | no release since 2.1.1 (2006) | XML Bible markup | Legacy; its reference style can be accepted on input. |

## Lessons taken into the design

1. **Identifiers, not offsets or quoted strings.** Every offset-based system
   surveyed needs a frozen, identically normalised text. Unicode normalisation
   reorders Hebrew marks and irreversibly merges some Greek accents. Gilyon
   therefore selects by identifier and keeps the surface form only as a check.
2. **Word identifiers are edition-relative.** Nestle 1904 and SBLGNT both begin
   at `n40001001001`; the same string can mean different words. The identifier
   appears in at least five spellings in the wild (with or without prefix, 11
   or 12 digits, with or without an appended surface form). Gilyon fixes one
   spelling and always pairs it with an edition.
3. **Licences constrain the anchor.** BHSA is CC BY-NC and NA28 is under
   copyright; neither can be a normative base text.
4. **Structures need more than the W3C model.** Units, relations between
   units, nesting and a centre come from the graph models (LAF, Text-Fabric,
   STAM).
5. **How small standards succeed.** Public repository, CC BY text, examples
   as test suite, extension prefix with promotion after two implementations,
   registries as versioned files (the pattern of IIIF, CommonMark, Data
   Package and Scripture Burrito).

## Reusable vocabularies and data

| Need | Source |
|---|---|
| Versification | Paratext `.vrs` (`eng`, `org`, `lxx`, `vul`, `rsc`, `rso`); Copenhagen Alliance JSON; Tyndale TVTMS (CC BY 4.0) |
| Persons, places | ACAI (CC BY-SA 4.0), TIPNR (CC BY 4.0), OpenBible.info geocoding (CC BY 4.0), Theographic |
| Lexical identity | Strong's; STEPBible disambiguated Strong's; UBS dictionaries (CC BY-SA 4.0) |
| Figures of speech | unfoldingWord `figs-*` tags are the only open tag set found. Bullinger's book is public domain, but the only machine-readable dataset found is a commercial product. |
| Chiasms | No open hand-curated corpus found. |
