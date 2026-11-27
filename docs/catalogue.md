# The catalogue: publishers, listing and verification

How collections and translations get into the Gilyon catalogue, how the
catalogue stays small enough to use, and what it verifies. The published
format is in the specification (§16.4). The process on this page is a
proposal. One publisher is registered so far: the bcv-commons team itself,
with one collection hosted on this site.

## The idea

People register **publishers**. Collections and translations are not listed
by hand: the catalogue reads them from the manifests each publisher names,
checks them, and publishes the result in slices.

```
catalogue/publishers/<name>.json     who answers for the publisher, and where its manifests are
            │  read and checked by a job
            ▼
catalogue/state/<name>.json          what was found, with the result of the checks
            │  built
            ▼
gilyon.org/collections/index.json            languages and publishers, with counts
gilyon.org/collections/lang/<folder>.json    what can be read in one language
gilyon.org/collections/publisher/<name>.json what one publisher provides
gilyon.org/collections/c/<key>.json          one collection with all its translations
```

The catalogue holds no annotations and no note text. Collections stay on
their publishers' servers. A copy is hosted on `gilyon.org` only when a
collection cannot be reached otherwise, and it is then marked
`"hosting": "republished"`.

## Why it is built this way

| What grows | How it is kept small |
|---|---|
| What an application downloads | An application fetches the index and the slice of its language. It never downloads the whole catalogue. |
| What people edit here | One file per publisher. A publisher that adds a collection or a language publishes it and, at most, adds one address to its own file. |
| Check results | Kept in generated files, apart from the files people edit, so a daily re-check never collides with a person's change. |
| Review work for the catalogue's admins | Registration of a publisher is reviewed once. After that the automated checks are the gate. |

A translator is a publisher like any other. A language community can keep
all its translations, of many collections, in one place and register that
place once.

## What an application fetches

1. `collections/index.json`: the list of languages and publishers.
2. `collections/lang/<folder>.json` for its language: every collection that
   can be read in that language, either because the collection provides it or
   because a listed translation does.
3. The manifests named there, from the publishers' servers.

An application that already holds a collection and wants its other languages
computes the collection's key (the first 16 hexadecimal digits of the
SHA-256 of its `id`) and fetches `collections/c/<key>.json`.

## Who publishes what

| Party | Publishes, on its own server | Needs from the other |
|---|---|---|
| The publisher of a collection | Annotation documents, the wording in the source language, a manifest | Nothing |
| A translator | Body documents in the new language, a translation manifest naming the collection | A licence that permits translation; nothing else |
| The catalogue | The slices, with the result of its checks | A registered publisher and the address of the manifest |

The publisher of a collection does not have to know about a translation. The
reading application finds it through the catalogue.

## Every publisher has a named maintainer

A collection may be hosted anywhere, but its publisher is registered in the
Gilyon repository on GitHub, and every publisher file must name at least one
**maintainer** with a GitHub account. This is a rule of the Gilyon
catalogue, not of the format.

| | |
|---|---|
| **Who** | A member of the publishing organisation, or a delegate the organisation has asked to act for it. A delegate is listed with `"role": "delegate"`. |
| **What they answer for** | The publisher's listings: that the addresses are right and are the publisher's own, and that someone replies when a check fails or a complaint arrives. |
| **What they can do** | Add and remove manifest addresses in their publisher file, and withdraw the publisher. |
| **What they do not answer for** | The content of the collections. That stays with the publisher. |

An organisation that does not use GitHub for its content still needs this
one person. The delegation is stated by the publisher in writing, so that
the catalogue can show who acts for whom.

If no maintainer responds to a failed check within the period the catalogue
sets, the listing is flagged, and later withdrawn. A publisher can replace
its maintainer at any time.

### How this is enforced

Two mechanisms use the `maintainers` of each publisher file:

- **An ownership check on every pull request** that touches `catalogue/`
  (`tools/build_catalogue.py owner-check`, run by the `catalogue-owner`
  workflow). It reads the maintainers from the main branch, not from the
  proposed change, so nobody can add themselves and approve it.
- **A generated `CODEOWNERS` file**, which asks the maintainers and the
  catalogue admins for review.

| A pull request that | From a maintainer of that publisher | From anyone else |
|---|---|---|
| Adds or removes manifest addresses in `sources` | Allowed | Refused |
| Sets the publisher to `withdrawn` | Allowed | Refused |
| Changes the name, the `id` or the maintainers | Needs a catalogue admin | Refused |
| Registers a new publisher | Needs a catalogue admin | Needs a catalogue admin |
| Deletes a publisher file | Needs a catalogue admin | Refused |
| Changes `state/` or `config.json` | Refused: the catalogue writes these | Refused |

Catalogue admins are listed in `catalogue/config.json`. They may change any
file.

