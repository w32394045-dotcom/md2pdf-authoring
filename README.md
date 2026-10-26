# md2pdf-authoring — 教 AI 用对 md2pdf、写对 Markdown 的通用 Skill

一个 **Skill**（给 AI agent 读的说明书 + 自检脚本），解决两件事：

1. **AI 知道怎么正确使用 [md2pdf](https://github.com/w32394045-dotcom/md2pdf)**——
   打开、载入、设置、打印另存为 PDF、导出独立 HTML，哪一步不能跳。
2. **AI 知道怎么写出「渲染正确、打印不出血」的 Markdown**——
   公式用 LaTeX（化学式 `\ce`、单位 `\pu`）、图形用渲染型围栏（`svg`/`css`/`html`）、
   表格不撑出纸外、分页不乱、交付前跑自检。

> 没有这个 Skill，模型也能写 Markdown，但最常见的翻车是：
> 公式写成 `x²`/`√`、化学式写成裸 `H2SO4`、表格 9 列挤成一团、
> 想画图却得到一段代码、把 `.md` 套进代码围栏导致表格全不渲染。

## 目录结构

```
SKILL.md                              主文件：流程、硬规范、故障对照表、自检清单
references/markdown-cheatsheet.md     这个工具到底认哪些 Markdown 写法（附不支持清单）
references/math-and-chem.md           LaTeX 规范 + \ce/\pu 用法与边界 + 常见错法
references/layout-and-print.md        A4 版式、SVG 画图规范、分页、打印排错
scripts/check_md.py                   交付前自检脚本（纯标准库，无依赖）
examples/示例-讲义.md                 一份能通过检查的正例
examples/反例-会被检查脚本逮住.md       一份故意写坏的反例（看脚本能查出什么）
```

## 安装

把整个目录放进你的 Skill 根目录即可（目录名保持 `md2pdf-authoring`）：

```bash
# 常见位置（按你的 agent 客户端选一个）
cp -r md2pdf-authoring ~/.dsh/skills/            # DeepSeek Harness（用户级）
cp -r md2pdf-authoring ./.dsh/skills/            # 只给当前仓库用
cp -r md2pdf-authoring ~/.claude/skills/         # Claude Code 风格目录
```

或者用 DSH 的安装命令：

```
skill_install source=<本仓库路径>/md2pdf-authoring
```

不需要安装也能用：直接把 `SKILL.md` 的内容贴进对话，它本身就是完整说明书。

## 自检脚本

```bash
python scripts/check_md.py 你的文档.md          # 查一份
python scripts/check_md.py --strict 文档.md     # 把 hint 也算失败（接流水线用）
```

查什么：

- 代码围栏是否闭合、是否漏标语言（漏标 → 不高亮，也没法触发渲染）
- `$$` / `\(` / `\[` 是否成对
- 表格每行列数是否与表头一致（缺格会让整表错位）
- 是否写了会被**安全过滤**的东西：`<script>`、`onclick=`、`@import`、外链 `url()`
- 是否用了 Unicode 近似数学符号（`x²`、`√2`、`≤`）——这些在公式里会散架
- `\ce{` / `\pu{` 花括号是否闭合
- 是否写了文档级 LaTeX（`\usepackage`、`\begin{document}`、`\label`/`\ref`）——不支持
- 表格是否超过 6 列、代码行是否超过 100 字符、标题是否跳级

跑 `examples/反例-会被检查脚本逮住.md` 的输出：

```
文档：examples/反例-会被检查脚本逮住.md
        [error] $$ 数量是奇数（1），有一个块级公式没闭合
  L7    [error] 表格这一行有 2 列，表头是 3 列（缺格会让整表错位）
  L8    [error] 表格这一行有 4 列，表头是 3 列（缺格会让整表错位）
  L14   [error] \usepackage 不支持（只用内置引擎）
  L16   [error] 这个代码围栏没有闭合（行尾缺 ``` 或 ~~~）
  L19   [error] \ce{ 的花括号没闭合
  L3    [warn] 标题层级跳级（H1 → H4），目录层级会错乱
  L10   [warn] <script> 会被过滤
  L12   [hint] Unicode 数学符号在公式里会散架，改用 LaTeX（$x^2$、$\le$、$\to$）
汇总：6 error, 2 warn, 1 hint
[FAIL] 有 6 处 error，先修完再交付。
```

## 适用 / 不适用

| 适用 | 不适用 |
|---|---|
| 把 Markdown 变 PDF / 打印稿 | 需要 `.docx` / `.pptx` / 可编辑 Excel |
| 出讲义、题包、技术文档、报告 | 多人协同编辑 |
| 需要公式、化学式、矢量图 | 需要联网渲染（MathJax CDN 之类） |
| 导出单文件 HTML 分享 | 需要 LaTeX 完整编译（宏包、交叉引用） |

## 配套工具

本 Skill 假定你手上有 **md2pdf**（离线单文件 Markdown → PDF，含内联 Temml 公式引擎）：

- 仓库：https://github.com/w32394045-dotcom/md2pdf
- 主站：https://md2pdf.xszx.cc.cd

工具本身是单文件，不需要安装；这个 Skill 只是让 AI 别把它用错、别把 Markdown 写坏。

## 许可证

[MIT](LICENSE) © 2026 w32394045-dotcom

随便用、随便改、随便分发，保留版权声明即可，不提供担保。
