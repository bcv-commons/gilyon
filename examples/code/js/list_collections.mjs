#!/usr/bin/env node
// List the annotation collections in the Gilyon catalogue.
// No dependencies: built-in fetch() (Node 20+ or a browser).
//
// Usage:
//     node list_collections.mjs            every collection
//     node list_collections.mjs sv         those that can be read in Swedish (a BCP 47 tag)
import { catalogue, title } from './gilyon.mjs';

const language = process.argv[2] || null;
const collections = await catalogue(undefined, language);
if (!collections.length) console.log('No collection' + (language ? ` in '${language}'.` : '.'));
for (const c of collections) {
  console.log(title(c));
  console.log(`  manifest:    ${c.manifest}`);
  console.log(`  licence:     ${c.license}` + (c.attribution ? `  (${c.attribution})` : ''));
  console.log(`  books:       ${(c.books || []).join(' ')}   annotations: ${c.annotations ?? '?'}`);
  console.log(`  languages:   ${(c.languages || []).join(', ') || 'none: anchors only, no wording'}`);
  for (const t of c.translations || []) {
    console.log(`  translation: ${t.languages.join(', ')} by ${t.publisher?.name ?? '?'} (${t.by ?? '?'})`);
  }
  const checked = c.checked || {};
  console.log(`  checked:     ${checked.date ?? '?'} ${checked.result ?? '?'}; status ${c.status ?? 'listed'}`);
}
