# Roadmap: what is built, and what the design leaves room for

The features planned around the format, with their state on 2026-11-27.
"Accommodated" means the format or the catalogue already has the members a
feature needs, so that adding it later changes no published file.

## Built

| Feature | Where |
|---|---|
| Annotation documents, selectors, anchoring, structures | spec §4–§12; `tools/validate.py` |
| Wording per language, apart from the anchors | spec §16.2; `examples/collection/` |
| Translation status and stale detection | spec §9.1; validator warnings |
| Translations published by another party | spec §16.3; `examples/translation-elsewhere/` |
| Catalogue format: an index and slices by language, publisher and collection | spec §16.4; `examples/catalogue/published/` |
| Catalogue kept as one file per publisher, with maintainers; entries read from the publishers' manifests | `catalogue/`, `tools/build_catalogue.py discover` and `build` |
| Checks on collections hosted elsewhere: fetching, checksums, validity, cross-origin access, stale and status counts | `tools/build_catalogue.py discover` (tried against local test servers only) |
| Ownership check on catalogue pull requests, generated `CODEOWNERS` | `.github/workflows/catalogue-owner.yml` |
| Validation in CI | `.github/workflows/validate.yml` |
| Site with every file at its permanent address | `tools/build_site.py` |

The workflows have not run on GitHub yet: the repository is not published.

## Accommodated, not built

| Feature | What it needs | Already in the design |
|---|---|---|
| Scheduled re-checks | Enabling the schedule in `.github/workflows/catalogue-discover.yml`; deciding the response periods | The workflow exists and runs by hand; `flag.since` is kept across runs |
| Licence compatibility of translations | A rule table over SPDX identifiers | `license` on both manifests |
| A further split of a language slice by Bible book | A fourth kind of slice | `books` on every entry; `slice.by` is an open list |
| Word identifiers verified against the base text | The pinned MACULA release at hand in CI | `texts` pins `edition`, `release`, `revision`; check names `words`, `surface` |
| Collections and translations kept in GitHub repositories | A template repository with the validator as its CI | `repository` on an entry; `checked.revision` |
| Review of translations with a record | A review workflow in which a reviewer's merge sets `reviewed` (the model of an existing bcv-commons review application) | `translation.reviewer` and `date` per body; `translation.evidence`: `recorded` or `claimed` on the entry |
| A translation pinned to a state of the collection | The translator's tool recording the manifest's checksum | `ofSha256` in a translation manifest |
| Discovery of a publisher's repositories by topic | A call to the hosting service's API in `discover` | Source type `github` (`owner`, `topic`) in a publisher file |
| Proof that a delegate acts for a publisher | A statement by the publisher, and a place to keep it | `maintainers[].role`, `maintainers[].delegation` in a publisher file |
| Hosting for publishers without a server | Storage, accounts and takedown handling | `hosting`: `republished` on a source |
| Notes of a translation project exported as a collection | An exporter that turns notes anchored in a translation into original-language anchors through that project's alignment | `anchoring.status` `derived` with `method`; nothing of the translation is written |
| An editor for translating and reviewing notes | An application over the body documents of one language | Body documents are small, one per chapter and language; a review changes one body and its `translation` record |
| JSON-LD for body documents, manifests and catalogues | Context terms | The context covers annotation documents only |

## Decisions these features wait for

- Who the catalogue admins are (`catalogue/config.json` is empty).
- Where collection repositories live when publishers use GitHub.
- Whether a third-party translation is listed without the publisher's
  consent.
- The response periods before an entry is flagged and withdrawn.
- A stability statement for MACULA word identifiers
  (`docs/open-issues.md` §4), which the base-text check depends on.
