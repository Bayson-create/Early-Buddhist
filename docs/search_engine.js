// BM25 word-level search engine, replacing "download the whole language
// corpus and linearly .includes() scan it" with:
//   1. tokenize the query the SAME way the offline indexer tokenized the
//      corpus (see build_word_index.py) - a vocabulary-driven greedy
//      longest-match segmenter for Chinese (jieba isn't available in the
//      browser, but the exact word list it discovered is, via vocab.json,
//      so a dictionary-based segmenter using that list stays consistent
//      with how the index itself was built), plain word tokenization for
//      English (unambiguous, no segmenter needed);
//   2. look up only the index shards those tokens hash to;
//   3. score every candidate with BM25 (IDF * TF-saturation) instead of a
//      flat "did this bigram occur" count, so rare/informative words
//      count for far more than common ones - a real precision upgrade
//      over plain coverage counting;
//   4. add a proximity bonus from the stored token offsets - do the
//      query's words actually cluster together in this entry, roughly in
//      order? - as an explicit defense against "these words happen to
//      both appear somewhere in a long text but are unrelated";
//   5. for Chinese, any character not covered by a recognized vocabulary
//      word also gets a lightweight char-bigram fallback search (a much
//      smaller supplementary index), so words the corpus itself never
//      used aren't just silently dropped from the query - out-of-
//      vocabulary terms still contribute what evidence exists;
//   6. resolve only the winning candidates back to actual display text,
//      fetching only the specific existing chunk files
//      (search_index_{lang}_N.json) that contain them - never the whole
//      corpus.
//
// Requires: toS()/toT() (index.html), EN_STOP (index.html).

const BM25_K1 = 1.5;
const BM25_B = 0.75;
const CHUNK_SIZE = 30000; // must match build_word_index.py / build_index.py

const engineState = {
  wordManifest: { zh: null, en: null },
  entryLengths: { zh: null, en: null },
  entryCollections: { zh: null, en: null },
  vocabSet: null,
  vocabMaxLen: 1,
  wordShardCache: { zh: new Map(), en: new Map() },
  bigramShardCache: new Map(),
  chunkCache: new Map(), // "zh_0" -> parsed array
};

async function fetchJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`fetch failed: ${path} (${res.status})`);
  return res.json();
}

async function ensureWordManifest(lang) {
  if (engineState.wordManifest[lang]) return;
  const dir = `word_index_${lang}`;
  const [manifest, lengths, collections] = await Promise.all([
    fetchJson(`${dir}/manifest.json`),
    fetchJson(`${dir}/entry_lengths.json`),
    fetchJson(`${dir}/entry_collections.json`),
  ]);
  engineState.wordManifest[lang] = manifest;
  engineState.entryLengths[lang] = lengths;
  engineState.entryCollections[lang] = collections;
}

async function ensureZhVocab() {
  if (engineState.vocabSet) return;
  const vocab = await fetchJson("word_index_zh/vocab.json");
  engineState.vocabSet = new Set(vocab);
  engineState.vocabMaxLen = vocab.length ? vocab[0].length : 1;
}

function bucketFor(word, buckets) {
  return zlib_crc32(word) % buckets;
}

