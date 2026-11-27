# Governance (proposal)

This file is a proposal by the bcv-commons team. None of it is in force
until the parties who would be bound by it agree.

## Stage 1 — Draft (now)

- The specification lives in a public Git repository. Text is CC BY 4.0.
- Changes are made by pull request. Every normative change updates the
  schema, the examples and the changelog in the same pull request.
- The examples are the test suite: every example must validate, and every
  normative rule that a document can violate should have a failing test case.

## Stage 2 — Working group (when two organisations beyond the authors implement)

- A named working group of implementers, with one editor.
- Decisions by consensus; failing that, a two-thirds vote of member
  organisations, one vote each.
- Registry entries: added by pull request with a public description and a
  licence statement; never removed, only deprecated.
- A private extension (`x-…`) that two independent implementations exchange is
  a candidate for the next minor version.
- Version 1.0 is declared when at least two independent Producers and two
  independent Consumers interoperate on the examples and on one real
  collection of at least a whole book.

## Stage 3 — Neutral home

Options, in the order they become worthwhile:

1. A W3C Community Group (no fee; needs five supporters). Fits because Gilyon is
   a profile of the W3C Web Annotation model.
2. A Scripture Burrito flavor for annotations, proposed to the Scripture
   Burrito Committee, so that Gilyon collections travel with Scripture packages.
3. Liaison with the USFM/USX Technical Committee, whose referencing standard
   Gilyon already follows and whose draft "Linkages" file is complementary.

## Whose work Gilyon touches

None of these organisations has been approached yet, and none has endorsed
Gilyon. The table says why each would be asked.

| Party | Why |
|---|---|
| Clear Bible / Biblica | Maintain MACULA: the identifier-stability policy Gilyon depends on is theirs to give. |
| USFM/USX Technical Committee | Referencing standard and Linkages draft. |
| Scripture Burrito Committee | Packaging; alignment format. |
| Mission Mutual / BiblioNexus (Bible Aquifer, ACAI) | Large open note corpus; forthcoming linking specification. |
| unfoldingWord | Largest existing original-language-anchored note corpus. |
| SIL and UBS (Paratext, Platform.Bible) | Installed base of translation notes. |
| Tyndale House / STEPBible | Versification data, name identifiers, lexical identifiers. |
| ETEN Innovation Lab | Funder and convenor of several of the above. |
