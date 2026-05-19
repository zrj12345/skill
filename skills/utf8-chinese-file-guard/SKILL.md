---
name: utf8-chinese-file-guard
description: Guard UTF-8 Chinese text file edits across repositories. Use when modifying Chinese source files, docs, proto files, comments, or configs; fixing garbled text; doing batch replacements; or writing PowerShell 5.1 edits that may corrupt UTF-8 Chinese content. Covers safe read/write workflow, forbidden patterns, and post-edit validation.
---

# UTF-8 Chinese File Guard

处理中文文件修改、乱码修复、批量替换与 PowerShell 文本回写风险时使用这个 skill。

## 目标

- 保持文本文件统一为 UTF-8。
- 避免 Windows PowerShell 5.1 回写中文文件时引入乱码。
- 让中文注释、文档、协议、配置修改走可逆、可校验的安全流程。

## 先找仓库真源

- 优先查看仓库根目录的 `AGENTS.md`、`README.md`、`docs/**`、`scripts/**`
- 搜索编码治理相关约束，例如：
  - `text-encoding`
  - `UTF-8`
  - `Read-Utf8Text`
  - `Write-Utf8Text`
  - `check_text_encoding`
- 如果仓库已经提供统一脚本或 helper，优先复用，不要自创另一套回写方式

## Repo-Provided Scripts First

- 使用这些仓库脚本：
  - `scripts/check_text_encoding.py`
  - `scripts/repair_proto_comments.py`
  - `scripts/powershell/Utf8File.ps1`

## Bundled Scripts

- `scripts/check_text_encoding.py`
  - 批量修改中文文本、注释、协议或配置后执行
  - 默认检查当前工作目录；也可用 `--repo-root <path>` 指定目标仓库
- `scripts/repair_proto_comments.py`
  - 用于批量修复 `.proto` 文件中的乱码注释、异常机翻注释与可恢复 mojibake
- `scripts/powershell/Utf8File.ps1`
  - 在仓库没有现成 UTF-8 helper，且必须使用 Windows PowerShell 5.1 时复用

## 执行流程

1. 先确认目标文件不是生成文件；生成文件不直接手改。
2. 小范围修改优先使用 `apply_patch`，不要先写脚本扩大风险面。
3. 需要脚本化改动时，按以下优先级选择：
   - Python / Go / Node.js 显式 UTF-8 读写
   - `pwsh` 并显式指定 UTF-8
   - Windows PowerShell 5.1 下仅使用 `.NET` UTF-8 文件 API，或复用仓库已有的 UTF-8 helper
4. 批量替换前先做少量样本 dry run，再扩到全量文件。
5. 修改后运行仓库已有的编码检查脚本；如果没有，使用 `scripts/check_text_encoding.py`，再说明未执行自动校验的原因。

## 禁止做法

- 不要在 Windows PowerShell 5.1 中直接使用 `Get-Content` / `Set-Content` / `Add-Content` / `Out-File` 读写包含中文的 UTF-8 文件。
- 不要在 Windows PowerShell 5.1 中使用 `Get-Content -Raw` 读取 UTF-8 中文文本后，再用 `Set-Content -Encoding UTF8` 写回。
- 不要依赖控制台显示效果判断文件是否乱码；必须按 UTF-8 直接读取文件内容再判断。
- 不要对中文源码、协议、规范文件做不带编码约束的批量替换。
- 不要直接编辑生成文件；如必须同步，先修源文件再走生成流程。
- 不要在未人工校对前启用自动机翻注释修复。

## 安全模式

### 小范围修改

- 优先直接用 `apply_patch`。
- 改动包含中文时，尽量缩小 patch 范围，降低误伤面。

### Python 安全读写

```python
from pathlib import Path

path = Path("example.proto")
text = path.read_text(encoding="utf-8")
text = text.replace("old", "new")
path.write_text(text, encoding="utf-8", newline="\n")
```

### PowerShell 5.1 安全读写

```powershell
$path = Resolve-Path -LiteralPath $file
$content = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
$content = $content -replace 'old', 'new'
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($path, $content, $utf8NoBom)
```

如果需要复用现成 helper，优先加载 skill 自带的 `scripts/powershell/Utf8File.ps1`。

## 修复优先级

- 协议、源码中的乱码注释优先恢复为可读内容。
- Go 注释默认改为英文，除非仓库已有别的明确约定。
- `proto` 注释允许中文或英文，但必须可读。
- 低价值且无法可靠恢复的历史乱码草稿，可删除而不是继续带病保留。
- 如果生成文件出现乱码，先修正源文件，再重新生成。

## 交付检查

- 说明本次修改使用了哪种读写路径：`apply_patch`、Python、`pwsh` 或 `.NET` UTF-8 API / 仓库 helper。
- 如果做了批量替换，说明是否先做了 dry run。
- 如果仓库存在编码检查脚本，说明是否执行以及结果如何。
- 如果未执行自动编码校验，明确说明原因。
