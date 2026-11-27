#!/usr/bin/env node
// Show the annotations of a Gilyon collection in a chapter of a Bible translation.
// No dependencies: built-in fetch() and Web Crypto (Node 20+ or a browser), and the copy of
// verse-text beside this file.
//
// A Gilyon annotation points at Hebrew or Greek words. To show it in a translation this
// script fetches, just in time:
//
//   1. the chapter's text, from helloAO, read with bcv-commons/bibles' verse-text;
//   2. the word alignment of that translation (bcv-commons/compact-alignments, CC0), after
//      checking that it was made on exactly this text (the text fingerprint);
//   3. the Gilyon files for the chapter (the manifest says which);
//
// and then puts each annotation where its anchor words are rendered.
//
// Usage:
//     node show_in_edition.mjs <BOOK> <chapter> [options]
//     node show_in_edition.mjs JOS 1
//     node show_in_edition.mjs GEN 1 --collection https://gilyon.org/0.1/examples/collection-parts/manifest.json --language en
//
// Options (defaults: the Berean Standard Bible):
//     --collection URL   manifest of the Gilyon collection
//     --language TAG     language of the wording to show, where the collection has it
//     --helloao ID       the translation's id at bible.helloao.org          (BSB)
//     --alignment NAME   its folder in compact-alignments                   (eng_BSB)
//     --iso CODE         its ISO 639-3 code                                 (eng)
//     --scheme NAME      its verse numbering: eng, org, orgw, vul, ...      (eng)
import { tokenize } from './verse_text/tokenize.js';
import { tokenizeWritten } from './verse_text/tokenize_written.js';
import { mergeBookUsj } from './verse_text/helloao_to_usj.mjs';
import { extractUsj } from './verse_text/extract_usj.js';
import * as gilyon from './gilyon.mjs';

const HELLOAO = 'https://bible.helloao.org/api';
const ALIGN = 'https://huggingface.co/datasets/bcv-commons/compact-alignments/resolve/main';
const ALIGN_META = 'https://huggingface.co/datasets/bcv-commons/compact-alignments-meta/resolve/main';
const DEFAULT = 'https://gilyon.org/collections/swe_svk/manifest.json';
const MARKS = '⁰¹²³⁴⁵⁶⁷⁸⁹';

const text = (bytes) => new TextDecoder().decode(bytes);
const mark = (n) => '⁽' + [...String(n)].map((d) => MARKS[Number(d)]).join('') + '⁾';

// ---------------------------------------------------------------- 1. the chapter's text

/** -> Map verse number -> text, the verse text every bcv-commons tool agrees on. */
async function chapterText(helloaoId, book, chapter) {
  const data = JSON.parse(text(await gilyon.get(`${HELLOAO}/${helloaoId}/${book}/${chapter}.json`)));
  const usj = mergeBookUsj(book, [data]);
  return new Map((extractUsj(usj)[String(chapter)] || []).map((v) => [Number(v.verse), v.text]));
}

async function chapterFingerprint(verses) {
  const lines = [];
  for (const v of [...verses.keys()].sort((a, b) => a - b)) {
    const tokens = tokenize(verses.get(v));
    if (tokens.length) lines.push(`${v}:${tokens.join(' ')}`);
  }
  return gilyon.sha256(new TextEncoder().encode(lines.join('\n')));
}

// ---------------------------------------------------------------- 2. the alignment

/** -> {aligned: Map 'chapter:verse' -> {verseKeys, words: Map word key -> [token position]}, message}
 *  The alignment file is named by the fingerprint of the text it was made on. We take the
 *  latest one for the book and use it only if our chapter is that text. */
