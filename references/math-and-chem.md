# 公式与化学式（LaTeX）规范

> md2pdf 的公式引擎是**内联的 Temml**（覆盖 amsmath / amssymb 绝大多数命令），
> 输出 MathML 交给浏览器排版。它认不出的写法会退回内置的简易解析器，最差是原样显示命令名。

## 一、基本写法

| 场景 | 写法 |
|---|---|
| 行内公式 | `$E = mc^2$` |
| 独立成行 | `$$\int_0^1 x^2\,dx = \frac{1}{3}$$` |
| 等价写法 | `\(…\)` 行内、`\[…\]` 独立 |

独立成行的公式**必须自己占一行**（`$$` 在行首），才能居中排版。

## 二、绝对不要做

| 错误写法 | 为什么错 | 正确写法 |
|---|---|---|
| `x²`、`a³` | Unicode 上标在数学排版里字号/基线不对 | `$x^2$`、`$a^3$` |
| `√2`、`≤`、`≥`、`≠`、`→`、`∞`、`∑` | 与周围 LaTeX 混排会散架、符号对不齐 | `$\sqrt{2}$`、`$\le$`、`$\ne$`、`$\to$`、`$\infty$`、`$\sum$` |
| `H2SO4`（裸文本） | 不会变成下标 | `$\ce{H2SO4}$` 或 `$H_2SO_4$` |
| `\documentclass{article}`、`\usepackage{amsmath}`、`\begin{document}` | 这不是 LaTeX 编译器 | 直接写正文 |
| `\label{` / `\ref{` | 没有交叉引用系统 | 手写「见第 3 节」 |
| `\tag{1}` 写在行内 | 只支持块级公式 | 块级 `$$…\tag{1}$$` |

## 三、常用命令（均已验证可用）

**希腊字母**：`\alpha \beta \gamma \delta \theta \lambda \mu \pi \sigma \omega \Delta \Omega`，
变体 `\varepsilon \vartheta \varphi \varrho`。

**关系符**：`\le \ge \ne \approx \equiv \sim \simeq \cong \propto \ll \gg \prec \succ`，
进阶 `\lesssim \gtrsim \leqslant \geqslant \nleq \ngeq \ll \gg`。

**运算**：`\pm \mp \times \div \cdot \ast \oplus \ominus \otimes \odot \oslash \circ \bullet`，
逻辑 `\wedge \vee \neg \forall \exists \therefore \because`。

**大算符**：`\sum \prod \int \oint \iint \iiint \bigcup \bigcap \bigoplus`，
极限 `\lim \limsup \liminf \max \min \sup \inf`，`\arg\min`、`\operatorname{rank}`。

**箭头**：`\to \leftarrow \leftrightarrow \Rightarrow \Leftrightarrow \mapsto \hookrightarrow
\twoheadrightarrow \rightsquigarrow \leadsto \rightleftharpoons`，
带标签 `\xrightarrow{f}`、`\xleftarrow[下]{上}`。

**定界符**：`\left( \right)`、`\left[ \right]`、`\left\{ \right\}`、
`\left\langle \right\rangle`、`\lceil \rceil`、`\lfloor \rfloor`。

**结构**：`\frac \dfrac \tfrac`、`\sqrt{x}`、`\sqrt[3]{x}`、`\binom{n}{k}`、
`\begin{pmatrix} \end{pmatrix}`、`\begin{cases} \end{cases}`、`\begin{aligned} \end{aligned}`、
`\begin{array}{cc} \end{array}`、`\substack`。

**修饰**：`\hat \bar \vec \dot \ddot \tilde \widehat \widetilde \overline \underline`、
`\overbrace{…}^{…}`、`\underbrace{…}_{…}`、`\overset{!}{=}`、`\boxed{x}`、`\cancel{x}`。

**字体**：`\mathbb{R}`、`\mathcal{L}`、`\mathfrak{g}`、`\mathbf{v}`、`\mathrm{d}x`、
`\text{中文或说明}`、`\operatorname{rank}`。

**间距**：`\quad`(1em)、`\qquad`(2em)、`\,`、`\:`、`\;`、`\!`(负间距)、`\ `。

## 四、化学式 `\ce{}`

**不要自己拼下标**，交给 `\ce`：

```markdown
$\ce{H2SO4}$                      → H₂SO₄
$\ce{Ca(OH)2}$                    → Ca(OH)₂
$\ce{SO4^2-}$                     → SO₄²⁻
$\ce{NH4+}$                       → NH₄⁺
$\ce{2H2 + O2 -> 2H2O}$           → 配平系数 + 箭头
$\ce{N2(g) + 3H2(g) <=> 2NH3(g)}$ → 可逆箭头 + 状态
$\ce{2H2O2 ->[MnO2] 2H2O + O2}$   → 箭头上写条件
$\ce{CuSO4.5H2O}$                 → 水合物中点
$\ce{[Cu(NH3)4]^2+}$              → 配位方括号
$\ce{Fe2O3 + 3CO ->[高温] 2Fe + 3CO2}$
```

**支持的形态**：

| 写法 | 含义 |
|---|---|
| `H2O` | 数字紧跟元素/`)` 自动变下标 |
| `SO4^2-`、`Fe^{3+}`、`HCO3^-` | 电荷（`^` 后接数字和正负号，可加花括号） |
| `CH3COO-`、`NH4+` | 紧贴原子的正负号也会当电荷 |
| `2H2 + O2 -> 2H2O` | 行首数字是配平系数；`+` 是加号 |
| `->` `<-` `<=>` `-->` | 箭头；`<=>` 是可逆 |
| `->[条件]`、`<=>[条件]` | 箭头上写反应条件 |
| `(g)` `(l)` `(s)` `(aq)` | 状态符号（直立字体） |
| `CuSO4.5H2O`、`*` | 中点 |
| `[Cu(NH3)4]^2+` | 方括号、圆括号照常 |
| `^{14}C` | 前置上标（同位素） |

**不支持**（不是 mhchem 全家桶）：`\bond{}`、键线式、多行反应条件、
`\ce{A <=>[\text{条件}][\text{逆条件}] B}` 这类双向条件文字。遇到就用普通 LaTeX 手写。

**只在 md2pdf 里生效**：把 Markdown 贴到别的平台，`\ce{}` 不会被解析——那种场合请用纯 LaTeX 下标
（`$H_2SO_4$`、`$Ca^{2+}$`）。

## 五、单位 `\pu{}`

```markdown
$\pu{9.8 m/s^2}$
$\pu{1.0e-3 mol/L}$
$\pu{98 kJ/mol}$
```

只处理「数字 + 单位」；复杂单位组合建议直接写 `$\mathrm{kg\cdot m/s^2}$`。

## 六、价格与美元符号

行内 `$…$` 采用类似 Pandoc 的判定规则，避免把价格当公式：

- `$5-$10` → 保持原样（结尾 `$` 后跟数字，不认作公式）
- `$100 和 $200` → 保持原样
- 真要写美元金额，建议写成 `USD 100` 或退化成文本，别用单个 `$`

## 七、公式写砸了怎么排查

| 现象 | 排查 |
|---|---|
| 原样显示 `$x^2$` | 设置里「解析 LaTeX」被关了 |
| 红色报错块 | 命令不存在或括号不配对 |
| 显示成 `\foo` 文本 | 该命令引擎不认；换写法或用 `\text{}` 包起来 |
| 独立公式不居中 | `$$` 没在行首，被当成行内处理 |
| 上下标位置怪 | 没加花括号：`x^23` 是 x²·3，要写 `x^{23}` |
