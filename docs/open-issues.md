# Open issues

What Working Draft 0.1 decides provisionally or leaves open. Each point has a
recommendation where there is one. Comments are welcome as issues on the
repository.

Sections 1 to 12 keep their numbers, because the specification refers to
some of them.

## 1. Name

The standard is called **Gilyon** (גִּלָּיוֹן, "margin; marginal note").

Checked 2026-11-27: no Bible software, standard or company of this name was
found, and the package name `gilyon` is free on PyPI, npm, crates.io and
RubyGems. Trademark registers were not searched.

## 2. Greek base text

The draft makes Nestle 1904 (MACULA) the default and registers SBLGNT as an
alternative.

*Recommendation:* keep Nestle 1904 as the single default (public-domain
text, CC BY identifiers), and publish the N1904↔SBLGNT word map as a
registered mapping. NA28 cannot be a default: it is under copyright.

## 3. Canonical spelling of word identifiers

The draft requires the MACULA form with its prefix (`o…`, `n…`). Several
systems store the bare digits, and the `BCVWP` scheme of the Scripture
Burrito alignment format has no prefix either.

*Recommendation:* keep the prefix (it is the upstream identifier, and it
separates the Hebrew and Greek spaces); Consumers accept bare digits on
input.

## 4. Identifier stability across MACULA releases

Gilyon depends on word identifiers that MACULA does not formally promise to
keep. Not established at the time of writing: which version of the
Westminster Leningrad Codex underlies MACULA Hebrew, and how ketiv/qere pairs
are identified. The stability policies in `registries/base-texts.json` are
placeholders.

*Needed:* a stability statement and migration maps from the maintainers, or a
pinned mirror with frozen identifiers. Without one of these, version 1.0
should not be declared.

## 5. Texts outside the 66 books; the Septuagint

No open word-identifier dataset of the MACULA kind was found for the
Septuagint or the deuterocanonical books. In 0.1 they can be annotated only
with `Passage` selectors.

## 6. Textual variants

A textual note is body text in 0.1. A structured form (readings, witnesses by
Gregory-Aland number, relation to the base text) is deferred.

## 7. Figure-of-speech taxonomy

`registries/categories.json` has a short starter list. A full classification
could be built from Bullinger's *Figures of Speech Used in the Bible* (1898,
public domain). No open machine-readable taxonomy of it was found. This is a
content project in its own right; the format only needs the prefix
mechanism.

## 8. Permanent addresses

The namespace is `https://gilyon.org/`. The draft assigns these addresses,
and `tools/build_site.py` lays the files out at them:

| Address | Content |
|---|---|
| `https://gilyon.org/0.1/` | The specification (`/0.1/spec.md` as written) |
| `https://gilyon.org/0.1/schema.json` | Document schema |
| `https://gilyon.org/0.1/manifest.schema.json` | Manifest schema |
| `https://gilyon.org/0.1/bodies.schema.json` | Body-document schema |
| `https://gilyon.org/0.1/catalogue.schema.json` | Catalogue schema |
| `https://gilyon.org/collections/index.json` | The catalogue: its index. Slices are under `lang/`, `publisher/` and `c/` |
| `https://gilyon.org/0.1/context.jsonld` | JSON-LD context |
| `https://gilyon.org/0.1/examples/…` | The examples |
| `https://gilyon.org/registries/<name>.json` | The registries |
| `https://gilyon.org/ns#` | Vocabulary namespace of Gilyon's own terms |
| `https://gilyon.org/collections/` | The catalogue |

Addresses under `/0.1/` belong to this version. The registries are not
versioned by address: entries are added and deprecated, never removed
(§17.3). Whether the site is live is not stated here; check the address.

*Still to decide:* a commitment that the content at a versioned address
never changes once a version is final. Before 1.0 the files under `/0.1/`
change with the draft.

The JSON-LD context is a first draft. The three examples expand to RDF with
it (tested with one processor, PyLD). Its known limits:

- An annotation has no `type` member, so the context alone does not state
  that it is an `oa:Annotation`.
- `target.text` is a local name and stays a string. The mapping to
  `oa:hasSource` with the IRI of the base-text edition (Appendix D) needs
  IRIs for editions, which the registry does not assign yet.
- Category terms, entity identifiers, word identifiers and lexeme
  identifiers stay strings; they are not yet IRIs.
- `check` and `lexemes` are carried as JSON literals.

## 9. Scripture Burrito flavor

The Scripture Burrito specification reserves the flavor types
`parascriptural` and `peripheral` without defining a notes flavor.

*Recommendation:* propose an annotations flavor once two implementations
exist.

## 10. Aramaic

Gilyon allows the prefix `arc:` for Aramaic lexemes beside `hbo:` for Hebrew.
Existing lexeme inventories often tag the whole Hebrew Bible as Hebrew.

*Needed:* a list of which lexeme identifiers are Aramaic, or a decision to
keep one prefix for the whole Hebrew Bible.

## 11. Sub-word anchors in Greek, and characters

