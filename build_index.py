#!/usr/bin/env python3
"""
Build search index JSON files from 按藏经部拆分_最终 data.

Produces:
  docs/search_index_en.json  — English segments index
  docs/search_index_zh.json  — Chinese legacy text index
  docs/collections.json      — Collection metadata for UI
"""

import json
import os
import re
import sys
from pathlib import Path

SOURCE_DIR = Path(__file__).parent / "docs" / "data"

COLLECTION_MAP = {
    "经藏/长部_dn": {"pitaka": "经藏 Sutta", "collection": "长部 Dīgha Nikāya", "abbr": "DN"},
    "经藏/中部_mn": {"pitaka": "经藏 Sutta", "collection": "中部 Majjhima Nikāya", "abbr": "MN"},
    "经藏/相应部_sn": {"pitaka": "经藏 Sutta", "collection": "相应部 Saṁyutta Nikāya", "abbr": "SN"},
    "经藏/增支部_an": {"pitaka": "经藏 Sutta", "collection": "增支部 Aṅguttara Nikāya", "abbr": "AN"},
    "经藏/小部_kn": {"pitaka": "经藏 Sutta", "collection": "小部 Khuddaka Nikāya", "abbr": "KN"},
    "律藏/pli-tv-bu-pm": {"pitaka": "律藏 Vinaya", "collection": "比丘波提木叉 Bhikkhu Pātimokkha", "abbr": "Bu-Pm"},
    "律藏/pli-tv-bu-vb": {"pitaka": "律藏 Vinaya", "collection": "比丘经分别 Bhikkhu Vibhaṅga", "abbr": "Bu-Vb"},
    "律藏/pli-tv-bi-pm": {"pitaka": "律藏 Vinaya", "collection": "比丘尼波提木叉 Bhikkhunī Pātimokkha", "abbr": "Bi-Pm"},
    "律藏/pli-tv-bi-vb": {"pitaka": "律藏 Vinaya", "collection": "比丘尼经分别 Bhikkhunī Vibhaṅga", "abbr": "Bi-Vb"},
    "律藏/pli-tv-kd": {"pitaka": "律藏 Vinaya", "collection": "犍度 Khandhaka", "abbr": "Kd"},
    "律藏/pli-tv-pvr": {"pitaka": "律藏 Vinaya", "collection": "附随 Parivāra", "abbr": "Pvr"},
    "论藏/ds": {"pitaka": "论藏 Abhidhamma", "collection": "法集论 Dhammasaṅgaṇī", "abbr": "Ds"},
    "论藏/dt": {"pitaka": "论藏 Abhidhamma", "collection": "界论 Dhātukathā", "abbr": "Dt"},
    "论藏/kv": {"pitaka": "论藏 Abhidhamma", "collection": "论事 Kathāvatthu", "abbr": "Kv"},
    "论藏/patthana": {"pitaka": "论藏 Abhidhamma", "collection": "发趣论 Paṭṭhāna", "abbr": "Paṭṭhāna"},
    "论藏/pp": {"pitaka": "论藏 Abhidhamma", "collection": "人施设论 Puggalapaññatti", "abbr": "Pp"},
    "论藏/vb": {"pitaka": "论藏 Abhidhamma", "collection": "分别论 Vibhaṅga", "abbr": "Vb-Abhi"},
    "论藏/ya": {"pitaka": "论藏 Abhidhamma", "collection": "双论 Yamaka", "abbr": "Ya"},
    "xplayground/other": {"pitaka": "其他", "collection": "其他 Other", "abbr": "Other"},
}


def find_collection_key(json_path: str) -> str:
    for key in COLLECTION_MAP:
        if key in json_path.replace("\\", "/"):
            return key
    return "xplayground/other"