async function alignment(iso, name, book, chapter, fingerprint) {
  const folder = `${iso[0]}/${iso}/${name}`;
  const listing = await gilyon.get(`${ALIGN_META}/${folder}/_fingerprints.txt`, true);
  const found = (listing ? text(listing) : '').split('\n').find((ln) => ln.startsWith(book + ' '));
  const aligned = new Map();
  if (!found) return { aligned, message: `no alignment of ${book} is published for ${name}` };
  const line = found.trim().split(/\s+/);
  const chapters = new Map();
  let n = 0;
  for (let item of line.slice(3)) {                         // 'da348', or '5:1ab2c' where the sequence breaks
    if (item.includes(':')) { n = Number(item.split(':')[0]) - 1; item = item.split(':')[1]; }
    n += 1;
    chapters.set(n, item);
  }
  if (chapters.get(chapter) !== fingerprint.slice(0, 5)) {
    return { aligned, message: 'the alignment was made on another wording of this chapter, so it is not used' };
  }
  const keys = JSON.parse(text(await gilyon.get(`${ALIGN}/_index/${book}_keys.json`)));   // verse -> the word keys, in order
  const array = JSON.parse(text(await gilyon.get(`${ALIGN}/${folder}/${book}_${line[1]}.json`)));
  Object.entries(keys).forEach(([ref, verseKeys], i) => {
    const words = new Map();
    for (const part of (array[i] || '').split(' ').filter(Boolean)) {   // '3:5-6' = word 3 is rendered by tokens 5 and 6
      const [ordinal, tokens] = part.split(':');
      const positions = [];
      for (const piece of tokens.split(',')) {
        const [lo, hi = lo] = piece.split('-');
        for (let p = Number(lo); p <= Number(hi); p++) positions.push(p);
      }
      for (const key of verseKeys[Number(ordinal)].split('+')) words.set(key, positions);
    }
    aligned.set(ref.split(' ')[1], { verseKeys, words });
  });
  return { aligned, message: `text fingerprint ${fingerprint.slice(0, 5)} matches the aligned text` };
}

/** Base-text verse -> the translation's verse, where the numbering differs. */
async function verseMap(scheme) {
  if (scheme === 'org') return {};
  const data = await gilyon.get(`${ALIGN}/_index/_versification_${scheme}.json`, true);
  return data ? JSON.parse(text(data)).map : {};
}

function editionPlace(vmap, book, chapter, verse) {
  const ref = vmap[`${book} ${chapter}:${verse}`];
  if (ref === undefined) return [chapter, verse];
  const [c, v] = ref.split(' ')[1].split(':');
  return v === 'title' ? [Number(c), null] : [Number(c), Number(v)];
}

/** The chapters of the base text a chapter of the translation draws on (spec §16.5 rule 8). */
function baseChapters(vmap, book, chapter) {
  const out = new Set([chapter]);
  for (const [spine, edition] of Object.entries(vmap)) {
    if (spine.startsWith(book + ' ') && edition.startsWith(`${book} ${chapter}:`)) out.add(Number(spine.split(' ')[1].split(':')[0]));
  }
  return [...out].sort((a, b) => a - b);
}

// ---------------------------------------------------------------- 3. placing an annotation

/** -> [base-text [chapter, verse] or null, token position to put the mark after or null, how] */
function place(selector, aligned) {
  const kind = selector.type;
  if (kind === 'Passage') return [gilyon.span(selector.ref)[1], null, 'verse'];
  let ids;
  if (kind === 'Point') ids = ['after', 'before'].filter((k) => k in selector).map((k) => selector[k]);
  else if (kind === 'Words') ids = selector.words;
  else if (kind === 'Range') ids = [selector.first, selector.last];
  else return [null, null, 'no place'];
  const where = gilyon.wordPlace(ids[0]);
  const { verseKeys = [], words = new Map() } = aligned.get(where.join(':')) || {};
  const content = verseKeys.flatMap((group) => group.split('+'));   // the verse's content words, in order

  // Token positions of a word; of the nearest content word on `side` if it is a function word.
  const tokens = (wordId, side) => {
    let key = wordId.slice(1);
    if (!content.includes(key)) {
      const near = content.filter((k) => (side < 0 ? k < key : k > key));
      if (!near.length) return null;
      key = side < 0 ? near[near.length - 1] : near[0];
    }
    return words.get(key) || null;
  };
  const filled = (x) => (x && x.length ? x : null);

  if (kind === 'Point') {
    const after = 'after' in selector ? filled(tokens(selector.after, -1)) : null;
    const before = 'before' in selector ? filled(tokens(selector.before, +1)) : null;
    if (after && before && Math.max(...after) < Math.min(...before)) return [where, Math.max(...after), 'between its two anchor words'];
    if (after && !before) return [where, Math.max(...after), 'after its anchor word'];
    if (before && !after) return [where, Math.min(...before) - 1, 'before its anchor word'];
    if (after && before) return [where, null, 'verse (the two anchor words come in the other order here)'];
    return [where, null, 'verse (anchor words not aligned)'];
  }
  let found;
  if (kind === 'Range') {
    const lo = selector.first.slice(1), hi = selector.last.slice(1);
    found = content.filter((k) => lo <= k && k <= hi).flatMap((k) => words.get(k) || []);
  } else {
    found = ids.flatMap((w) => tokens(w, 0) || []);
  }
  if (found.length) return [where, Math.max(...found), 'after the words that render it'];
  return [where, null, 'verse (words not aligned)'];
}