// Minimal crc32 (matches Python's zlib.crc32 used by build_word_index.py)
const _CRC_TABLE = (() => {
  const t = [];
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();
function zlib_crc32(str) {
  const bytes = new TextEncoder().encode(str);
  let crc = 0xffffffff;
  for (const b of bytes) crc = _CRC_TABLE[(crc ^ b) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

async function loadWordShard(lang, word) {
  const manifest = engineState.wordManifest[lang];
  const b = bucketFor(word, manifest.buckets);
  const key = `${lang}_${b}`;
  const cache = engineState.wordShardCache[lang];
  if (cache.has(key)) return cache.get(key);
  const data = await fetchJson(`word_index_${lang}/shard_${String(b).padStart(3, "0")}.json`);
  cache.set(key, data);
  return data;
}

async function loadBigramShard(bigram) {
  const b = zlib_crc32(bigram) % 64;
  const key = `zh_bg_${b}`;
  if (engineState.bigramShardCache.has(key)) return engineState.bigramShardCache.get(key);
  const data = await fetchJson(`bigram_index_zh/shard_${String(b).padStart(3, "0")}.json`);
  engineState.bigramShardCache.set(key, data);
  return data;
}

// ===== Tokenizers: MUST stay consistent with build_word_index.py =====

function zhTokenizeQuery(text) {
  const norm = toS(text.trim());
  const vocab = engineState.vocabSet;
  const maxLen = engineState.vocabMaxLen;
  const tokens = [];
  const covered = new Array(norm.length).fill(false);
  let i = 0;
  while (i < norm.length) {
    let matchLen = 0;
    for (let l = Math.min(maxLen, norm.length - i); l >= 1; l--) {
      const cand = norm.slice(i, i + l);
      if (vocab.has(cand)) {
        matchLen = l;
        break;
      }
    }
    if (matchLen > 0) {
      const word = norm.slice(i, i + matchLen);
      if (!ZH_INDEX_STOP.has(word)) tokens.push({ word, start: i });
      for (let k = i; k < i + matchLen; k++) covered[k] = true;
      i += matchLen;
    } else {
      i += 1;
    }
  }
  // Any bigram touching an uncovered character is a candidate for the
  // OOV fallback - a word the vocabulary-based segmenter couldn't place.
  const oovBigrams = new Set();
  for (let k = 0; k < norm.length - 1; k++) {
    if (!covered[k] || !covered[k + 1]) oovBigrams.add(norm.slice(k, k + 2));
  }
  return { norm, tokens, oovBigrams: Array.from(oovBigrams) };
}

// Same particle list as build_word_index.py's ZH_STOP, minus glossary
// overlaps - kept here only to avoid scoring noise from a query that's
// pure grammatical filler; harmless if this list drifts slightly from
// the Python one since it only ever discards near-zero-IDF tokens.
const ZH_INDEX_STOP = new Set(
  "的了是在与及之也而或则即乃矣焉哉故若如所其此彼吾汝你他她它們们着過过被把讓让給给對对從从到為为以於于又還还並并但卻却才就都很更最不沒没無无一個个這这那些".split("")
);

function enTokenizeQuery(text) {
  const lower = text.trim().toLowerCase();
  const tokens = [];
  const re = /[a-zA-Zāīūṁṃṅñṭḍṇḷ']+/g;
  let m;
  while ((m = re.exec(lower))) {
    const w = m[0];
    if (EN_STOP.has(w) || w.length < 2) continue;
    tokens.push({ word: w, start: m.index });
  }
  return { norm: lower, tokens };
}

// ===== BM25 scoring =====

function bm25Contribution(df, tf, entryLen, N, avgdl) {
  const idf = Math.log(1 + (N - df + 0.5) / (df + 0.5));
  const tfNorm = (tf * (BM25_K1 + 1)) / (tf + BM25_K1 * (1 - BM25_B + BM25_B * (entryLen / avgdl)));
  return idf * tfNorm;
}

function proximityBonus(matchedFirstOffsets) {
  if (matchedFirstOffsets.length < 2) return 0;
  const offsets = matchedFirstOffsets.slice().sort((a, b) => a - b);
  const span = offsets[offsets.length - 1] - offsets[0];
  return matchedFirstOffsets.length / (span + matchedFirstOffsets.length);
}

// Pali root text is indexed both under its exact diacritic form and an
// accent-stripped fallback form (see build_word_index.py's
// fold_diacritics) - so a plain-ASCII query like "sati" still finds
// entries whose Pali is "sāti", without needing a regex compiled and
// run against every candidate at query time.
const _DIACRITIC_FOLD_JS = { "ā": "a", "ī": "i", "ū": "u", "ṁ": "m", "ṃ": "m", "ṅ": "n", "ñ": "n", "ṭ": "t", "ḍ": "d", "ṇ": "n", "ḷ": "l" };
function foldDiacritics(word) {
  return word.replace(/[āīūṁṃṅñṭḍṇḷ]/g, (c) => _DIACRITIC_FOLD_JS[c] || c);
}

/**
 * Core scorer: tokens = [{word,start}], lang = 'zh'|'en'.
 * Returns Map<entryId, {score, matchedWords: Set<string>, offsets:number[]}>
 */
async function scoreTokens(tokens, lang) {
  await ensureWordManifest(lang);
  const manifest = engineState.wordManifest[lang];
  const lengths = engineState.entryLengths[lang];
  const N = manifest.n_entries;
  const avgdl = manifest.avgdl;

  const scores = new Map();
  const oovWords = [];

  for (const { word } of tokens) {
    let shard = await loadWordShard(lang, word);
    let postings = shard[word];
    let matchedWord = word;
    if (!postings && lang === "en") {
      const folded = foldDiacritics(word);
      if (folded !== word) {
        shard = await loadWordShard(lang, folded);
        postings = shard[folded];
        matchedWord = folded;
      }
    }
    if (!postings) {
      oovWords.push(word);
      continue;
    }
    const df = postings.length;
    for (const [entryId, tf, offsets] of postings) {
      const contrib = bm25Contribution(df, tf, lengths[entryId], N, avgdl);
      let rec = scores.get(entryId);
      if (!rec) {
        rec = { score: 0, matchedWords: new Set(), offsets: [] };
        scores.set(entryId, rec);
      }
      rec.score += contrib;
      rec.matchedWords.add(matchedWord);
      rec.offsets.push(offsets[0]);
    }
  }
  return { scores, oovWords };
}

async function applyBigramFallback(oovBigrams, scores, weight = 0.6) {
  if (!oovBigrams || oovBigrams.length === 0) return;
  const n = oovBigrams.length;
  for (const bg of oovBigrams) {
    const shard = await loadBigramShard(bg);
    const ids = shard[bg];
    if (!ids) continue;
    const contrib = weight / n;
    for (const entryId of ids) {
      let rec = scores.get(entryId);
      if (!rec) {
        rec = { score: 0, matchedWords: new Set(), offsets: [] };
        scores.set(entryId, rec);
      }
      rec.score += contrib;
      rec.matchedWords.add(`~${bg}`);
    }
  }
}

function applyProximity(scores) {
  for (const rec of scores.values()) {
    const bonus = proximityBonus(rec.offsets);
    rec.score = rec.score * (1 + 0.5 * bonus);
  }
}

function filterByCollection(scores, lang, collectionFilter) {
  if (!collectionFilter) return scores;
  const ec = engineState.entryCollections[lang];
  const keyIdx = ec.keys.indexOf(collectionFilter);
  if (keyIdx === -1) return new Map();
  const out = new Map();
  for (const [entryId, rec] of scores) {
    if (ec.map[entryId] === keyIdx) out.set(entryId, rec);
  }
  return out;
}

async function resolveEntries(rankedIds, lang) {
  const manifest = engineState.wordManifest[lang];
  const chunkSize = manifest.chunk_size || CHUNK_SIZE;
  const byChunk = new Map();
  for (const id of rankedIds) {
    const chunkIdx = Math.floor(id / chunkSize);
    if (!byChunk.has(chunkIdx)) byChunk.set(chunkIdx, []);
    byChunk.get(chunkIdx).push(id);
  }
  const results = [];
  await Promise.all(
    Array.from(byChunk.keys()).map(async (chunkIdx) => {
      const cacheKey = `${lang}_${chunkIdx}`;
      let chunkData = engineState.chunkCache.get(cacheKey);
      if (!chunkData) {
        chunkData = await fetchJson(`search_index_${lang}_${chunkIdx}.json`);
        engineState.chunkCache.set(cacheKey, chunkData);
      }
      for (const id of byChunk.get(chunkIdx)) {
        const localIdx = id % chunkSize;
        results.push({ id, entry: chunkData[localIdx] });
      }
    })
  );
  return new Map(results.map((r) => [r.id, r.entry]));
}

/**
 * Full pipeline: raw query -> ranked, displayable entries in the exact
 * same shape renderResultCard()/renderResults() already expect.
 * Returns { results, tokens, oovWords } (tokens/oovWords surfaced so the
 * UI can show what was actually searched for).
 */
async function engineSearch(rawQuery, lang, { collectionFilter = "", limit = 300 } = {}) {
  let tokens, oovBigrams;
  if (lang === "zh") {
    await Promise.all([ensureWordManifest("zh"), ensureZhVocab()]);
    const t = zhTokenizeQuery(rawQuery);
    tokens = t.tokens;
    oovBigrams = t.oovBigrams;
  } else {
    await ensureWordManifest("en");
    tokens = enTokenizeQuery(rawQuery).tokens;
    oovBigrams = [];
  }

  if (tokens.length === 0 && (!oovBigrams || oovBigrams.length === 0)) {
    return { results: [], tokens: [], oovWords: [] };
  }

  const { scores, oovWords } = await scoreTokens(tokens, lang);
  if (lang === "zh") await applyBigramFallback(oovBigrams, scores);
  applyProximity(scores);

  const filtered = filterByCollection(scores, lang, collectionFilter);
  const ranked = Array.from(filtered.entries())
    .sort((a, b) => b[1].score - a[1].score)
    .slice(0, limit);
  const rankedIds = ranked.map(([id]) => id);

  const entryMap = await resolveEntries(rankedIds, lang);
  const results = ranked
    .map(([id, rec]) => {
      const entry = entryMap.get(id);
      if (!entry) return null;
      return { ...entry, _score: rec.score, _matchedWords: Array.from(rec.matchedWords) };
    })
    .filter(Boolean);

  return { results, tokens: tokens.map((t) => t.word), oovWords };
}

/**
 * Single-word/phrase search used by the existing multi-term grouped view
 * and searchSingleTerm() - same engine, just one token (or a short run of
 * tokens for an English glossary phrase like "right view").
 */
async function engineSearchTerm(term, lang, { collectionFilter = "", limit = 200 } = {}) {
  return engineSearch(term, lang, { collectionFilter, limit });
}