def build_english_index():
    entries = []
    en_files = sorted(SOURCE_DIR.rglob("pali_english_*.json"))
    for fpath in en_files:
        rel = str(fpath.relative_to(SOURCE_DIR)).replace("\\", "/")
        coll_key = find_collection_key(rel)
        coll_info = COLLECTION_MAP.get(coll_key, COLLECTION_MAP["xplayground/other"])

        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)

        for text in data["texts"]:
            uid = text["uid"]
            sources = text.get("translation_sources", [])
            authors = list({s["author"] for s in sources})

            for seg in text["segments"]:
                en_texts = seg.get("english", [])
                if not en_texts:
                    continue
                combined_en = " / ".join(e["text"].strip() for e in en_texts if e["text"].strip())
                if not combined_en:
                    continue
                pali = seg.get("pali", "").strip()
                entries.append({
                    "u": uid,
                    "s": seg["segment_id"],
                    "p": pali,
                    "e": combined_en,
                    "a": authors,
                    "c": coll_key,
                })

    return entries


def split_into_sentences(text: str) -> list:
    text = re.sub(r'\n{2,}', '\n', text)
    lines = text.split('\n')
    sentences = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = re.split(r'(?<=[。！？；])', line)
        for p in parts:
            p = p.strip()
            if len(p) > 2:
                sentences.append(p)
    return sentences


def build_chinese_index():
    entries = []
    zh_files = sorted(SOURCE_DIR.rglob("pali_chinese_*.json"))
    for fpath in zh_files:
        rel = str(fpath.relative_to(SOURCE_DIR)).replace("\\", "/")
        coll_key = find_collection_key(rel)
        coll_info = COLLECTION_MAP.get(coll_key, COLLECTION_MAP["xplayground/other"])

        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)

        for text in data["texts"]:
            uid = text["uid"]
            for legacy in text.get("zh_legacy", []):
                author = legacy.get("author", "")
                author_uid = legacy.get("author_uid", "")
                title = legacy.get("title", "")
                raw_text = legacy.get("text", "")
                if not raw_text.strip():
                    continue
                sentences = split_into_sentences(raw_text)
                for i, sent in enumerate(sentences):
                    entries.append({
                        "u": uid,
                        "i": i,
                        "t": title,
                        "z": sent,
                        "a": author,
                        "au": author_uid,
                        "c": coll_key,
                    })

    return entries


VAGGA_RE = re.compile(r"^[（(]?(.+?品)[\[［].*?[\]］]?[）)]?$|^[（(]?(.+?品)[）)]?$")
UID_NUM_RE = re.compile(r"^([a-z]+)(\d+)(?:\.(\d+))?")


def extract_vagga(raw_text: str) -> str:
    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
    for line in lines[:6]:
        m = VAGGA_RE.match(line)
        if m:
            return m.group(1) or m.group(2)
    return ""


def build_title_index():
    entries = []
    en_files = {f.stem: f for f in SOURCE_DIR.rglob("pali_english_*.json")}
    zh_files = sorted(SOURCE_DIR.rglob("pali_chinese_*.json"))

    # Build uid -> english title map first
    en_titles = {}
    for fpath in sorted(SOURCE_DIR.rglob("pali_english_*.json")):
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
        for text in data["texts"]:
            segs = text.get("segments", [])
            title_segs = [s for s in segs if re.search(r":0\.\d+$", s.get("segment_id", ""))]
            title_segs.sort(key=lambda s: int(re.search(r":0\.(\d+)$", s["segment_id"]).group(1)))
            parts = []
            for s in title_segs:
                for e in s.get("english", []):
                    t = e.get("text", "").strip()
                    if t:
                        parts.append(t)
                        break
            en_titles[text["uid"]] = parts

    last_vagga = {}
    for fpath in zh_files:
        rel = str(fpath.relative_to(SOURCE_DIR)).replace("\\", "/")
        coll_key = find_collection_key(rel)
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)

        order = 0
        for text in data["texts"]:
            uid = text["uid"]
            legacies = text.get("zh_legacy", [])
            zh_title = legacies[0].get("title", "") if legacies else ""
            vagga = ""
            if legacies:
                vagga = extract_vagga(legacies[0].get("text", ""))
            if not vagga:
                vagga = last_vagga.get(coll_key, "")
            else:
                last_vagga[coll_key] = vagga

            en_parts = en_titles.get(uid, [])
            en_title = en_parts[-1] if en_parts else ""
            en_collection_label = en_parts[0] if en_parts else ""

            num_m = UID_NUM_RE.match(uid)
            nipata = None
            samyutta = None
            sutta_num = None
            if num_m and coll_key.endswith("增支部_an"):
                nipata = int(num_m.group(2))
                sutta_num = num_m.group(3)
            elif num_m and coll_key.endswith("相应部_sn"):
                samyutta = int(num_m.group(2))
                sutta_num = num_m.group(3)

            entries.append({
                "u": uid,
                "zt": zh_title,
                "et": en_title,
                "ec": en_collection_label,
                "vg": vagga,
                "c": coll_key,
                "o": order,
                "n": nipata,
                "sy": samyutta,
            })
            order += 1

    return entries


