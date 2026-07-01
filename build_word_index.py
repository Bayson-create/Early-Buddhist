#!/usr/bin/env python3
"""
Build a word-level BM25 inverted index (+ a smaller char-bigram OOV
fallback index, Chinese only) over the same entries build_index.py
produces, so the static site can search this ~356k-sentence corpus
without downloading and linearly scanning the whole thing on every
query, and without being limited to a fixed ~130-term glossary.

Reuses build_index.py's build_english_index()/build_chinese_index() so
entry ordering is identical to the existing search_index_en_N.json /
search_index_zh_N.json chunk files: entry_id (0-based, sequential) maps
straight back to (chunk_idx = entry_id // CHUNK_SIZE, local_idx =
entry_id % CHUNK_SIZE) with zero changes to those files or to
build_index.py's chunking logic.

Why word-level BM25 instead of the char-bigram approach used elsewhere
(see docs/SEARCH_ARCHITECTURE.md for the full writeup):
  - Vocabulary size is bounded (real ZH/EN words), so unlike character
    bigrams it doesn't need aggressive frequency-based pruning to stay
    small - meaning common-but-meaningful compounds don't get dropped.
  - BM25's IDF weighting means a match on a rare, informative word counts
    far more than a match on a common one, which is a real relevance
    signal - plain bigram-coverage counting (dhamma-lineage's approach)
    treats every matched bigram equally.
  - Entries here are already sentence/segment-level (short), so a
    same-entry match is a much stronger topical-relevance prior than a
    same-document match in a system indexing whole multi-juan texts.
    Storing token positions on top of that lets query-time scoring add
    a proximity/order bonus (do the query's words actually cluster
    together in this entry, in roughly the right order?) as an explicit
    anti-"coincidental co-occurrence" mechanism.

Requires: pip install jieba opencc-python-reimplemented

Usage:
    python3 build_word_index.py
"""
import json
import re
import sys
import zlib
from collections import defaultdict
from pathlib import Path

import jieba
from opencc import OpenCC

from build_index import build_english_index, build_chinese_index

CHUNK_SIZE = 30000  # must match build_index.py
WORD_BUCKETS = 64
BIGRAM_BUCKETS = 64
BIGRAM_DF_CEILING = 0.15  # ZH-only OOV fallback; see build_search_index.py in
                          # the sibling dhamma-lineage project for the same idea

cc_t2s = OpenCC("t2s")

# ===== glossary (ported from docs/index.html's GLOSSARY_ZH, kept in sync
# by hand - it's a short list and duplicating it avoids adding a second
# runtime dependency between the Python build step and the JS UI) =====
GLOSSARY_ZH_RAW = [
    "四念处", "四念處", "八正道", "八聖道", "四圣谛", "四聖諦", "十二因缘", "十二因緣", "七觉支", "七覺支",
    "五蕴", "五蘊", "四如意足", "四正勤", "五根", "五力", "三十七道品",
    "正见", "正見", "正思维", "正思惟", "正语", "正語", "正业", "正業", "正命", "正精进", "正精進", "正念", "正定",
    "苦谛", "苦諦", "集谛", "集諦", "灭谛", "滅諦", "道谛", "道諦",
    "色蕴", "色蘊", "受蕴", "受蘊", "想蕴", "想蘊", "行蕴", "行蘊", "识蕴", "識蘊",
    "无明", "無明", "名色", "六处", "六處", "六入", "缘起", "緣起",
    "涅槃", "解脱", "解脫", "烦恼", "煩惱", "贪", "貪", "嗔", "瞋", "痴", "无常", "無常", "无我", "無我",
    "禅那", "禪那", "初禅", "初禪", "二禅", "二禪", "三禅", "三禪", "四禅", "四禪",
    "阿罗汉", "阿羅漢", "菩提", "觉悟", "覺悟", "轮回", "輪迴", "业", "業", "因果",
    "戒", "定", "慧", "布施", "持戒", "精进", "精進", "忍辱",
    "比丘", "比丘尼", "僧伽", "僧团", "僧團", "三宝", "三寶", "世尊", "如来", "如來", "善逝",
    "神通", "宿命", "天眼", "漏尽", "漏盡", "须陀洹", "須陀洹", "斯陀含", "阿那含",
    "慈", "悲", "喜", "舍", "捨", "四无量心", "四無量心", "安般", "出入息",
    "正知", "善法", "不善法", "善根", "不善根", "五盖", "五蓋", "三毒", "三学", "三學",
    "色界", "无色界", "無色界", "欲界", "结", "結", "随眠", "隨眠",
    "苦", "集", "灭", "滅", "道", "空", "受", "想", "行", "识", "識", "触", "觸", "爱", "愛", "取", "有", "生", "老死",
]
GLOSSARY_ZH = sorted({cc_t2s.convert(t) for t in GLOSSARY_ZH_RAW})

