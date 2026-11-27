#!/usr/bin/env node
// Fetch the annotations of one chapter of a Gilyon collection.
// No dependencies: built-in fetch() (Node 20+ or a browser).
//
// Only the manifest and the files for that chapter are fetched, and each file is checked
// against the SHA-256 the manifest states.
//
// Usage:
//     node fetch_chapter.mjs <BOOK> <chapter> [manifest address] [language]
//     node fetch_chapter.mjs JOS 1
//     node fetch_chapter.mjs GEN 1 https://gilyon.org/0.1/examples/collection-parts/manifest.json en
import { chapter, targets, title } from './gilyon.mjs';

const DEFAULT = 'https://gilyon.org/collections/swe_svk/manifest.json';

function describe(selector) {
  switch (selector.type) {
    case 'Point': return `between ${selector.after ?? '(verse start)'} and ${selector.before ?? '(verse end)'}`;
    case 'Words': return 'words ' + selector.words.join(' ');
    case 'Range': return `from ${selector.first} to ${selector.last}`;
    case 'Passage': return 'passage ' + selector.ref;
    case 'Lexeme': return 'lexeme ' + selector.lexeme + ' (wherever it occurs)';
    default: return selector.type;
  }
}

const [book, chapterArg, manifestUrl = DEFAULT, language = null] = process.argv.slice(2);
if (!book || !chapterArg) {
  console.error('usage: fetch_chapter.mjs <BOOK> <chapter> [manifest address] [language]');
  process.exit(1);
}
const { manifest, annotations } = await chapter(manifestUrl, book, [Number(chapterArg)], language);
console.log(`${title(manifest)}\n${manifest.license}, ${manifest.attribution ?? ''}\n`);
for (const a of annotations) {
  for (const t of targets(a)) {
    const sel = t.selector || {};
    const anchoring = t.anchoring || {};
    let status = anchoring.status ?? '';
    if ('tier' in anchoring) status += `, ${anchoring.tier} confidence`;
    console.log(`${(sel.ref ?? '').padEnd(10)} ${describe(sel)}   [${status}]`);
  }
  for (const b of a.body || []) console.log(`           ${b.value}`);
}
console.log(`\n${annotations.length} annotations`);