def main():
    out_dir = Path(__file__).parent / "docs"
    out_dir.mkdir(exist_ok=True)

    print("Building title index...")
    title_entries = build_title_index()
    with open(out_dir / "title_index.json", "w", encoding="utf-8") as f:
        json.dump(title_entries, f, ensure_ascii=False, separators=(",", ":"))
    size_mb = os.path.getsize(out_dir / "title_index.json") / 1024 / 1024
    print(f"  {len(title_entries)} titles, {size_mb:.1f} MB")

    print("Building English index...")
    en_entries = build_english_index()
    print(f"  {len(en_entries)} English segments")

    # Split English index into chunks (~5MB each) for lazy loading
    CHUNK_SIZE = 30000
    en_chunks = []
    for i in range(0, len(en_entries), CHUNK_SIZE):
        chunk = en_entries[i:i + CHUNK_SIZE]
        en_chunks.append(chunk)

    en_manifest = []
    for idx, chunk in enumerate(en_chunks):
        fname = f"search_index_en_{idx}.json"
        with open(out_dir / fname, "w", encoding="utf-8") as f:
            json.dump(chunk, f, ensure_ascii=False, separators=(",", ":"))
        size_mb = os.path.getsize(out_dir / fname) / 1024 / 1024
        colls = sorted(set(e["c"] for e in chunk))
        en_manifest.append({"file": fname, "count": len(chunk), "size_mb": round(size_mb, 2), "collections": colls})
        print(f"  Written {fname} ({len(chunk)} entries, {size_mb:.1f} MB)")

    print("Building Chinese index...")
    zh_entries = build_chinese_index()
    print(f"  {len(zh_entries)} Chinese sentences")

    zh_chunks = []
    for i in range(0, len(zh_entries), CHUNK_SIZE):
        chunk = zh_entries[i:i + CHUNK_SIZE]
        zh_chunks.append(chunk)

    zh_manifest = []
    for idx, chunk in enumerate(zh_chunks):
        fname = f"search_index_zh_{idx}.json"
        with open(out_dir / fname, "w", encoding="utf-8") as f:
            json.dump(chunk, f, ensure_ascii=False, separators=(",", ":"))
        size_mb = os.path.getsize(out_dir / fname) / 1024 / 1024
        colls = sorted(set(e["c"] for e in chunk))
        zh_manifest.append({"file": fname, "count": len(chunk), "size_mb": round(size_mb, 2), "collections": colls})
        print(f"  Written {fname} ({len(chunk)} entries, {size_mb:.1f} MB)")

    # Write collections metadata
    collections_data = {
        "collections": COLLECTION_MAP,
        "en_manifest": en_manifest,
        "zh_manifest": zh_manifest,
        "stats": {
            "total_en_segments": len(en_entries),
            "total_zh_sentences": len(zh_entries),
        }
    }
    with open(out_dir / "collections.json", "w", encoding="utf-8") as f:
        json.dump(collections_data, f, ensure_ascii=False, indent=2)

    print(f"\nDone. {len(en_entries)} EN + {len(zh_entries)} ZH entries.")


if __name__ == "__main__":
    main()
