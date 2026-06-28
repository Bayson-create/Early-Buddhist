# Early Buddhist Texts Search

巴利语三藏经典全文检索 · Pāli Canon Full-Text Search

基于 [SuttaCentral](https://suttacentral.net) 数据源，提供巴利语三藏经典的英文和中文全文搜索功能。

## 功能

- **英文逐句段搜索**：搜索 206,440 条英文译文句段（Bilara 分段对齐）
- **中文全文搜索**：搜索 149,860 条中文译文句段（Legacy HTML 译文）
- **按藏经部筛选**：支持在经藏（DN/MN/SN/AN/KN）、律藏、论藏各部中搜索
- **美观展示**：每条结果显示经文 UID、所属藏/经部、译者、句段 ID，关键词高亮
- **链接 SuttaCentral**：点击经文 UID 可跳转至 SuttaCentral 原文页面

## 数据来源

- 英文译文：SuttaCentral Bilara 分段译文（published + unpublished）
- 中文译文：SuttaCentral Legacy HTML 汉语译文（莊春江等译者）
- 巴利原文：SuttaCentral Bilara root texts

## 目录结构

```
data/           — 按藏经部拆分的 JSON 数据文件（巴利-英文/巴利-中文对照）
docs/           — GitHub Pages 静态站点
  index.html    — 搜索页面
  collections.json — 藏经部元数据
  search_index_en_*.json — 英文搜索索引
  search_index_zh_*.json — 中文搜索索引
build_index.py  — 索引构建脚本
```

## 本地开发

```bash
python3 -m http.server 8765 -d docs
# 访问 http://localhost:8765
```

## License

Data sourced from [SuttaCentral](https://suttacentral.net), available under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).
