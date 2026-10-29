#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md2pdf 交付前自检：查 Markdown 在 md2pdf 里会不会渲染 / 打印出问题。

用法:
    python check_md.py 文档.md [更多.md ...]
    python check_md.py --strict 文档.md     # hint 也算失败（更适合接流水线）

退出码: 0 = 没发现 error；1 = 有 error（或 --strict 下有 hint）

只查「会让结果出错」的硬问题，不做风格说教。

内置排版指令也在检查范围内（写法必须独占一行）：
    [[gap:3]] / [[gap:20mm]]   留白，单位只认 mm 或省略（行）
    [[rules:3]]                答题横线，只按行数算
    [[pagebreak]]              强制分页，不能带参数
写错的形式工具会原样显示成文字（不会报错），所以这里是 error；
超出 200 行 / 500mm 会被静默截断，也按 error 报。
"""

import os
import re
import sys

# ---------------------------------------------------------------- 规则常量

FENCE_RE = re.compile(r'^(\s{0,3})(`{3,}|~{3,})(.*)$')

# 渲染型围栏：内容会被真正渲染（所以里面的东西要更小心）
RENDER_LANGS = {'svg', 'css', 'html', 'render', 'render-svg', 'render-css', 'render-html'}

DANGEROUS = [
    (re.compile(r'<\s*script\b', re.I), '<script> 会被过滤'),
    (re.compile(r'\bon(click|error|load|mouseover|focus)\s*=', re.I), '事件属性会被过滤'),
    (re.compile(r'javascript\s*:', re.I), 'javascript: 伪协议会被过滤'),
    (re.compile(r'@import\b', re.I), '@import 会被过滤（样式不生效）'),
    (re.compile(r'url\(\s*[\'"]?(?!data:|#)', re.I), '外链 url() 会被过滤'),
]

DOC_LEVEL_TEX = [
    (re.compile(r'\\documentclass\b'), r'\documentclass 不是这个工具能编译的'),
    (re.compile(r'\\usepackage\b'), r'\usepackage 不支持（只用内置引擎）'),
    (re.compile(r'\\begin\s*\{\s*document\s*\}'), r'\begin{document} 不支持'),
    (re.compile(r'\\(label|ref|eqref)\s*\{'), r'交叉引用 \label / \ref 不支持，手写「见第 X 节」'),
    (re.compile(r'\\(input|include)\s*\{'), r'\input / \include 不支持'),
]

# Unicode 近似数学符号（在公式外出现时提示）
UNICODE_MATH = '²³¹⁰⁴⁵⁶⁷⁸⁹≤≥≠≈≢∞√∑∏∫∮→←↔⇒⇔∂∇∈∉⊂⊃∪∩'
UNICODE_HINT = 'Unicode 数学符号在公式里会散架，改用 LaTeX（$x^2$、$\\le$、$\\to$）'

# ---------------------------------------------------------------- 内置排版指令
# 工具只认这几种「独占一行」的写法（命令名大小写不敏感）：
#   [[gap:3]]      空 3 行（1 行 = 正文行高的 1.78em）
#   [[gap:20mm]]   空 20 毫米（可写小数）
#   [[rules:3]]    3 条答题横线（行距 1.9em）
#   [[pagebreak]]  强制分页（只在打印 / 导出 PDF 时换页；屏幕上只是虚线标记）
DIRECTIVE_MAX_LINES = 200      # 留白行数 / 横线条数上限，超了工具会截断
DIRECTIVE_MAX_MM = 500         # 留白毫米上限，超了工具会截断
DIRECTIVE_VALID_RE = re.compile(
    r'^ {0,3}\[\[(gap|rules|pagebreak)(?::(\d+(?:\.\d+)?)(mm)?)?\]\][ \t]*$', re.I)
# 只在「像指令」的片段里查：命令名后面不以 ] 收尾的都算写错
DIRECTIVE_LOOK_RE = re.compile(r'\[\[\s*(gap|rules|pagebreak)\b[^\]]*\]\]', re.I)
QUOTE_PREFIX_RE = re.compile(r'^>\s?')
LIST_PREFIX_RE = re.compile(r'^(?:[-*+]|\d{1,9}[.)])[ \t]+')

H1_RE = re.compile(r'^ {0,3}#{1,6}[ \t]+\S')
HEADING_RE = re.compile(r'^ {0,3}(#{1,6})[ \t]+\S')
TABLE_SEP_RE = re.compile(r'^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$')


class Report(object):
    def __init__(self):
        self.items = []          # (level, line, msg)

    def add(self, level, line, msg):
        self.items.append((level, line, msg))

    def count(self, level):
        return sum(1 for lv, _, _ in self.items if lv == level)

    @property
    def errors(self):
        return self.count('error')


def read_text(path):
    with open(path, 'rb') as f:
        raw = f.read()
    for enc in ('utf-8-sig', 'utf-8', 'gb18030'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', 'replace')


def mask_inline_code(line):
    """把行内代码的内容换成等长的占位符。

    为什么需要：文档里「讲」某个语法（比如说明 `\\usepackage` 不支持、
    `\\ce{` 要怎么写）不等于真的在用。之前没做这层屏蔽，README 讲 LaTeX 规范
    就被自己的脚本判成 6 处 error —— 典型的假阳性。
    """
    out = []
    in_code = False
    for ch in line:
        if ch == '`':
            in_code = not in_code
            out.append(ch)
            continue
        out.append('x' if in_code else ch)
    return ''.join(out)


def strip_container_prefix(line):
    """去掉引用块 / 列表记号，拿到容器里这一行的内容。

    指令在引用块和列表项里也生效（`> [[gap:2]]`、`- [[gap:2]]`），
    所以判断「是否独占一行」要看剥掉容器记号之后剩下什么。
    """
    s = line
    while True:
        t = s.lstrip(' \t')
        m = QUOTE_PREFIX_RE.match(t)
        if m:
            s = t[m.end():]
            continue
        m = LIST_PREFIX_RE.match(t)
        if m:
            s = t[m.end():]
            continue
        return t


def directive_problem(tok, kind):
    """给一个「像指令但写法不对」的片段，说明它错在哪。"""
    if kind == 'pagebreak':
        if tok[2:-2].strip().lower() == 'pagebreak':
            return '写法不规范（多余空格），只能写 [[pagebreak]]'
        return 'pagebreak 不接受参数，只能单独写 [[pagebreak]]'
    inner = tok[2:-2].strip()             # gap:3px
    rest = inner[len(kind):].lstrip()     # :3px
    if not rest:
        return '缺少数量，应写成 [[%s:数字]] 或 [[%s:数字mm]]' % (kind, kind)
    if not rest.startswith(':'):
        return '指令名后面要跟半角冒号，例如 [[%s:3]]' % kind
    arg = rest[1:].strip()
    if not arg:
        return '冒号后面缺少数字'
    if re.match(r'^\d+(?:\.\d+)?[A-Za-z]+$', arg):
        return '单位只认 mm（省略表示行数），`%s` 不是有效单位' % arg
    if not re.match(r'^\d', arg):
        return '数量必须是数字，不能是 `%s`' % arg
    return '写法不符合 [[%s:数字]] / [[%s:数字mm]]' % (kind, kind)


def check_directives(line, lineno, rep):
    """检查内置排版指令：写法、单位、上限、是否独占一行。

    代码围栏里的内容由主循环跳过（文档里讲语法不误报）；
    行内代码里的 `[[...]]` 会被 mask_inline_code 屏蔽，也不会误报。
    """
    if '[[' not in line:
        return
    plain = mask_inline_code(line)
    if '[[' not in plain:
        return
    # 缩进 4 格会被当成缩进代码块（原样显示），不算指令
    if (len(line) - len(line.lstrip(' ')) >= 4
            and strip_container_prefix(line) == line.lstrip(' ')):
        return
    content = strip_container_prefix(plain)

    m = DIRECTIVE_VALID_RE.match(content)
    if m:
        kind = m.group(1).lower()
        token = m.group(0).strip()
        if kind == 'pagebreak':
            if m.group(2) is not None:
                rep.add('error', lineno,
                        '%s 带了参数，会被当普通文字显示；只写 [[pagebreak]]' % token)
            return
        val = float(m.group(2))
        has_mm = bool(m.group(3))
        if val <= 0:
            rep.add('error', lineno,
                    '%s 的数量必须大于 0；0 会被当普通文字显示' % token)
            return
        if kind == 'rules':
            if has_mm:
                rep.add('error', lineno,
                        '%s 只按行数算，没有毫米单位；改成 [[rules:3]] 这种写法' % token)
            elif val > DIRECTIVE_MAX_LINES:
                rep.add('error', lineno,
                        '%s 超过上限 %d 条，工具会截断到上限'
                        % (token, DIRECTIVE_MAX_LINES))
            return
        limit, unit = (DIRECTIVE_MAX_MM, 'mm') if has_mm else (DIRECTIVE_MAX_LINES, '行')
        if val > limit:
            rep.add('error', lineno,
                    '%s 超过上限 %d %s，工具会截断到上限' % (token, limit, unit))
        return

    # 不是独立一行的合法写法：分「整行就是坏指令」和「指令混在正文里」两种情况
    for am in DIRECTIVE_LOOK_RE.finditer(content):
        tok = am.group(0)
        rest = (content[:am.start()] + content[am.end():]).strip()
        if rest:
            rep.add('hint', lineno,
                    '排版指令必须独占一行（前后不能有其他文字），否则会原样显示成文字')
            return
        kind = am.group(1).lower()
        rep.add('error', lineno,
                '%s 会原样显示成文字：%s' % (tok, directive_problem(tok, kind)))
        return


def split_row(line):
    """按未转义、且不在行内代码里的 | 切单元格。"""
    cells, buf, i, in_code = [], '', 0, False
    while i < len(line):
        ch = line[i]
        if ch == '\\' and i + 1 < len(line) and line[i + 1] == '|':
            buf += '|'
            i += 2
            continue
        if ch == '`':
            in_code = not in_code
            buf += ch
            i += 1
            continue
        if ch == '|' and not in_code:
            cells.append(buf)
            buf = ''
            i += 1
            continue
        buf += ch
        i += 1
    cells.append(buf)
    if cells and cells[0].strip() == '':
        cells = cells[1:]
    if cells and cells[-1].strip() == '':
        cells = cells[:-1]
    return cells


def scan(path):
    rep = Report()
    text = read_text(path)
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')

    in_fence = False
    fence_char = ''
    fence_len = 0
    fence_start = 0
    fence_lang = ''
    fence_long_line_reported = False
    h1_seen = False
    last_heading = 0
    i = 0
    n = len(lines)

    # ---------- 逐行扫描：围栏 / 表格 / 标题 / 危险内容 ----------
    while i < n:
        line = lines[i]
        lineno = i + 1
        m = FENCE_RE.match(line)

        if in_fence:
            # 结束判定：同字符、长度不短于开头、后面没有信息串
            if m and m.group(2)[0] == fence_char and len(m.group(2)) >= fence_len and not m.group(3).strip():
                in_fence = False
                i += 1
                continue
            if fence_lang in RENDER_LANGS:
                for rx, why in DANGEROUS:
                    if rx.search(line):
                        rep.add('warn', lineno, '渲染型围栏（%s）里 %s' % (fence_lang, why))
                        break
            if len(line) > 100 and not fence_long_line_reported:
                fence_long_line_reported = True
                rep.add('hint', lineno, '代码行超过 100 字符，打印时会折行，可读性下降')
            i += 1
            continue

        if m:
            in_fence = True
            fence_char = m.group(2)[0]
            fence_len = len(m.group(2))
            fence_start = lineno
            fence_lang = (m.group(3) or '').strip().split(' ')[0].lower()
            fence_long_line_reported = False
            if not fence_lang:
                rep.add('warn', lineno,
                        '代码围栏没标语言：不会高亮；想让它渲染要标 svg/css/html/render，想显示代码标 text')
            i += 1
            continue

        # 标题
        hm = HEADING_RE.match(line)
        if hm:
            lv = len(hm.group(1))
            if lv == 1:
                h1_seen = True
            if last_heading and lv > last_heading + 1:
                rep.add('warn', lineno, '标题层级跳级（H%d → H%d），目录层级会错乱' % (last_heading, lv))
            last_heading = lv
            i += 1
            continue

        # 内置排版指令：[[gap:…]] / [[rules:…]] / [[pagebreak]]
        check_directives(line, lineno, rep)

        # 表格
        if '|' in line and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1]) and '-' in lines[i + 1]:
            header = split_row(line)
            ncol = len(header)
            if ncol > 6:
                rep.add('warn', lineno, '表格 %d 列，A4 常规边距下会很挤，建议拆表或改列表' % ncol)
            j = i + 2
            while j < n and lines[j].strip() and '|' in lines[j]:
                got = len(split_row(lines[j]))
                if got != ncol:
                    rep.add('error', j + 1, '表格这一行有 %d 列，表头是 %d 列（缺格会让整表错位）' % (got, ncol))
                j += 1
            i = j
            continue

        # 危险内容（围栏外也查，正文里出现同样会被过滤）
        plain = mask_inline_code(line)

        for rx, why in DANGEROUS:
            if rx.search(plain):
                rep.add('warn', lineno, why)
                break

        # 文档级 LaTeX
        for rx, why in DOC_LEVEL_TEX:
            if rx.search(plain):
                rep.add('error', lineno, why)
                break

        # Unicode 数学符号（行内有 $ 时跳过，说明用户已经在用 LaTeX）
        if '$' not in plain:
            bad = [c for c in plain if c in UNICODE_MATH]
            if bad and not plain.lstrip().startswith('#'):
                rep.add('hint', lineno, '%s（本行出现 %s）' % (UNICODE_HINT, ''.join(sorted(set(bad))[:4])))

        i += 1

    if in_fence:
        rep.add('error', fence_start, '这个代码围栏没有闭合（行尾缺 ``` 或 ~~~）')

    if lines and lines[0].strip():
        first_nonblank = next((k for k, l in enumerate(lines) if l.strip()), 0)
        if not H1_RE.match(lines[first_nonblank]):
            rep.add('hint', first_nonblank + 1, '开头建议给一个 # 一级标题：md2pdf 会用它当文档标题和打印文件名')

    # ---------- 全文检查：公式与化学式配对 ----------
    # 只看「正文」：围栏里的代码、行内代码都屏蔽掉，否则讲语法的文档全会误报。
    # 单独跑一遍是为了保持行号 1:1 对齐（正文里的空行/表格行都留在原位）。
    prose = []
    _in, _ch, _len = False, '', 0
    for ln in lines:
        _m = FENCE_RE.match(ln)
        if _in:
            if _m and _m.group(2)[0] == _ch and len(_m.group(2)) >= _len and not _m.group(3).strip():
                _in = False
            prose.append('')
            continue
        if _m:
            _in, _ch, _len = True, _m.group(2)[0], len(_m.group(2))
            prose.append('')
            continue
        prose.append(mask_inline_code(ln))
    body = '\n'.join(prose)
    for token, pair in (('$$', '$$'), ('\\(', '\\)'), ('\\[', '\\]')):
        cnt = body.count(token)
        if token == '$$':
            if cnt % 2 != 0:
                rep.add('error', 0, '$$ 数量是奇数（%d），有一个块级公式没闭合' % cnt)
        else:
            close = body.count(pair)
            if cnt != close:
                rep.add('error', 0, '公式定界符不成对：%s ×%d，%s ×%d' % (token, cnt, pair, close))

    for macro in ('\\ce', '\\pu'):
        for mo in re.finditer(re.escape(macro) + r'\s*\{', body):
            start = body.index('{', mo.start())
            depth = 0
            closed = False
            for ch in body[start:]:
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        closed = True
                        break
            if not closed:
                linea = body[:mo.start()].count('\n') + 1
                rep.add('error', linea, '%s{ 的花括号没闭合' % macro)

    # ---------- 输出 ----------
    order = {'error': 0, 'warn': 1, 'hint': 2}
    rep.items.sort(key=lambda it: (order[it[0]], it[1]))
    print('=' * 62)
    print('文档：%s' % path)
    if not rep.items:
        print('  [OK] 没发现问题，可以交给 md2pdf。')
    for level, lineno, msg in rep.items:
        where = ('L%-4d' % lineno) if lineno else '     '
        print('  %s [%s] %s' % (where, level, msg))
    print('-' * 62)
    print('汇总：%d error, %d warn, %d hint'
          % (rep.count('error'), rep.count('warn'), rep.count('hint')))
    return rep


def _setup_stdout():
    """Windows 控制台默认是 GBK，中文和符号会报 UnicodeEncodeError。
    能改就改成 UTF-8；改不了就退化成「不抛异常」而不是崩掉。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            try:
                stream.reconfigure(errors='replace')
            except Exception:
                pass


def main(argv):
    _setup_stdout()
    strict = False
    files = []
    for a in argv[1:]:
        if a in ('-s', '--strict'):
            strict = True
        elif a in ('-h', '--help'):
            print(__doc__)
            return 0
        else:
            files.append(a)
    if not files:
        print(__doc__)
        return 2

    total_err = 0
    hinted = 0
    for p in files:
        if not os.path.isfile(p):
            print('找不到文件：%s' % p)
            total_err += 1
            continue
        rep = scan(p)
        total_err += rep.errors
        hinted += rep.count('hint')
        print('')

    if total_err:
        print('[FAIL] 有 %d 处 error，先修完再交付。' % total_err)
        return 1
    if strict and hinted:
        print('[FAIL] --strict 模式下 %d 处 hint 也算失败。' % hinted)
        return 1
    print('[OK] 通过。')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
