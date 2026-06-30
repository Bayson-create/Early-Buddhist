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

### 上座部视角：法非私产

在上座部佛教传统中，佛陀的教导（**Buddhavacana**，佛语）历经口诵结集（saṅgāyana）二千五百余年，由历代僧团共同护持、传诵、抄写，最终结集为巴利三藏（Tipiṭaka）。这些教法的本质是"**法布施**"（dhammadāna）——《法句经》第 354 偈言："一切布施中，法施为最上"（*Sabbadānaṃ dhammadānaṃ jināti*）。佛语本身不属于任何个人、译者或机构的私有财产，而是历代僧俗共同护持、自由流通的共同遗产。

基于这一立场，本项目所索引的经文数据来源与授权如下：

- **巴利原文**（Tipiṭaka root text）：源自 [SuttaCentral](https://suttacentral.net) 维护的 Mahāsaṅgīti Tipiṭaka（佛历 2500 年结集本），以 [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) 公共领域贡献方式发布，不设权利保留。
- **英文译文**：由 SuttaCentral 上数百位译者（以 Bhikkhu Sujato、Bhikkhu Brahmali 等为主）翻译，published 与 unpublished 分支译文均以 CC0 1.0 发布，译者明确放弃专属权利，使译文如同原典一样自由流通。
- **中文译文**：主要采用莊春江（Zhuang Chunjiang）居士的譯註，经 SuttaCentral legacy HTML 接口收录、对外公开传播；本着法布施精神，鼓励非商业性自由引用与转载，敬请保留译者署名以志感念。

本项目（索引构建脚本、搜索网页、跨语言术语对照表等）由编者原创整理编纂，同样以法供养的精神向大众免费开放，欢迎自由使用、转载、修改、二次开发，无需另行授权；若用于学术研究或公开传播，敬请保留对原始译者与 [SuttaCentral](https://suttacentral.net) 的署名，以示对历代结集者、译经者的尊重与感念。

### 免责声明

本项目的关键词高亮、问答意图识别、术语提取等功能均为程序化检索辅助，不构成对经义的权威诠释；检索结果的取舍、排序仅依据文本匹配规则，不代表任何僧团或学术机构的立场。读者应以巴利原文及尊者译本为准，并以闻、思、修次第如理作意（yoniso manasikāra）。若发现数据有误或链接失效，欢迎通过 [GitHub Issues](https://github.com/Bayson-create/Early-Buddhist/issues) 指正。

### 功德回向

愿以此网站编纂、校对、修订之功德，回向一切有情，愿正法久住，愿众生离苦得乐，证得涅槃。

*Idaṁ me puññaṁ āsavakkhayāvahaṁ hotu — 愿此功德，导向诸漏灭尽。*

---

**Attribution**: Pāli root text & translations released under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) via [SuttaCentral](https://suttacentral.net). Chinese translations primarily by 莊春江 (Zhuang Chunjiang). This project's original curation (search index, cross-language glossary, code) is shared freely in the spirit of *dhammadāna* — the gift of the Dhamma, said to excel all other gifts (Dhp 354).