# Ultra-common grammatical particles: dropped from the index (near-zero
# IDF anyway, only bloat) UNLESS they're a glossary term in their own
# right (several single-character Buddhist terms - 受/想/行/识/苦/集/灭/道 -
# are also common function-word-shaped characters in ordinary prose).
ZH_STOP = set("的了是在与及之也而或则即乃矣焉哉故若如所其此彼吾汝你他她它們们着過过被把讓让給给對对從从到為为以於于又還还並并但卻却才就都很更最不沒没無无一個个這这那些").difference(
    set(GLOSSARY_ZH)
)

EN_STOP = set(
    "what is are the a an of in to and or how do does this that it for with on at by from as be was were "
    "been being have has had will would could should may might can shall not no but if then so than too "
    "very just about which who whom whose when where why i you he she we they me him her us them my your "
    "his its our their".split(" ")
)
EN_WORD_RE = re.compile(r"[a-zA-Zāīūṁṃṅñṭḍṇḷ']+")

# Pali root text carries diacritics (sāti, ānāpāna...) that users very
# often don't type. Alongside the exact accented token, every token
# containing a diacritic also gets indexed under its accent-stripped
# form (sati, anapana...) so a plain-ASCII query still finds it - this
# replaces the old runtime paliFlexRegex character-class approach with an
# index-time normalization that's cheaper to look up (one extra postings
# entry instead of compiling and running a regex against every entry).
_DIACRITIC_FOLD = str.maketrans("āīūṁṃṅñṭḍṇḷ", "aiummnntdnl")


def fold_diacritics(word):
    return word.translate(_DIACRITIC_FOLD)


def setup_jieba():
    for term in GLOSSARY_ZH:
        jieba.add_word(term, freq=200000)


def tokenize_zh(text):
    """Returns [(token, start_offset)] over the Simplified-normalized text."""
    norm = cc_t2s.convert(text)
    out = []
    for word, start, _end in jieba.tokenize(norm):
        w = word.strip()
        if not w:
            continue
        if w in ZH_STOP:
            continue
        out.append((w, start))
    return norm, out


def tokenize_en(text, pali_text=""):
    """Returns [(token, start_offset)] over the lowercased English text,
    plus the entry's Pali root text (both the exact diacritic form and an
    accent-stripped fallback form) so Pali terms are searchable even
    though only English is used for display in the search results list."""
    lower = text.lower()
    out = []
    for m in EN_WORD_RE.finditer(lower):
        w = m.group(0)
        if w in EN_STOP or len(w) < 2:
            continue
        out.append((w, m.start()))

    if pali_text:
        pali_lower = pali_text.lower()
        offset_base = len(lower) + 1
        for m in EN_WORD_RE.finditer(pali_lower):
            w = m.group(0)
            if len(w) < 2:
                continue
            pos = offset_base + m.start()
            out.append((w, pos))
            folded = fold_diacritics(w)
            if folded != w:
                out.append((folded, pos))
    return lower, out


def build_bm25_index(entries, tokenize_fn, lang_label):
    """
    postings[word] -> list of [entry_id, tf, [offsets...]]
    """
    postings = defaultdict(list)
    entry_lengths = []
    total_tokens = 0

    for entry_id, entry in enumerate(entries):
        if "e" in entry:
            _norm, tokens = tokenize_fn(entry["e"], entry.get("p", ""))
        else:
            _norm, tokens = tokenize_fn(entry["z"])
        entry_lengths.append(len(tokens))
        total_tokens += len(tokens)

        per_word = defaultdict(list)
        for word, offset in tokens:
            per_word[word].append(offset)
        for word, offsets in per_word.items():
            postings[word].append([entry_id, len(offsets), offsets])

        if (entry_id + 1) % 20000 == 0:
            print(f"  [{lang_label}] tokenized {entry_id + 1}/{len(entries)}", file=sys.stderr)

    avgdl = total_tokens / len(entries) if entries else 0.0
    return postings, entry_lengths, avgdl