GitHub only honours a code owner who has write access to the repository, and
outside maintainers will not have it. The ownership check is therefore the
rule that counts, and the repository's branch protection must require it to
pass, with an admin's approval for merging. `CODEOWNERS` is a convenience on
top. This reading of GitHub's behaviour should be confirmed when the
repository is set up.

## Getting listed

1. **Publish** the files at a stable `https` address that allows
   cross-origin requests.
2. **Validate** them: `tools/validate.py <manifest>`.
3. **Register as a publisher**, once: a pull request that adds
   `catalogue/publishers/<name>.json` with the maintainers and the manifest
   addresses (`catalogue/README.md`). A catalogue admin reviews it.
4. **Later collections, languages and translations**: the maintainer adds
   the address to the publisher file. Nothing else is needed.
5. **The discovery job** reads the manifests, runs the checks and writes the
   state. The slices are rebuilt at the next site build.

## What is verified

Every claim a manifest makes falls into one of four groups. The catalogue is
explicit about which group a claim is in.

### 1. Checked by machine, every time

| Check | Name in `checked.checks` | State |
|---|---|---|
| The manifest and every file it lists can be fetched | `reachable` | Built |
| The server allows cross-origin requests | `cors` | Built, for the manifest |
| Every file has the SHA-256 the manifest states | `checksums` | Built |
| Every file is valid Gilyon, and the cross-file rules hold | `valid` | Built |
| A translation names its collection, and its bodies fit the collection's annotations | `translation` | Built |
| How many translated bodies are stale; how many are machine-made, reviewed, human | `checked.stale`, `checked.bodies` | Built |
| Every word identifier exists in the pinned release of the base text | `words` | Not built |
| `check` values match the base text | `surface` | Not built |

What an entry says about a collection (its identifier, licence, languages,
books) is read from the manifest. Nobody types it, so it cannot disagree
with the manifest.

The checks were tried against local test servers: a valid collection, a
valid translation, a server without cross-origin access, an invalid
collection and a missing manifest each gave the expected result. They have
not run against a real publisher.

### 2. Checked by machine, as far as a rule can go

- **Machine-made content is marked.** A `machine` translation must name a
  software creator. Built.
- **Licence compatibility.** A translation of bodies under a no-derivatives
  licence is to be refused; a translation of share-alike bodies must carry
  the same licence. Not built.

### 3. Tied to who is asking

- **A named maintainer** for every publisher (above).
- **Control of the address.** A publisher is registered only when its
  maintainer shows that the publisher stands behind it. For content hosted
  on GitHub that is the ownership of the repository. For content hosted
  elsewhere it is the publisher's written delegation, and where needed a
  file on the publisher's server that names the registration.
- **Publisher or third party.** A translation is marked
  `"by": "publisher"` only when the same registered publisher provides the
  collection. Otherwise it is `"third-party"`, and applications are required
  to let users tell the two apart (§16.3 rule 5).

### 4. Not verified: the publisher's own claims

- That an anchor is `authored` or `reviewed`.
- That a translation is `reviewed` or `human`, and that the reviewer knows
  both languages. When the translation is kept in a repository whose history
  shows who merged each reviewed body, the catalogue can mark the entry
  `"evidence": "recorded"`; otherwise it is `"claimed"`.
- That the publisher holds the rights to the content.
- That a note is accurate.

The catalogue records these as claims and does not vouch for them. A listing
never means endorsement of the content (§16.4 rule 2).

## After listing

- **Re-checks.** The discovery job runs again on a schedule and proposes the
  new state as a pull request.
- **A failing check** sets the entry to `"flagged"`, with the date it began
  and the reason. The entry stays visible. It is not removed silently.
- **A changed manifest** is normal: publishers correct notes. The entry is
  re-read, and translations of the changed notes show up as stale.
- **Withdrawal.** A collection that is gone keeps its entry with `status`
  `"withdrawn"`.
- **Complaints** about rights or content are handled by a catalogue admin,
  who can flag or withdraw.

## What a hosted publishing service would add

For a publisher without a server, a service could accept an upload, run the
same checks and host the files under `gilyon.org`. That is the
`"republished"` case. It brings obligations the pointer model does not have:
accounts, storage, takedown handling, and responsibility for content hosted
under the Gilyon name. The proposal is to start with registered publishers
and pointers, and to add hosting when a publisher needs it.

## Not decided

- Who the catalogue admins are, and how a decision is appealed
  (`GOVERNANCE.md`).
- How a publisher that hosts outside GitHub proves that the named
  maintainer acts for it, beyond a written statement.
- The response period before a listing is flagged, and before it is
  withdrawn.
- Whether a third-party translation is listed without the consent of the
  collection's publisher. The licence may permit the translation; listing it
  is a separate choice.
- Whether a language slice needs a further split, by Bible book, once a
  language has very many collections.
- Finding a publisher's repositories by topic, as an alternative to a list
  of addresses. The publisher file reserves a source type for it.
