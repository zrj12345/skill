---
name: chuhai-seo-keyword
description: "出海 / 谷歌 SEO 关键词决策与建站方法论，提炼自 Web.Cafe 出海seo资源分享V1.0 全库 1104 篇中文资料（2024-2026），并可按 id 回溯任意原文。用于判断一个关键词的数据好不好、是否值得基于它建站、如何找热词与新词、基础概念与术语解释，以及上站后的 GSC 诊断、内页内链、PSEO、变现算账。触发词包括 SEO、谷歌SEO、关键词、找词、挖词、热词、新词、长尾词、KD、KGR、KDRoi、搜索量、SERP、GSC、EMD、选词、建站、AdSense、keyword research、keyword difficulty。This skill should be used when the user asks to evaluate a keyword, decide whether to build a niche site around it, source trending or emerging keywords, explain SEO metrics, or apply the Web.Cafe SEO playbook."
agent_created: true
---

# 出海 SEO 关键词决策手册

## 目的

把本地资料库（1104 篇、约 211 万字）沉淀成可执行的判断方法：拿到一个词能给出「做 / 慎做 / 先内页验证 / 不做」的结论与依据；想找词能给出具体渠道和操作路径；问概念能用资料里的口径回答，而不是通用 SEO 科普。

知识来源：`出海seo资源分享V1.0`（飞书共享文件夹离线导出，含 `search-index.json` 全文索引）。脚本按目录名在工作区及其上级自动查找，也可用 `--kb` 或环境变量 `SEO_KB_ROOT` 指定。资料跨 2024-2026，含哥飞原文、社群成员整理、案例复盘，观点有演进也有冲突。

## 核心原则

1. **结论先行**：先给判断档位和一句话理由，再展开数据与依据。
2. **人肉 SERP 最高优先级**：任何工具指标都只是参考，前 10 结果的首页/内页构成、域名年龄、DR、页面质量才是最终依据 [id=47][id=940]。
3. **两个竞争维度都要看**：KGR 看竞争者**数量**（`allintitle 结果数 ÷ 月搜索量`），KD 看竞争者**质量**（前 10 的外链与权重），两者无正相关，只看一个必然被骗 [id=79]。
4. **算账再动手**：可达流量、外链成本、CPC/变现路径，任一算不过来就不要买域名 [id=47][id=893]。
5. **不确定就先内页试水**：先用老站做一个内页观察 GSC 出词与 ChatGPT 推荐流量，再决定是否注册域名单独建站 [id=76]。
6. **区分口径与作者**：区分日/月搜索量、工具数据当上限看；区分哥飞原文（放宽派）与新人整理 SOP（保守派），按站点阶段选择，并显式告知冲突 [id=106]。
7. **估算必须标估算**：KD→引荐域、位次 CTR、RPM 都是社群经验值，不是 Google 公式；上线后一律以 GSC 实测为准。
8. **可回溯**：关键结论标注 `[id=N]`，用 `kb_search.py --id N --all` 查原文；不凭记忆编造数字和来源 [id=106]。

## 工作流路由

| 用户意图 | 动作 |
| --- | --- |
| 判断某个关键词数据 / 能否建站 | 读 `references/07-playbooks.md` 第二节 + `references/03-evaluation.md`，按十步 SOP 采集数据；信息不足时明确列出需要补的字段，不臆测；能算时跑 `scripts/keyword_scorecard.py` |
| 找热词 / 新词 / 拓词 | 读 `references/02-sourcing.md`，按渠道清单给出组合路径与筛选条件 |
| 基础概念 / 术语 / 排名机制 | 读 `references/01-concepts.md`，用资料里的定义与口径坑作答 |
| 从词到站：结构、页面、内容、多语言、上线 | 读 `references/04-building.md` |
| 上站后：收录、GSC、外链、增长停滞、变现算账 | 读 `references/05-ops-money.md` |
| 找案例、避坑、工具选型、观点演进 | 读 `references/06-cases-tools.md` + `references/08-source-index.md` |
| 查某篇原文 / 某个说法出自哪里 | 跑 `scripts/kb_search.py`，输出 `[id=N]` 与标题 |