def shard_and_write(postings, out_dir, buckets, label):
    out_dir.mkdir(parents=True, exist_ok=True)
    shards = defaultdict(dict)
    for word, plist in postings.items():
        b = zlib.crc32(word.encode("utf-8")) % buckets
        shards[b][word] = plist

    total_bytes = 0
    for b in range(buckets):
        fname = f"shard_{b:03d}.json"
        payload = shards.get(b, {})
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        (out_dir / fname).write_text(data, encoding="utf-8")
        total_bytes += len(data.encode("utf-8"))
    print(f"  [{label}] {len(postings)} words, {buckets} shards, {total_bytes / 1024 / 1024:.1f} MB total")


def write_entry_collections(entries, out_path):
    """Compact entry_id -> collection-key lookup so the client can honor
    the existing collection filter BEFORE fetching each candidate's full
    chunk file (the postings/BM25 pass only knows entry_id + score, not
    which collection an entry belongs to)."""
    keys = sorted({e["c"] for e in entries})
    key_to_idx = {k: i for i, k in enumerate(keys)}
    mapping = [key_to_idx[e["c"]] for e in entries]
    out_path.write_text(
        json.dumps({"keys": keys, "map": mapping}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def build_bigram_fallback(entries, get_text_fn, out_dir, n_entries):
    """ZH-only OOV safety net: bigram -> [entry_ids] (presence only, no tf),
    pruned by document-frequency ceiling, same idea as the bigram index in
    the sibling dhamma-lineage project."""
    postings = defaultdict(set)
    for entry_id, entry in enumerate(entries):
        text = get_text_fn(entry)
        norm = cc_t2s.convert(text)
        seen = set(a + b for a, b in zip(norm, norm[1:]))
        for bg in seen:
            postings[bg].add(entry_id)

    ceiling = int(n_entries * BIGRAM_DF_CEILING)
    kept = {bg: sorted(ids) for bg, ids in postings.items() if len(ids) <= ceiling}
    dropped = len(postings) - len(kept)
    print(f"  [zh-bigram] {len(postings)} bigrams, dropping {dropped} (df > {BIGRAM_DF_CEILING:.0%}), keeping {len(kept)}")
    shard_and_write(kept, out_dir, BIGRAM_BUCKETS, "zh-bigram")


def main():
    out_root = Path(__file__).parent / "docs"
    setup_jieba()

    print("Loading English entries (via build_index.build_english_index)...")
    en_entries = build_english_index()
    print(f"  {len(en_entries)} entries")

    print("Building English BM25 word index...")
    en_postings, en_lengths, en_avgdl = build_bm25_index(en_entries, tokenize_en, "en")
    shard_and_write(en_postings, out_root / "word_index_en", WORD_BUCKETS, "en-words")
    (out_root / "word_index_en" / "manifest.json").write_text(
        json.dumps({"buckets": WORD_BUCKETS, "n_entries": len(en_entries), "avgdl": en_avgdl, "chunk_size": CHUNK_SIZE}),
        encoding="utf-8",
    )
    (out_root / "word_index_en" / "entry_lengths.json").write_text(
        json.dumps(en_lengths, separators=(",", ":")), encoding="utf-8"
    )
    write_entry_collections(en_entries, out_root / "word_index_en" / "entry_collections.json")

    print("Loading Chinese entries (via build_index.build_chinese_index)...")
    zh_entries = build_chinese_index()
    print(f"  {len(zh_entries)} entries")

    print("Building Chinese BM25 word index...")
    zh_postings, zh_lengths, zh_avgdl = build_bm25_index(zh_entries, tokenize_zh, "zh")
    shard_and_write(zh_postings, out_root / "word_index_zh", WORD_BUCKETS, "zh-words")
    (out_root / "word_index_zh" / "manifest.json").write_text(
        json.dumps({"buckets": WORD_BUCKETS, "n_entries": len(zh_entries), "avgdl": zh_avgdl, "chunk_size": CHUNK_SIZE}),
        encoding="utf-8",
    )
    (out_root / "word_index_zh" / "entry_lengths.json").write_text(
        json.dumps(zh_lengths, separators=(",", ":")), encoding="utf-8"
    )
    write_entry_collections(zh_entries, out_root / "word_index_zh" / "entry_collections.json")
    vocab = sorted(zh_postings.keys(), key=len, reverse=True)
    (out_root / "word_index_zh" / "vocab.json").write_text(
        json.dumps(vocab, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"  [zh-vocab] {len(vocab)} distinct words, max length {len(vocab[0]) if vocab else 0}")

    print("Building Chinese char-bigram OOV fallback index...")
    build_bigram_fallback(zh_entries, lambda e: e["z"], out_root / "bigram_index_zh", len(zh_entries))

    print("\nDone.")


if __name__ == "__main__":
    main()