/** The verse text with a mark after each token position (-1: before the first word; null: at the end). */
function withMarks(verse, marks) {
  let cut = new Map(), pos = 0;
  tokenizeWritten(verse).every((token, i) => {              // where each token ends in the text
    const at = verse.indexOf(token, pos);
    if (at < 0) { cut = null; return false; }
    pos = at + token.length;
    cut.set(i, pos);
    return true;
  });
  let tail = '';
  const inserts = new Map();
  for (const [position, label] of marks) {
    if (position === null || cut === null || (position >= 0 && !cut.has(position))) tail += label;
    else {
      const at = position < 0 ? 0 : cut.get(position);
      inserts.set(at, (inserts.get(at) || '') + label);
    }
  }
  let out = verse;
  for (const at of [...inserts.keys()].sort((a, b) => b - a)) out = out.slice(0, at) + inserts.get(at) + out.slice(at);
  return out + tail;
}

// ---------------------------------------------------------------- command line

const opt = { collection: DEFAULT, language: null, helloao: 'BSB', alignment: 'eng_BSB', iso: 'eng', scheme: 'eng' };
const positional = [];
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  if (argv[i].startsWith('--')) opt[argv[i].slice(2)] = argv[++i];
  else positional.push(argv[i]);
}
if (positional.length < 2) {
  console.error('usage: show_in_edition.mjs <BOOK> <chapter> [--collection URL] [--language TAG] [--helloao ID] [--alignment NAME] [--iso CODE] [--scheme NAME]');
  process.exit(1);
}
const book = positional[0], chapter = Number(positional[1]);

const verses = await chapterText(opt.helloao, book, chapter);
const { aligned, message } = await alignment(opt.iso, opt.alignment, book, chapter, await chapterFingerprint(verses));
const vmap = await verseMap(opt.scheme);
const { manifest, annotations } = await gilyon.chapter(opt.collection, book, baseChapters(vmap, book, chapter), opt.language);

console.log(`${book} ${chapter} in ${opt.helloao}, with: ${gilyon.title(manifest)}`);
console.log(`Annotations: ${manifest.license}, ${manifest.attribution ?? ''}`);
console.log(`Alignment: bcv-commons/compact-alignments (${opt.alignment}); ${message}\n`);

const byVerse = new Map(), notes = [], elsewhere = [];
for (const ann of annotations) {
  for (const target of gilyon.targets(ann)) {
    const selector = target.selector || {};
    const [where, position, how] = place(selector, aligned);
    const wording = (ann.body || []).map((b) => b.value).join(' / ') || '(no wording published)';
    const status = target.anchoring?.status ?? '';
    if (where === null) { elsewhere.push(`${selector.lexeme ?? selector.type}: ${wording}`); continue; }
    const [c, v] = editionPlace(vmap, book, ...where);
    if (c !== chapter || (v !== null && !verses.has(v))) continue;   // not in the chapter shown (spec §16.5 rule 10)
    const label = ann.source?.noteId || ann.motivation;
    notes.push(`${mark(notes.length + 1)} ${label}: ${wording}\n      placed ${how}; anchor ${status}`);
    if (!byVerse.has(v)) byVerse.set(v, []);
    byVerse.get(v).push([position, mark(notes.length)]);
  }
}
for (const v of [...verses.keys()].sort((a, b) => a - b)) {
  console.log(`${String(v).padStart(3)} ${withMarks(verses.get(v), byVerse.get(v) || [])}`);
}
console.log();
if (notes.length) console.log(notes.join('\n'));
for (const line of elsewhere) console.log(`  * ${line}`);
