# Early Buddhist Texts Search

巴利语三藏经典全文检索 · Pāli Canon Full-Text Search

基于 [SuttaCentral](https://suttacentral.net) 数据源，提供巴利语三藏经典的英文和中文全文搜索功能。

请访问网页 https://bayson-create.github.io/Early-Buddhist/ 进行查看。

## 功能

- **英文逐句段搜索**：搜索 206,440 条英文译文句段（Bilara 分段对齐）
- **中文全文搜索**：搜索 149,860 条中文译文句段（Legacy HTML 译文）
- **按藏经部筛选**：支持在经藏（DN/MN/SN/AN/KN）、律藏、论藏各部中搜索
- **美观展示**：每条结果显示经文 UID、所属藏/经部、译者、句段 ID，关键词高亮
- **链接 SuttaCentral**：点击经文 UID 可跳转至 SuttaCentral 原文页面

## 检索架构

搜索不再是"把整个语料下载进浏览器、逐条 `.includes()` 线性扫描"，也不再要求查询命中一份约130词的固定佛学术语表才能有效检索。现在的流程：

1. **离线分词建索引**（`build_word_index.py`）：中文用 [jieba](https://github.com/fxsjy/jieba) 分词（自定义词典注入术语表，保证"四念处"等多字术语不被拆开），英文按空白与标点分词；所有中文文本先经 [OpenCC](https://github.com/BYVoid/OpenCC) 归一化为简体规范形式再建索引（查询也只需归一化一次，不必像过去那样对每条记录都试简体/繁体/原文三种写法）。
2. **BM25 倒排索引**：按词分片（而非固定约130词表），每个词记录其在各条目中的出现次数与位置；检索时按 IDF × 词频饱和度打分——生僻但关键的词权重远高于"的"、"是"这类到处出现的字，这比"只要出现过就记一次"的粗略计数精确得多。
3. **字符二元组回退索引**（仅中文）：分词后仍未被词表覆盖的字符，另外查一份轻量的字符二元组索引，确保词库外的表达（网络流行语、非佛学词汇等）依然能取得部分证据，而不是直接返回空。
4. **邻近度加权**：命中的多个查询词在同一条目中越靠得近、顺序越吻合，分数加成越高——这是专门针对"两个词各自出现过，但其实毫不相关"这种误判设计的抗噪机制。
5. **按需加载**：一次查询只拉取涉及到的词分片（几十到几百KB）和最终命中条目所在的现有分块文件，不再无条件下载整门语言的全部索引。

存在多个候选术语（如同时问"四圣谛"和"缘起"）时，仍保留原有的分组展示（每个术语单独一组，可展开）；单一查询（无论是完整问句还是陈述句）则统一交给 BM25 引擎整体打分排序，不再要求先在固定术语表里命中才能检索。

详见 `build_word_index.py`（索引构建）与 `docs/search_engine.js`（客户端检索引擎）的代码注释。

## 数据来源

- 英文译文：SuttaCentral Bilara 分段译文（published + unpublished）
- 中文译文：SuttaCentral Legacy HTML 汉语译文（莊春江等译者）
- 巴利原文：SuttaCentral Bilara root texts

## 目录结构

```
data/                — 按藏经部拆分的 JSON 数据文件（巴利-英文/巴利-中文对照）
docs/                — GitHub Pages 静态站点
  index.html         — 搜索页面
  search_engine.js   — 客户端 BM25 检索引擎
  collections.json   — 藏经部元数据
  search_index_en_*.json / search_index_zh_*.json — 展示用分块数据（沿用原有格式，未变）
  word_index_en/ word_index_zh/  — BM25 倒排索引分片 + 词表 + 条目长度/所属藏经部
  bigram_index_zh/    — 中文字符二元组回退索引（仅中文，OOV安全网）
build_index.py        — 原始分块数据构建脚本
build_word_index.py   — BM25 索引构建脚本（依赖 build_index.py 的分块顺序）
```

## 本地开发

```bash
python3 -m http.server 8765 -d docs
# 访问 http://localhost:8765
```

### 重新生成检索索引

修改了语料或 `build_index.py` 的分块数据之后，需要重新生成 `docs/word_index_*` `docs/bigram_index_zh`：

```bash
pip install jieba opencc-python-reimplemented
python3 build_word_index.py
```

`entry_id` 与 `search_index_{lang}_N.json` 分块文件的对应关系（`chunk_idx = entry_id // 30000`）由 `build_index.py` 的分块顺序决定，两个脚本必须基于同一份 `build_english_index()`/`build_chinese_index()` 输出，不能单独重跑其中一个。

## 版权声明 · Copyright Notice

本项目（索引构建脚本、搜索网页、跨语言术语对照表等）由 **[Bayson-create](https://github.com/Bayson-create)** 设计开发，© 2026 Bayson-create。代码以 [MIT License](https://opensource.org/licenses/MIT) 开源；术语对照表等原创整理内容以 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 共享——欢迎自由使用、转载、修改、二次开发，但请注明出处并附本仓库链接。

本着"法布施胜一切施"（*Sabbadānaṃ dhammadānaṃ jināti*，《法句经》354 偈）的精神，作者不以此项目牟利，亦不限制非商业性的自由传播。

### 经文数据来源与引用

巴利三藏原文及其英、中译文并非本项目原创，引用时遵照各自授权：

- **巴利原文**：源自 [SuttaCentral](https://suttacentral.net) 维护的 Mahāsaṅgīti Tipiṭaka（佛历 2500 年结集本），以 [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) 公共领域方式发布。
- **英文译文**：由 SuttaCentral 上数百位译者（以 Bhikkhu Sujato、Bhikkhu Brahmali 等为主）翻译，published 与 unpublished 分支译文均以 CC0 1.0 发布。
- **中文译文**：主要采用莊春江（Zhuang Chunjiang）居士的譯註，经 SuttaCentral legacy HTML 接口收录、对外公开传播，敬请保留译者署名。

### 免责声明

本项目的关键词高亮、问答意图识别、术语提取等功能均为程序化检索辅助，不构成对经义的权威诠释；检索结果的取舍、排序仅依据文本匹配规则，不代表任何僧团或学术机构的立场，仅供学习参考，请以巴利原文及尊者译本为准。若发现数据有误或链接失效，欢迎通过 [GitHub Issues](https://github.com/Bayson-create/Early-Buddhist/issues) 指正。

---

**Copyright**: © 2026 [Bayson-create](https://github.com/Bayson-create). Code under [MIT License](https://opensource.org/licenses/MIT); original written content (cross-language glossary, categorization) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — attribution and a link back to this repo appreciated.

**Sutta data attribution**: Pāli root text & translations released under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) via [SuttaCentral](https://suttacentral.net). Chinese translations primarily by 莊春江 (Zhuang Chunjiang).