Hebrew identifiers reach prefixes and suffixes. Greek identifiers stop at the
word (a crasis form is one word). Character-level anchors are not in 0.1.

## 12. Clause- and phrase-level targets

Gilyon 0.1 expresses a clause as a `Range`. A `Clause` selector would need a
pinned clause layout; deferred.

## 13. Original languages only (decided)

Gilyon links exclusively to Hebrew, Aramaic and Greek words. A document holds
no position in a translation (spec §1.4). Earlier drafts had selectors for
translation tokens and quoted text, a record of the place where a note
originally stood, alignment declarations and a projection algorithm. All were
removed on 2026-11-27.

Consequences to be aware of:

- A wrong derived anchor cannot be corrected from the document alone. The
  party that derives anchors checks them against the translation before
  publishing.
- An application that only knows a place in a translation (a highlight made
  in a reading app) must find the original-language words before it can
  export to Gilyon.

## 14. Gaps that hold only function words

A method that anchors between content words produces points whose `after` and
`before` are separated by an article or a preposition. In the sense of §7.5
these are gaps, although the position is known as well as it can be. In a
first conversion of 292 notes on Joshua, 16 of 163 two-sided points were
exact.

*To decide:* whether §7.5 should distinguish a gap that holds only function
words.

## 15. Method-specific evidence

`anchoring.detail` is one string. A method may report more: which words it
skipped and why, or a second candidate. Today this goes into an `x-` member.

*To decide:* a registered, method-specific `evidence` member, once two
implementations exchange one (§17.2).

## 16. Pinning a base text between releases

A tool chain may be built from a state of a MACULA dataset that lies between
two tagged releases. §5.2 rule 5 says that `revision` then governs and that
`release` names the latest release the revision contains. The validator
cannot check this.

## 17. Versification of references inside a note

A Scripture reference written in a note follows the numbering of the edition
the note was written for. A converter must know that numbering to produce
correct `links`. Where it is assumed and not verified, the collection's
description should say so.

## 18. A file of a split collection cannot name its collection

Each file is a complete document with its own `id`; only the manifest says
that the files belong together.

*To decide:* an optional `meta.partOf` holding the collection's `id`,
following the collection-and-page pattern of the W3C Web Annotation model.
The header (`meta`, `texts`) is repeated in every file, which is noticeable
for small chapters.

## 19. Note identity in the source

Many publications give their notes no identifier. A converter then has to
make one, and the obvious scheme (book, chapter, verse, ordinal within the
verse) breaks when a later edition inserts or removes a note: identifiers
would be reused for different notes, which §14.2 forbids.

*Needed:* guidance on matching notes across editions by their text, or a
recommendation that publishers assign note identifiers at the source.

## 20. Bodies by language: what is not settled

Version 0.1 keeps the wording in body documents per language (§16.2) and
records the state of each translation (§9.1). Open points:

- **Folder names are not checked against ISO 639-3.** The validator checks
  the form of a folder name, not that `swe` is the code for `sv`. A table of
  codes would be needed.
- **Macrolanguages.** For Chinese, Arabic, Norwegian and others there is a
  macrolanguage code and codes for individual languages. Which one names the
  folder is left to the publisher. *Recommendation:* follow the choice of the
  `bcv-commons/bibles` catalogue for the same language.
- **Comments on relations** of a structure have no address in a body
  document (§16.2 rule 7).
- **Language maps elsewhere.** Titles and link labels stay language maps in
  the annotation document and the manifest. They are short; whether they
  should move to the language folders is open.
- **Partial review.** `languages.<tag>.translation.status` in the manifest is
  a summary (`mixed` when bodies differ). A count per status would tell a
  reader more.
- **Who may review.** "Competent in both languages" is not defined, and the
  format does not record more than one reviewer.
- **The JSON-LD context** does not cover body documents.

## 21. The catalogue

The format is in the draft (§16.4): an index and slices by language,
publisher and collection, with translations published by other parties
listed under the collection they translate (§16.3). The catalogue is kept as
one file per registered publisher, and its entries are read from the
publishers' manifests. The process is proposed in `docs/catalogue.md`. Open:

- The checks have run against local test servers only. The check that word
  identifiers exist in the pinned release is not implemented.
- The cross-origin check covers the manifest, not every file.
- A collection whose manifest was never reachable has no entry, since its
  identifier is unknown; it appears only in the publisher's state file.
- Who the catalogue admins are, and proof that a delegate acts for a
  publisher (`docs/catalogue.md`).
- The ownership check and the workflows have not run on GitHub yet.
- Whether a third-party translation is listed without the consent of the
  collection's publisher.
- Whether `gilyon.org` should host collections for publishers without a
  server, and what that obliges the operator to do.
- A body document does not record which state of the annotation document it
  was written against. Stale wording is detected per body; a removed
  annotation is only noticed as an entry that matches nothing.

## 22. Not yet verified

- The status of the USFM Scripture Referencing Standard: its file says 1.0,
  its roadmap says "In Discussion".
- Whether a JSON Schema release newer than 2020-12 is final.
- The examples and the specification have not been reviewed outside the
  bcv-commons team.
