# 09 · `[id=N]` 如何找到对应文章

## id 是什么

`[id=N]` 是本地资料库 `出海seo资源分享V1.0/search-index.json` 里**数组的下标（从 0 开始，范围 0~1103，共 1104 篇）**。每篇记录含：

| 字段 | 含义 |
| --- | --- |
| `n` | 文档标题（带日期前缀） |
| `d` | 分类 / 子目录名（根目录文档为空） |
| `f` | 该文档的文件夹名 |
| `h` | HTML 文件名（把 `.html` 换成 `.md` 即 Markdown 文件名） |
| `t` | 全文纯文本，首行通常含 `> 原文链接： https://new.web.cafe/...` |

因此 id 不是随机编号，也不是飞书文档 id；它只是导出索引的顺序号。**同一个标题可能对应多个 id**（飞书里有重名文档，导出时加了 `(2)`、`(3)` 区分），引用时按 id 回溯才准确。

## 三种查找方式

### 1. 看全文（最常用）

```bash
python scripts/kb_search.py --id 17 --all
```

输出标题、分类和整篇正文；不加 `--all` 只输出前 3 万字。正文首行就是原文链接。

### 2. 定位本地 md / html 文件（想在编辑器里打开）

```bash
python scripts/kb_search.py --id 17 --path
```

输出相对工作区根目录的路径 + 原文链接，例如 id=17：

```
id=17 | 哥飞小课堂 | 20251209 [2025.12.07]哥飞小课堂：GSC 的四级信号、谷歌为什么要给站长的网站流量、每一个关键词搜索结果都是一个排行榜 | Web.Cafe
md   : 出海seo资源分享V1.0\哥飞小课堂\20251209 [... _ Web.Cafe\20251209 [... _ Web.Cafe.md
html : 出海seo资源分享V1.0\哥飞小课堂\20251209 [... _ Web.Cafe\20251209 [... _ Web.Cafe.html
原文 : https://new.web.cafe/tutorial/detail/emi4bdks44
```

路径规则（全部 1104 篇已验证可定位）：

```
出海seo资源分享V1.0 / <d 分类> / <f 文件夹> / <h 去掉 .html 再加 .md>
```

`d` 为空的根目录文档则少一层分类。路径按目录名定位、不含盘符；资料库放在别处时用 `--kb <目录>` 或环境变量 `SEO_KB_ROOT` 指定。

### 3. 离线速查（不跑脚本）

`references/id-map.tsv` 是全量对照表，4 列用 Tab 分隔：`id`、`category`、`title`、`source_url`。1104 行，其中 1095 篇带原文链接。

```bash
grep -P "^17\t" references/id-map.tsv
# 17  哥飞小课堂  20251209 [2025.12.07]哥飞小课堂：GSC 的四级信号... | Web.Cafe  https://new.web.cafe/tutorial/detail/emi4bdks44
```

没有资料库副本时，用 `source_url` 直接打开 Web.Cafe 原文；有资料库时用 `--path` 打开本地 md/html。

## 其它入口

- `references/08-source-index.md`：按主题列出高相关文档的 id 与标题（不是全量，是全量的主题索引），并附策略演进时间线。
- `INDEX.md` / `INDEX.html`（资料库根目录）：按分类的全量标题索引，链接可直接打开本地文件，但没有 id 列。
- `scripts/kb_search.py --query "关键词"`：不知道 id 时按内容反查，结果里会给出 `[id=N]`，再回到上面三种方式。

## 注意

- id 由导出顺序决定，资料库重新导出后可能变化；若发现引用对不上，用标题在 `id-map.tsv` 里重新定位。
- 9 篇文档没有 `原文链接`（导出时正文或链接缺失），另 7 篇有附件/消息卡片导出缺失（见资料库 `README.md`），这些篇目以本地 md 为准。
- 引用格式统一写 `[id=N]`，便于 skills 之间互相校验，不要写成文档标题的简写。
