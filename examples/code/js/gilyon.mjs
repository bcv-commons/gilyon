// Reading Gilyon collections: a small client with no dependencies (Node 20+ or a browser).
//
//   catalogue(indexUrl, language)                  the collections of a catalogue
//   chapter(manifestUrl, book, chapters, language) the annotations a passage needs (spec §16.5)
//
// Nothing here knows about a Bible translation. Placing an annotation in a translation needs
// that translation's text and a word alignment; see show_in_edition.mjs.

export const CATALOGUE = 'https://gilyon.org/collections/index.json';

export async function get(url, optional = false) {
  const res = await fetch(url);
  if (optional && res.status === 404) return null;
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  return new Uint8Array(await res.arrayBuffer());
}

export async function sha256(bytes) {
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, '0')).join('');
}

/** Fetch JSON; with `hash`, refuse a file that is not the one the manifest states. */
export async function getJson(url, hash) {
  const bytes = await get(url);
  if (hash && (await sha256(bytes)) !== hash) throw new Error(`${url}: not the file the manifest states (SHA-256 differs)`);
  return JSON.parse(new TextDecoder().decode(bytes));
}

export const join = (base, ref) => new URL(ref, base).href;

// ---------------------------------------------------------------- references (spec Appendix B)

const REF = /^([A-Z0-9]{3})(?: (\d{1,3})(?:[:.](\d{1,3}|title)[a-z]?)?(?:-(?:(\d{1,3})[:.])?(\d{1,3}|title)[a-z]?)?)?$/;

/** 'JOS 1:1-2:5' -> ['JOS', [1, 1], [2, 5]]; a whole chapter runs from verse 0 to 999. */
export function span(ref) {
  const m = REF.exec(ref);
  if (!m) throw new Error(`not a reference: ${ref}`);
  const [, book, c1, v1, c2, e] = m;
  const num = (v) => (v === 'title' ? 0 : Number(v));
  if (c1 === undefined) return [book, [0, 0], [999, 999]];
  if (v1 === undefined) return [book, [Number(c1), 0], [e ? Number(e) : Number(c1), 999]];
  if (e === undefined) return [book, [Number(c1), num(v1)], [Number(c1), num(v1)]];
  return [book, [Number(c1), num(v1)], [c2 ? Number(c2) : Number(c1), num(e)]];
}

export function overlaps(ref, book, chapters) {
  const [b, first, last] = span(ref);
  return b === book && chapters.some((c) => first[0] <= c && c <= last[0]);
}

// ---------------------------------------------------------------- the catalogue (spec §16.4)

/** The collections of a catalogue: all of them, or those readable in one language. */
export async function catalogue(indexUrl = CATALOGUE, language = null) {
  const index = await getJson(indexUrl);
  let slices;
  if (language) {
    const entry = index.languages[language];
    slices = entry ? [entry.path] : [];
  } else {
    slices = index.publishers.map((p) => p.path);
  }
  const seen = new Set(), out = [];
  for (const path of slices) {
    const url = join(indexUrl, path);
    for (const c of (await getJson(url)).collections) {
      if (seen.has(c.id)) continue;
      seen.add(c.id);
      out.push({ ...c, manifest: join(url, c.manifest) });   // absolute address
    }
  }
  return out;
}

// ---------------------------------------------------------------- one passage of a collection (spec §16.5)

/** -> {manifest, wanted: [[file entry, address its paths resolve against], ...]}
 *  Only the files whose stated coverage (`ref`) overlaps the chapters, and the files of the
 *  book that state none. `chapters` are chapters of the base text. */
export async function filesFor(manifestUrl, book, chapters) {
  const manifest = await getJson(manifestUrl);
  const listed = (manifest.files || []).map((e) => [e, manifestUrl]);
  for (const part of manifest.parts || []) {
    if (!part.books.includes(book)) continue;               // read only the part for this book
    const url = join(manifestUrl, part.path);
    for (const e of (await getJson(url, part.sha256)).files) listed.push([e, url]);
  }
  const wanted = listed.filter(([entry]) => {
    if (!entry.books.includes(book)) return false;
    const refs = typeof entry.ref === 'string' ? [entry.ref] : entry.ref;
    return refs === undefined || refs.some((r) => overlaps(r, book, chapters));
  });
  return { manifest, wanted };
}

/** The annotations for `chapters` of `book`, each with its wording where there is one.
 *  An annotation gets `body` from the body document of `language`, else of the collection's
 *  source language (spec §16.2). -> {manifest, annotations} */
export async function chapter(manifestUrl, book, chapters, language = null) {
  const { manifest, wanted } = await filesFor(manifestUrl, book, chapters);
  const source = manifest.sourceLanguage;
  const annotations = [];
  for (const [entry, base] of wanted) {
    const doc = await getJson(join(base, entry.path), entry.sha256);
    const wording = new Map();
    for (const tag of [source, language]) {                 // the requested language wins
      const b = tag ? (entry.bodies || {})[tag] : null;
      if (!b) continue;
      for (const e of (await getJson(join(base, b.path), b.sha256)).entries) {
        if (!('unit' in e)) wording.set(e.annotation, [tag, e.body]);
      }
    }
    for (let a of doc.annotations) {
      if (!('body' in a) && wording.has(a.id)) {
        const [tag, body] = wording.get(a.id);
        a = { ...a, body: body.map((x) => ({ ...x, language: x.language ?? tag })) };
      }
      annotations.push(a);
    }
  }
  return { manifest, annotations };
}

export function title(obj, language = 'en') {
  const t = obj.title ?? '';
  if (typeof t === 'object') return t[language] || Object.values(t)[0] || '';
  return t;
}

export function targets(annotation) {
  const t = annotation.target;
  return Array.isArray(t) ? t : t ? [t] : [];
}

/** 'o060010010051' -> [chapter, verse] of the base text. */
export const wordPlace = (id) => [Number(id.slice(3, 6)), Number(id.slice(6, 9))];
