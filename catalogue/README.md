# The catalogue's source

People register **publishers**. What each publisher provides is read from
the publisher's own manifests; nobody lists collections here by hand.

| Path | Holds | Written by |
|---|---|---|
| `config.json` | The catalogue's `id` and `title`, and `admins`: GitHub accounts of the catalogue admins | Admins |
| `publishers/<name>.json` | One publisher: its name, its maintainers, and where its manifests are | Its maintainers; admins |
| `state/<name>.json` | What was found at those addresses, with the result of the checks | `tools/build_catalogue.py discover` |

The published catalogue (`https://gilyon.org/collections/…`) is built from
`publishers/` and `state/` by `tools/build_catalogue.py build`.

## A publisher file

```json
{
  "name": "Example Publisher",
  "id": "https://publisher.example/",
  "added": "2026-11-27",
  "maintainers": [
    { "github": "<account>", "role": "publisher", "since": "2026-11-27" }
  ],
  "sources": [
    { "type": "manifests",
      "manifests": [
        "https://publisher.example/notes/manifest.json"
      ] }
  ]
}
```

- **`maintainers`**: at least one person with a GitHub account who answers
  for this publisher's listings. Use `"role": "delegate"` and `delegation`
  (the address of the publisher's written statement) for someone who acts for
  a publisher they do not belong to.
- **`sources`**: where the manifests are. A manifest of a collection (spec
  §16.1) and a manifest of a translation (§16.3) are listed the same way. A
  translator is a publisher like any other.
- A source of `"type": "github"` (`owner`, `topic`) is reserved for finding
  repositories by topic. It is not implemented yet.
- `"hosting": "republished"` on a source marks copies hosted by the
  catalogue's operator.
- File names: lower-case letters, digits, `-` and `_`. A file name does not
  change once the publisher is registered.

A maintainer adds or removes addresses in `sources` by pull request and
needs nobody's approval for the content of that list. Registering a
publisher, and changing its name or maintainers, needs a catalogue admin
(`docs/catalogue.md`).

## Commands

```
uv run --with jsonschema tools/build_catalogue.py discover          # read and check the manifests
uv run --with jsonschema tools/build_catalogue.py build --out DIR   # the published files
uv run --with jsonschema tools/build_catalogue.py codeowners --out .github/CODEOWNERS
```
