# Gilyon vocabulary

Namespace: `https://gilyon.org/ns#`

This is the namespace of the terms Gilyon adds to the W3C Web Annotation
vocabulary. It is used by the JSON-LD context at
[`/0.1/context.jsonld`](../context/gilyon-0.1.context.jsonld). A plain-JSON
implementation never needs it.

**Status: draft.** The terms are defined by the
[specification](../spec/gilyon-0.1.md); this page only lists them. The list
and the IRIs may change before version 1.0.

## Classes

| Term | Defined in |
|---|---|
| `Passage`, `Words`, `Range`, `Point`, `Lexeme`, `Composite` | Selector types, §7 |

## Values

| Term | Defined in |
|---|---|
| `authored`, `reviewed`, `derived`, `unresolved` | Anchoring status, §8.2 |
| `draft`, `review`, `approved`, `withdrawn` | Document and annotation status, §4.3 |
| `crossReference`, `quotes`, `quotedBy`, `alludesTo`, `parallel`, `denotes`, `speaker`, `addressee`, `about`, `citation` | Link relations, §11.1 |

## Properties

| Term | Member | Defined in |
|---|---|---|
| `formatVersion`, `level` | `gilyon`, `conformsTo` | §4.2 |
| `declaresText`, `localName` | `texts` and its keys | §5 |
| `annotation` | `annotations` | §6 |
| `text`, `ref`, `words`, `first`, `last`, `after`, `before`, `lexeme`, `sense`, `items`, `check`, `lexemes`, `fallback` | the same names | §7 |
| `annotationTarget` | `target.annotation` | §11.3 |
| `anchoring`, `method`, `confidence`, `tier`, `detail`, `reviewer`, `date` | the same names | §8 |
| `category`, `sequence`, `presentation`, `supersedes`, `attribution` | the same names | §6, §10 |
| `links`, `rel`, `entity`, `url`, `label` | the same names | §11 |
| `structure`, `unit`, `unitId`, `relation`, `relationType`, `relatedUnit`, `focus`, `notation`, `key`, `level`, `parent` | `structure` and its members | §12 |

Members that the context maps to existing vocabularies (`motivation`, `body`,
`target`, `selector`, `value`, `title`, `creator`, `created`, `license` and
others) are not listed here.