## 三个高频动作

### 1. 评估一个关键词

按 `references/07-playbooks.md` 第二节十步执行，至少覆盖：品牌/新闻词排除 → 搜索量与词形确认 → Trends 生命周期 → KGR/KD/KDRoi → SERP 前 10 人肉盘面 → 外链 ROI 与可达流量 → 商业价值与搜索意图 → 四档结论 → 下一步动作。

数据采集齐备时运行打分卡（可用 `--json` 取结构化结果）：

```bash
python scripts/keyword_scorecard.py --keyword "xxx" --volume-monthly 30000 \
  --kd 35 --kgr 0.18 --cpc 0.9 --serp-innerpages 7 --serp-homepages 3 \
  --dr-max 38 --trend rising --stage new
python scripts/keyword_scorecard.py --demo
```

按 `references/07-playbooks.md` 第六节的模板输出结论，包含数据、三档流量估算、风险、下一步、依据 id。

### 2. 挖掘热词 / 新词

从 `references/02-sourcing.md` 选 3~5 个渠道组合，写清「去哪 → 搜什么 → 筛什么 → 怎么验证是新词」。默认闭环：词根/赢家反推 → Semrush/Ahrefs 粗筛 → Google Trends 12 个月与 5 年 → `allintitle` 算 KGR → 人肉看 SERP → 词库表格 → 从站反查更多词。新词判断必须看趋势起势时间，且区分「产品新词」与「新闻热点词」[id=300][id=55]。

### 3. 解释概念

先给一句资料里的定义，再给「怎么用它做判断」，最后给常见误解。例如 KD 低但流量巨大，要解释 Ahrefs 只看前 10 外链、而站长可能故意用内页承接排名以规避整站惩罚 [id=52]。

## 检索原始资料库

```bash
python scripts/kb_search.py --query "KGR 阈值 搜索量" --limit 8
python scripts/kb_search.py --title "找词" --cat 哥飞小课堂
python scripts/kb_search.py --id 1037 --all
python scripts/kb_search.py --id 17 --path
python scripts/kb_search.py --list-cats
python scripts/kb_search.py --query "SERP" --json
```

默认只按目录名 `出海seo资源分享V1.0` 在工作区及其上级查找，不含任何绝对路径；需要指定别处时用 `--kb <目录>` 或环境变量 `SEO_KB_ROOT`。资料库移动后先确认能检索到，再回答涉及原文的问题。

**`[id=N]` 的回溯**：id 是 `search-index.json` 数组下标（0~1103）。用户问「id=17 是哪篇」或要引用出处时，用 `--id N --all` 读全文、`--id N --path` 拿本地 md/html 相对路径与原文链接；不跑脚本时查 `references/id-map.tsv`（全量 1104 行：id / 分类 / 标题 / 原文链接）。规则详见 `references/09-id-lookup.md`。回答时把标题和原文链接一并给出，不要只回一个编号。

## 回答规范

- 用中文、结论先行、少废话；能给方法就不给科普。
- 每个数字阈值标注来源 id 与时间口径；资料内部冲突时并列说明并给出按站点阶段的选择建议。
- 用户只给关键词、没给数据时：先做定性判断（品牌词/趋势/意图），再列出「需要你补充的字段清单」，不要编造搜索量和 KD。
- 涉及具体站点诊断时，先要 GSC 数据；没有数据就明确说明结论为假设。
- 不把「新人整理 SOP」的硬红线当成哥飞原文或官方规则；不把估算说成实测。
- 需要更细的内容时再打开对应 reference，避免一次性把全部资料塞进上下文。

## 参考资料

`references/01-concepts.md` 概念与排名机制 · `02-sourcing.md` 找词与热词 · `03-evaluation.md` 关键词判断与建站决策 · `04-building.md` 从词到站 · `05-ops-money.md` 运营与变现 · `06-cases-tools.md` 案例、避坑、工具 · `07-playbooks.md` 总纲、公式、阈值、模板 · `08-source-index.md` 主题→原文 id 索引与策略演进时间线 · `09-id-lookup.md` id 回溯说明 · `id-map.tsv` 全量 id→标题→原文链接对照表。
