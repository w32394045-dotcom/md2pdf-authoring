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

**不知道怎么装？** 下面「安装 → 方式一」有一段现成的提示词，**整段复制给你的 AI agent**
（Claude Code / Codex / DSH / Cursor 都行），它自己下载、放到正确位置、装完还会自验。

## 目录结构

```text
SKILL.md                              主文件：流程、硬规范、故障对照表、自检清单
references/markdown-cheatsheet.md     这个工具到底认哪些 Markdown 写法（附不支持清单）
references/math-and-chem.md           LaTeX 规范 + \ce/\pu 用法与边界 + 常见错法
references/layout-and-print.md        A4 版式、SVG 画图规范、分页、打印排错
scripts/check_md.py                   交付前自检脚本（纯标准库，无依赖）
examples/示例-讲义.md                 一份能通过检查的正例
examples/反例-会被检查脚本逮住.md       一份故意写坏的反例（看脚本能查出什么）
```

## 安装

先说清楚：**这个仓库是「Skill」**——给 AI 读的说明书（`SKILL.md`）+ 参考资料 + 一个自检脚本，
不是双击就用的软件。真正干活的是配套工具 [md2pdf](https://github.com/w32394045-dotcom/md2pdf)（一个 HTML 文件）。

装它 = 让 AI 知道这些规范。三条路，按你手上有什么挑一条。

### 方式一：把下面这段直接发给你的 AI agent（推荐，最省事）

支持 Skill 的客户端都行：Claude Code、Codex、DeepSeek Harness、Cursor、Gemini CLI……
**把下面整段复制过去**，它会自己下载、放对位置、装完还会自验并告诉你结果。

```text
请帮我安装一个 Skill：md2pdf-authoring。

来源仓库：https://github.com/w32394045-dotcom/md2pdf-authoring
它是什么：一份给 AI 读的说明书（SKILL.md）+ 参考资料（references/ 三个 md）+
自检脚本（scripts/check_md.py）。作用是教 AI 正确使用 md2pdf（Markdown→PDF 工具），
并写出「公式、化学式、图表都渲染正确、打印不出血」的 Markdown。

请按顺序执行：

1. 把仓库下载到本机，目录名保持 md2pdf-authoring，且目录里必须有 SKILL.md。
   参考命令：git clone --depth 1 https://github.com/w32394045-dotcom/md2pdf-authoring.git
   （没有 git 就下载 zip 解压，同样保留目录名）

2. 把这个目录整体放进我的 Skill 根目录，按你所在客户端挑一个：
   - DeepSeek Harness / 通用：~/.dsh/skills/md2pdf-authoring/
   - Claude Code 风格：~/.claude/skills/md2pdf-authoring/
   - 只给当前项目用：<项目根>/.dsh/skills/md2pdf-authoring/
   如果你有 skill_install / skill 安装工具，优先用它，但要注意：
   必须连 references/ 和 scripts/ 一起复制，不要只装 SKILL.md。
   也不要把它压成一个平铺的 md 文件（那样 references/ 和 scripts/ 会丢，脚本路径就废了）。

3. 装完做三项验证，并把结果告诉我：
   a) 你的 Skill 列表里能看到 md2pdf-authoring，状态正常；
   b) 目录里有 SKILL.md、references/（3 个 md）、scripts/check_md.py；
   c) 运行 python scripts/check_md.py examples/示例-讲义.md，能打印检查结果
      （预期 0 error 并退出码 0）。

4. 如果任何一步失败，告诉我卡在哪：路径不存在、没权限、客户端不支持 Skill、
   或者只能装单文件——并给出退路（至少让我能把 SKILL.md 当系统提示词用）。

约束：不要修改 SKILL.md 的内容；不要改脚本逻辑；不要把这个仓库的文件混进我别的 Skill 目录。
```

### 方式二：手动装（一条命令）

把整个目录放进 Skill 根目录，**目录名保持 `md2pdf-authoring`**：

```bash
git clone --depth 1 https://github.com/w32394045-dotcom/md2pdf-authoring.git
cp -r md2pdf-authoring ~/.dsh/skills/        # DeepSeek Harness（用户级）
cp -r md2pdf-authoring ~/.claude/skills/     # Claude Code 风格
cp -r md2pdf-authoring ./.dsh/skills/        # 只给当前仓库用
```

用 DSH 的安装工具则：

```text
skill_install source=<本仓库路径>/md2pdf-authoring scope=user
```

> ⚠️ 两个坑：**别只复制 SKILL.md**（`references/`、`scripts/` 一丢，说明书里的路径全失效）；
> **别装成平铺单文件**（会变成 `skills/md2pdf-authoring.md`，资源同样丢失）。
> 这两个坑我都踩过——现在目录里 `SKILL.md` 是 bundle 形态，装完确认有 5 个文件。

### 方式三：AI 软件没有 Skill 机制（网页版 ChatGPT / 豆包 / Kimi / 通义 等）

没有 `skills` 目录、也不支持安装 Skill 的客户端，**根本不用装**——把内容直接给它就行。
三种给法，从省事到最省事：

**3.1 直接发文件（最省事）**

把 `SKILL.md`（或整份 zip）**作为附件上传 / 拖进对话框**，然后说一句：

```text
这是一个给 AI 用的写作规范（Skill）。请读里面的 SKILL.md，
接下来帮我写/改 Markdown 文档时严格按它的规范来（公式用 LaTeX、化学式用 \ce、
图形用 svg/css/html 渲染型围栏、表格列数≤6、交付前按它的清单自检）。
如果你还能读 references/ 里的文件，需要时自己去看。
```

- 大多数网页版都支持拖文件、粘贴文件、或点回形针上传。
- 能一次发整个仓库（zip / 拖文件夹）更好——`references/` 和 `scripts/` 都在里面，AI 需要时自己去读。
- 注意：**文件会被当成"参考资料"而不是"规则"**，所以要在那句话里明确「按它来写」，
  光上传不说，AI 不一定会遵守。

**3.2 直接贴内容（最通用，什么软件都行）**

打开仓库里的 [`SKILL.md`](SKILL.md)，把**全文复制**进对话框发出去
（包括开头 `---` 之间的 name / description）。习惯的话就存到软件的
「**系统提示词 / 自定义指令 / 项目知识库 / Agent 配置**」里，之后新建会话自动带上。

需要公式、化学式、画图或排错时，再把 `references/` 里对应的那一个 md 也贴进来：

| 贴哪个 | 管什么 |
|---|---|
| `references/math-and-chem.md` | 公式、`\ce` 化学式、`\pu` 单位、常见错法 |
| `references/layout-and-print.md` | A4 版式、SVG 画图、分页、打印排错 |
| `references/markdown-cheatsheet.md` | 这个工具支持/不支持哪些 Markdown 写法 |

**3.3 只贴一句话版**

懒得贴全文时，发这一句也能拿到大部分效果：

```text
以后帮我写 Markdown（要转 PDF/打印的）时按这些规矩来：
公式一律 LaTeX（$…$ / $$…$$），化学式用 \ce{H2SO4} 这种写法，禁止用 x² √ ≤ → 这类 Unicode 近似；
画图用 ```svg / ```css / ```html 围栏（SVG 要带 viewBox、文字给 font-size、白底配色）；
表格列数 ≤ 6 且每行列数一致；需要分页用 <div class="page-break"></div>；
代码围栏必须标语言；不要写 \usepackage / \begin{document} / \label 这类 LaTeX 文档级命令；
写完先自检一遍再给我。
```

这样能得到**八成到九成的效果**，代价有两个：

- 它不会**自动触发**——每次要说明「按 md2pdf 规范来写」，或在会话开头提醒一次；
- 上下文占用变长（SKILL.md 约 12KB，三份 reference 全贴约 26KB）。
- 附件方式还有个坑：**长文件可能被截断**，或用「文件检索」只索引摘要；感觉它没按规范来，
  就把关键段落单独再贴一遍。

### 装完怎么验证真的生效

```bash
# 1. 文件都在
ls ~/.dsh/skills/md2pdf-authoring/
#    期望看到 SKILL.md  references/  scripts/

# 2. 脚本能跑
python ~/.dsh/skills/md2pdf-authoring/scripts/check_md.py \
       ~/.dsh/skills/md2pdf-authoring/examples/示例-讲义.md
#    期望：汇总 0 error, 0 warn, 0 hint / [OK] 通过

# 3. 问 AI 一句测试题（能答对说明规范已加载）
#    「写一个含二元一次方程组和化学方程式的 Markdown 小片段，按 md2pdf 规范来」
#    正确表现：公式用 $…$、化学式用 \ce{}、不用 x² / √ / ≤ 这类 Unicode 近似
```

### 更新与卸载

```bash
cd md2pdf-authoring && git pull          # 更新
rm -rf ~/.dsh/skills/md2pdf-authoring    # 卸载（就是删目录）
```


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

**讲过不误报**：围栏里的代码和行内代码会被屏蔽，所以「文档里教别人怎么写 `\ce{`
或者说明 `\usepackage` 不支持」不会把自己判成错误（这个误报我踩过，已经修了）。

跑 `examples/反例-会被检查脚本逮住.md` 的真实输出：

```text
==============================================================
文档：examples/反例-会被检查脚本逮住.md
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
