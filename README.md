# md2pdf-authoring — teach an AI to use md2pdf and to write Markdown that survives rendering

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Skill](https://img.shields.io/badge/type-agent%20skill-9cf)](SKILL.md)

**English** · [简体中文](README.zh-CN.md)

A **Skill** — instructions for an AI agent, plus a linter — that solves two things:

1. **The agent knows how to drive [md2pdf](https://github.com/w32394045-dotcom/md2pdf)** —
   open, load, set up, print to PDF, export a standalone HTML; which step cannot be skipped.
2. **The agent knows how to write Markdown that renders and prints correctly** —
   maths in LaTeX (chemistry via `\ce`, units via `\pu`), figures in render fences (`svg` / `css` / `html`),
   tables that don't blow out the page, page breaks that behave, and a linter run before delivery.

> Without this, models still write Markdown — they just get the usual things wrong:
> `x²`/`√` instead of LaTeX, bare `H2SO4`, a nine-column table squeezed onto A4,
> asking for a picture and getting a code block, or wrapping the whole `.md` in a fence so nothing renders.

**Can't be bothered to install it?** Section "Install → Option 1" below has a prompt you can paste straight
into your agent (Claude Code / Codex / DSH / Cursor). It downloads, installs, and verifies itself.

## What's inside

```text
SKILL.md                              main instructions: workflow, hard rules, troubleshooting, checklist
references/markdown-cheatsheet.md     what this tool's Markdown subset actually supports (and what it doesn't)
references/math-and-chem.md           LaTeX conventions + \ce/\pu usage, limits, common mistakes
references/layout-and-print.md        A4 layout, SVG drawing rules, page breaks, print troubleshooting
scripts/check_md.py                   pre-delivery linter (stdlib only, no dependencies)
examples/sample-notes.md              a Chinese positive example that passes the linter
examples/bad-example-caught.md        a deliberately broken file, to show what the linter catches
```

> The `examples/` files are in Chinese on purpose (they double as a fixture for the Chinese README);
> the linter's rules are language-agnostic.

## Install

First, a clarification: **this repo is a Skill** — instructions for an AI, plus a checker script.
The thing that does the work is [md2pdf](https://github.com/w32394045-dotcom/md2pdf) (one HTML file).
Installing the skill just tells the AI about the rules. Three routes; pick whatever fits.

### Option 1 — paste this into your AI agent (easiest)

Works with any agent that supports skills: Claude Code, Codex, DeepSeek Harness, Cursor, Gemini CLI…
**Copy the whole block below.** It downloads the repo, puts it in the right place, and verifies the result.

```text
Please install a skill for me: md2pdf-authoring.

Source repository: https://github.com/w32394045-dotcom/md2pdf-authoring
What it is: an instruction file for AI agents (SKILL.md) + references (three markdown files in references/)
+ a linter (scripts/check_md.py). It teaches an AI to use md2pdf (a Markdown→PDF tool) correctly and to
produce Markdown whose maths, chemistry, figures and tables render and print correctly.

Please do the following, in order:

1. Download the repository to this machine, keeping the directory name md2pdf-authoring, and make sure
   SKILL.md exists inside it.
   Suggested command: git clone --depth 1 https://github.com/w32394045-dotcom/md2pdf-authoring.git
   (If git is unavailable, download the zip and extract it — keep the directory name.)

2. Move that whole directory into my skills root, choosing the one that matches your client:
   - DeepSeek Harness / generic: ~/.dsh/skills/md2pdf-authoring/
   - Claude Code style: ~/.claude/skills/md2pdf-authoring/
   - This project only: <project root>/.dsh/skills/md2pdf-authoring/
   If you have a skill_install / skill tool, prefer it — but copy references/ and scripts/ along with
   SKILL.md. Do not install it as a single flat markdown file: references/ and scripts/ would be lost and
   the paths inside SKILL.md would break.

3. After installing, verify three things and report the results to me:
   a) md2pdf-authoring shows up in your skill list and is valid;
   b) the directory contains SKILL.md, references/ (three .md files) and scripts/check_md.py;
   c) running `python scripts/check_md.py examples/sample-notes.md` prints a report (expect 0 errors, exit 0).

4. If any step fails, tell me exactly where: path missing, permission denied, client doesn't support skills,
   or only single-file install works — and give me the fallback (at minimum, let me paste SKILL.md as a
   system prompt).

Constraints: do not edit SKILL.md; do not change the script's logic; do not mix these files into my other
skill directories.
```

### Option 2 — do it manually (one command)

```bash
git clone --depth 1 https://github.com/w32394045-dotcom/md2pdf-authoring.git
cp -r md2pdf-authoring ~/.dsh/skills/        # DeepSeek Harness (user scope)
cp -r md2pdf-authoring ~/.claude/skills/     # Claude Code style
cp -r md2pdf-authoring ./.dsh/skills/        # this project only
```

With a skill installer tool:

```text
skill_install source=<path to this repo>/md2pdf-authoring scope=user
```

> ⚠️ Two traps: **don't copy only SKILL.md** (lose `references/` and `scripts/`, and every path inside breaks),
> and **don't install it as a flat file** (it becomes `skills/md2pdf-authoring.md` with the same loss).
> Both traps are real — I hit them. After installing, check that there are 5 files.

### Option 3 — your AI has no skill mechanism (web ChatGPT / Kimi / Doubao / Tongyi …)

No `skills` directory, no install support — then don't install anything, just hand the content over.
Three ways, easiest first:

**3.1 Send the file**

Attach or drop `SKILL.md` (or the whole zip) into the chat, then say:

```text
This is a writing spec for AI (a Skill). Read the SKILL.md inside.
From now on, when you help me write or edit Markdown, follow it strictly:
maths in LaTeX, chemistry via \ce, figures via svg/css/html render fences, tables with at most 6 columns,
and run its checklist before you hand anything back.
If you can also read the files in references/, consult them when needed.
```

- Most web assistants accept drag-and-drop, paste-as-file, or a paperclip upload.
- Sending the whole repo (zip / folder) is better: `references/` and `scripts/` come along.
- Caveat: **an uploaded file is treated as reference material, not as rules** — you must say "follow it",
  otherwise the model may ignore it.

**3.2 Paste the content**

Open [`SKILL.md`](SKILL.md), copy the whole text into the chat (including the `---` frontmatter), or store it
under *system prompt / custom instructions / project knowledge* so new chats pick it up automatically.
When you need maths, chemistry, figures or troubleshooting, paste the matching reference file too:

| File | Covers |
|---|---|
| `references/math-and-chem.md` | formulas, `\ce`, `\pu`, common mistakes |
| `references/layout-and-print.md` | A4 layout, SVG drawing, page breaks, print fixes |
| `references/markdown-cheatsheet.md` | what this tool supports / does not support |

**3.3 One-line version**

If you don't want to paste 12 KB, this sentence already gets most of the benefit:

```text
Whenever you write Markdown meant for PDF or print: use LaTeX for all maths ($…$ / $$…$$),
write chemistry as \ce{H2SO4}, never use Unicode approximations like x² √ ≤ →, draw figures with
```svg / ```css / ```html fences (SVG needs viewBox, explicit font-size, colours for white paper),
keep tables to 6 columns or fewer with a consistent column count, use <div class="page-break"></div>
for page breaks, always tag code fences with a language, and never use \usepackage / \begin{document} /
\label. Self-check before handing it over.
```

Expect **80–90% of the benefit**. The cost: it does not trigger automatically (remind it, or say "follow the
md2pdf rules"), it eats context (SKILL.md ≈ 12 KB, all three references ≈ 26 KB), and long attachments may be
truncated or only indexed — if the model ignores the spec, paste the key paragraphs again.

### Verify it actually works

```bash
# 1. files are there
ls ~/.dsh/skills/md2pdf-authoring/
#    expect: SKILL.md  references/  scripts/

# 2. the linter runs
python ~/.dsh/skills/md2pdf-authoring/scripts/check_md.py \
       ~/.dsh/skills/md2pdf-authoring/examples/sample-notes.md
#    expect: 0 errors, 0 warnings, 0 hints / [OK]

# 3. ask the AI a test question — correct answers show the spec loaded:
#    "Write a short Markdown snippet with a quadratic equation and a chemical equation, md2pdf-style"
#    good sign: $…$ maths, \ce{} chemistry, no x² / √ / ≤
```

### Update / uninstall

```bash
cd md2pdf-authoring && git pull          # update
rm -rf ~/.dsh/skills/md2pdf-authoring    # uninstall (just delete the directory)
```

## The linter

```bash
python scripts/check_md.py your-doc.md          # one file
python scripts/check_md.py --strict your-doc.md # hints count as failures (CI-friendly)
```

What it checks:

- fences closed, and every fence tagged with a language (untagged → no highlighting, no rendering)
- `$$` / `\(` / `\[` balance
- table rows whose column count differs from the header (a missing cell shifts the whole table)
- things that get **sanitised away**: `<script>`, `onclick=`, `@import`, external `url()`
- Unicode maths approximations (`x²`, `√2`, `≤`) — they fall apart inside formulas
- unbalanced `\ce{` / `\pu{` braces
- document-level LaTeX that is not supported (`\usepackage`, `\begin{document}`, `\label`/`\ref`)
- tables wider than 6 columns, code lines over 100 characters, skipped heading levels

It does **not** fire on documentation: code fences and inline code are masked before checking, so a file that
*explains* `\ce{` or `\usepackage` is not flagged (that false positive existed once; it is fixed).

Real output for `examples/bad-example-caught.md`:

```text
==============================================================
文档：examples/bad-example-caught.md
        [error] $$ 数量是奇数（1），有一个块级公式没闭合
  L7    [error] 表格这一行有 2 列，表头是 3 列（缺格会让整表错位）
  L8    [error] 表格这一行有 4 列，表头是 3 列（缺格会让整表错位）
  L14   [error] \usepackage 不支持（只用内置引擎）
  L16   [error] \ce{ 的花括号没闭合
  L22   [error] 这个代码围栏没有闭合（行尾缺 ``` 或 ~~~）
  L3    [warn] 标题层级跳级（H1 → H4），目录层级会错乱
  L10   [warn] <script> 会被过滤
  L12   [hint] Unicode 数学符号在公式里会散架，改用 LaTeX（$x^2$、$\le$、$\to$）（本行出现 ²√）
--------------------------------------------------------------
汇总：6 error, 2 warn, 1 hint

[FAIL] 有 6 处 error，先修完再交付。
```

(The report text is in Chinese; `--strict` only changes the exit code.)

## Good fit / not a fit

| Good fit | Not a fit |
|---|---|
| Markdown → PDF / print output | `.docx` / `.pptx` / editable Excel |
| Handouts, problem sets, technical notes, reports | Multi-user collaborative editing |
| Documents with maths, chemistry, vector figures | Anything needing CDN rendering (MathJax etc.) |
| Sharing a single self-contained HTML file | Full LaTeX compilation (packages, cross-references) |

## Companion tool

This Skill assumes you have **md2pdf** (offline single-file Markdown → PDF, with an inlined Temml engine):

- repo: https://github.com/w32394045-dotcom/md2pdf
- primary site: https://md2pdf.xszx.cc.cd

The tool itself is one file and needs no install; the Skill just stops the AI from using it wrongly and from
writing Markdown that breaks.

## Licence

[MIT](LICENSE) © 2026 w32394045-dotcom

Use it, change it, redistribute it — keep the copyright notice. No warranty.
