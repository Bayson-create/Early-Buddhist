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
