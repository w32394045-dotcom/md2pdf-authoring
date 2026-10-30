# md2pdf-authoring — teach an AI to use md2pdf and to write Markdown that survives rendering

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Skill](https://img.shields.io/badge/type-agent%20skill-9cf)](SKILL.md)

**English** · [简体中文](README.zh-CN.md)

A **Skill** — instructions for an AI agent, plus two scripts (a linter and an image→base64 converter) — that solves two things:

1. **The agent knows how to drive [md2pdf](https://github.com/w32394045-dotcom/md2pdf)** —
   open, load, set up, print to PDF, export a standalone HTML; which step cannot be skipped.
2. **The agent knows how to write Markdown that renders and prints correctly** —
   maths in LaTeX (chemistry via `\ce`, units via `\pu`), figures in render fences (`svg` / `css` / `html`),
   tables that don't blow out the page; layout spacing via `[[gap:N]]`, answer lines via `[[rules:N]]`,
   forced page breaks via `[[pagebreak]]`; and a linter run before delivery.

> Without this, models still write Markdown — they just get the usual things wrong:
> `x²`/`√` instead of LaTeX, bare `H2SO4`, a nine-column table squeezed onto A4,
> asking for a picture and getting a code block, wrapping the whole `.md` in a fence so nothing renders,
> padding with blank lines that Markdown silently collapses, or inventing HTML for page breaks.

**Can't be bothered to install it?** Section "Install → Option 1" below has a prompt you can paste straight
into your agent (Claude Code / Codex / DSH / Cursor). It downloads, installs, and verifies itself.

## What's inside

```text
SKILL.md                              main instructions: workflow, hard rules, troubleshooting, checklist
references/markdown-cheatsheet.md     what this tool's Markdown subset actually supports (and what it doesn't)
references/math-and-chem.md           LaTeX conventions + \ce/\pu usage, limits, common mistakes
references/layout-and-print.md        A4 layout, SVG drawing rules, page breaks, print troubleshooting
scripts/check_md.py                   pre-delivery linter (stdlib only, no dependencies; also checks images)
scripts/img2base64.py                 image → base64 embedder (stdlib only; uses Pillow to downsize when available)
examples/sample-notes.md              an English positive example (with spacing / answer-line / break directives and footnotes)
examples/bad-example-caught.md        a deliberately broken file, to show what the linter catches (including a bad directive)
```

> The `examples/` files come in Chinese/English pairs; the linter's rules are language-agnostic.

## What's new in the companion tool (v2 / v3)

The Skill only covers *how to write*; these are the md2pdf features added this round that matter while writing,
already folded into `SKILL.md` wherever they affect a writing decision:

- **Built-in layout directives (v3)**: `[[gap:3]]` — 3 blank lines; `[[gap:20mm]]` — 20 mm of space;
  `[[rules:3]]` — 3 answer lines; `[[pagebreak]]` — forced page break. Each must sit on its own line
  (several may share one line, but no body text on that line); invalid forms show up as literal text;
  caps are 200 lines / rules and 500 mm.
- **Three footnote placements**: end of document / next to the reference (same page when printed) / both.
  Syntax is still a plain `[^1]`; the reader picks the placement in settings.
- **Per-page decorations**: author card (avatar + text; top / bottom / every page top / every page bottom) and
  a page info bar (once at the end / on every page, two independent switches). They hug the page edge when printed.
- **Backgrounds & avatars**: page background image (A4 / A5 / Letter / square / circle crop), background opacity,
  content-surface opacity; avatar upload, crop and reuse. Print needs "Background graphics" ticked in the print dialog.
- **Richer accent colour**: 7 presets + free colour wheel + `#RRGGBB` + "pick from image" + the 24 most recent colours.
- **File history**: autosaved after ~2.6 s of inactivity, up to 50 entries, with time / word count / size (IndexedDB, local only).
- **Images embedded as base64, with a converter**: `scripts/img2base64.py` turns local image files into
  Markdown with inline base64 (`--insert doc.md fig1.png` replaces `<!--img-->` placeholders), so the AI never
  has to copy megabytes of base64 into its context. Stdlib only; with Pillow installed, `--max-edge 1600`
  downsizes first. The toolbar’s “🖼 Image” button in md2pdf (pick / paste / drop) does the same thing and is
  fully compatible. Local paths (`![](fig1.png)`) and external links are unreliable — don’t use them.
- **Large documents fall back to IndexedDB**: once embedded images push the document past the localStorage quota,
  the text is stored in the local database instead, so a reload doesn’t lose it.
- **Settings export / import as JSON** (excludes background image, avatar, document images and the font library).
- **Rewritten built-in samples in 7 languages**, covering directives, footnotes, backgrounds, avatars and per-page decorations — usable as templates.

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
+ tools (scripts/check_md.py linter, scripts/img2base64.py image→base64 converter). It teaches an AI to use
md2pdf (a Markdown→PDF tool) correctly and to produce Markdown whose maths, chemistry, figures, images and
tables render and print correctly.

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
   b) the directory contains SKILL.md, references/ (three .md files), scripts/check_md.py and
      scripts/img2base64.py;
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
> Both traps are real — I hit them. After installing, check that `SKILL.md`, `references/` (3 markdown files),
> `scripts/check_md.py` and `examples/` are all there.

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
keep tables to 6 columns or fewer with a consistent column count, use [[gap:3]] or [[gap:20mm]] for spacing,
[[rules:3]] for answer lines and [[pagebreak]] for page breaks — each on its own line, never pad with blank lines,
write footnotes as [^1] and let the reader choose where they print, always tag code fences with a language,
and never use \usepackage / \begin{document} / \label. Self-check before handing it over.
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

# 2b. the image → base64 tool runs (printing --help is enough)
python ~/.dsh/skills/md2pdf-authoring/scripts/img2base64.py --help
#    try: python .../img2base64.py --insert doc.md fig1.png
#    (put <!--img--> placeholders in doc.md first; they are replaced with
#     ![fig1](data:image/png;base64,…))

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
- **layout directives**: own line (several may share one; caps count per line as a whole), valid syntax / unit / count,
  and caps (200 lines or rules, 500 mm) — a malformed directive is silently printed as text by the tool,
  so the linter reports it as an error
- tables wider than 6 columns, code lines over 100 characters, skipped heading levels
- **images**: local paths (`![](fig1.png)`) and external links → warnings (the browser cannot read them and
  offline printing is unreliable); `data:image/…;base64,…` → checks that the base64 decodes, that the file
  header matches the declared mime type, and hints when a single image is very large
- the legacy `<div class="page-break"></div>` is **not** flagged (still supported, no forced migration)

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
  L20   [error] [[gap:3px]] 会原样显示成文字：单位只认 mm（省略表示行数），`3px` 不是有效单位
  L26   [error] 这个代码围栏没有闭合（行尾缺 ``` 或 ~~~）
  L3    [warn] 标题层级跳级（H1 → H4），目录层级会错乱
  L10   [warn] <script> 会被过滤
  L12   [hint] Unicode 数学符号在公式里会散架，改用 LaTeX（$x^2$、$\le$、$\to$）（本行出现 ²√）
--------------------------------------------------------------
汇总：7 error, 2 warn, 1 hint

[FAIL] 有 7 处 error，先修完再交付。
```

(The report text is in Chinese; `--strict` only changes the exit code.)

## The image → base64 tool

Images in the Markdown have to be **base64-embedded** (`![fig1](data:image/png;base64,…)`) — a browser cannot
read a local path, and local paths break when the file is printed, exported or moved. This stdlib script does
the conversion:

```bash
# Recommended: put <!--img--> placeholders in the .md, then let the script fill them in
python scripts/img2base64.py --insert notes.md fig1.png fig2.jpg
#   → 已替换 2 个占位符（L5、L9）; no placeholders → appended at the end

# custom placeholder
python scripts/img2base64.py --insert notes.md --marker "[[IMG]]" fig1.png

# big photos: downsize to 1600 px on the long edge first (needs Pillow; otherwise embedded as-is)
python scripts/img2base64.py --max-edge 1600 --insert notes.md photo.jpg

# other outputs
python scripts/img2base64.py fig1.png          # stdout: Markdown snippet
python scripts/img2base64.py --uri logo.svg    # stdout: data URI
python scripts/img2base64.py --json fig1.png   # metadata only (no base64 payload)
python scripts/img2base64.py --out snippet.md fig1.png
```

- png / jpg / gif / webp / avif / bmp / svg / ico, detected by **file signature** (a wrong extension is fine).
- Why `--insert`: a multi-megabyte base64 string stays in the file instead of the model's context — copying it
  by hand always loses characters.
- Keep each embedded image at ≤ 300 KB (the script warns above 400 KB); `--max-edge 1600` ≈ 240 dpi on A4.
- The “🖼 Image” button in md2pdf is the same tool with a GUI (pick / paste / drop) and is fully compatible.

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
