#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md2pdf 交付前自检：查 Markdown 在 md2pdf 里会不会渲染 / 打印出问题。

用法:
    python check_md.py 文档.md [更多.md ...]
    python check_md.py --strict 文档.md     # hint 也算失败（更适合接流水线）

退出码: 0 = 没发现 error；1 = 有 error（或 --strict 下有 hint）

只查「会让结果出错」的硬问题，不做风格说教。

内置排版指令也在检查范围内（必须单独成行；一行可以并排写几个）：
    [[gap:3]] / [[gap:20mm]]   留白，单位只认 mm 或省略（行）
    [[rules:3]]                答题横线，只按行数算
    [[pagebreak]]              强制分页，不能带参数
写错的形式工具会原样显示成文字（不会报错），所以这里是 error；
超出 200 行 / 500mm 会被静默截断（并排多个时按合计算），也按 error 报。

图片也在检查范围内（base64 内嵌是推荐写法）：
    本地路径（`![](图1.png)`、`![](C:\\…\\1.png)`）→ warn：浏览器读不到，打印 / 导出会丢图
    外链（`![](https://…)`）→ warn：离线打印不可靠
    `data:image/…;base64,…` → 校验 base64 能解码、文件头与 mime 对得上；单张过大给 hint
用 scripts/img2base64.py 把本地图片转成 base64 再写进 Markdown。

下划线也在检查范围内（md2pdf 里它是填空，不是加粗）：
    `__文字__` → hint：会被排成填空空线，加粗请用 `**文字**`
    整行只有 `___` → hint：会被当成分隔线；整行答题线用 `[[rules:N]]`
"""

import argparse
import base64
import binascii
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
# 工具只认这几种「单独成行」的写法（命令名大小写不敏感；一行可以并排写多个，
# 指令之间只允许空白，整行再夹正文就整行失效）：
#   [[gap:3]]      空 3 行（1 行 = 正文行高的 1.78em）
#   [[gap:20mm]]   空 20 毫米（可写小数）
#   [[rules:3]]    3 条答题横线（行距 1.9em）
#   [[pagebreak]]  强制分页（只在打印 / 导出 PDF 时换页；屏幕上只是虚线标记）
DIRECTIVE_MAX_LINES = 200      # 留白行数 / 横线条数上限，超了工具会截断
DIRECTIVE_MAX_MM = 500         # 留白毫米上限，超了工具会截断
DIRECTIVE_TOKEN_RE = re.compile(
    r'\[\[(gap|rules|pagebreak)(?::(\d+(?:\.\d+)?)(mm)?)?\]\]', re.I)
# 只在「像指令」的片段里查：命令名后面不以 ] 收尾的都算写错
DIRECTIVE_LOOK_RE = re.compile(r'\[\[\s*(gap|rules|pagebreak)\b[^\]]*\]\]', re.I)
QUOTE_PREFIX_RE = re.compile(r'^>\s?')
LIST_PREFIX_RE = re.compile(r'^(?:[-*+]|\d{1,9}[.)])[ \t]+')

# ---------------------------------------------------------------- 图片
# Markdown 行内图片：![alt](url "title")
IMAGE_RE = re.compile(r'!\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(?:\s+["\']([^"\']*)["\'])?\s*\)')
IMAGE_MAX_HINT = 1024 * 1024          # base64 后单张超过 1MB 给 hint
IMAGE_MAX_WARN = 3 * 1024 * 1024      # 超过 3MB 给 warn
DATA_IMAGE_MAGIC = {
    'image/png': (b'\x89PNG\r\n\x1a\n',),
    'image/jpeg': (b'\xff\xd8\xff',),
    'image/jpg': (b'\xff\xd8\xff',),
    'image/gif': (b'GIF87a', b'GIF89a'),
    'image/bmp': (b'BM',),
    'image/x-icon': (b'\x00\x00\x01\x00',),
    'image/vnd.microsoft.icon': (b'\x00\x00\x01\x00',),
}
CJK_RE = re.compile(r'[\u3400-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af]')
UNDERSCORE_LINE_RE = re.compile(r'^_{3,}[ \t]*$')
BOLD_CJK_RE = re.compile(r'__([^_\n]{1,60})__')


def image_magic_ok(mime, head):
    """文件头是不是这个 mime 该有的样子（防把改坏的 base64 当正常）。"""
    if mime == 'image/webp':
        return head[:4] == b'RIFF' and head[8:12] == b'WEBP'
    if mime == 'image/avif':
        return head[4:12] in (b'ftypavif', b'ftypavis')
    if mime == 'image/svg+xml':
        low = head.lower().lstrip()
        return b'<svg' in low or low.startswith(b'<?xml')
    magic = DATA_IMAGE_MAGIC.get(mime)
    return bool(magic and any(head.startswith(m) for m in magic))


def check_images(line, lineno, rep):
    """检查正文里的图片写法：本地路径 / 外链 / base64。

    推荐写法是 base64 内嵌（scripts/img2base64.py 生成）——本地路径浏览器读不到，
    外链离线打印不可靠。代码围栏里的内容由主循环跳过，行内代码里的示例被屏蔽。
    """
    if '![' not in line:
        return
    plain = mask_inline_code(line)
    for m in IMAGE_RE.finditer(plain):
        alt, target = m.group(1), m.group(2)
        if not alt.strip() and not rep.img_alt_hinted:
            rep.img_alt_hinted = True
            rep.add('hint', lineno, '图片建议写 alt 文字（图没出来 / 导出 HTML 时还能看出是什么）；这一条只提示一次')
        low = target.lower()
        if low.startswith('data:'):
            dm = re.match(r'^data:image/([a-z0-9.+-]+)((?:;[^,]*)?),(.*)$', target, re.I | re.S)
            if not dm:
                rep.add('warn', lineno,
                        '图片 data URI 写法不规范：写成 data:image/png;base64,…（SVG 是 image/svg+xml）')
                continue
            mime = 'image/' + dm.group(1).lower()
            params = (dm.group(2) or '').lower()
            payload = dm.group(3)
            if 'base64' not in params:
                rep.add('hint', lineno, '图片 data URI 建议用 base64：data:%s;base64,…' % mime)
                continue
            b64 = re.sub(r'\s+', '', payload)
            try:
                data = base64.b64decode(b64, validate=True)
            except (binascii.Error, ValueError):
                rep.add('error', lineno,
                        '图片 base64 解码失败（内容被截断 / 改坏了）：%s…' % m.group(0)[:32])
                continue
            if not data:
                rep.add('error', lineno, '图片 base64 是空的')
                continue
            if not image_magic_ok(mime, data[:32]):
                rep.add('warn', lineno,
                        '图片 data URI 声明的类型（%s）和实际文件头对不上，可能显示不出来' % mime)
            size = len(data)
            if size > IMAGE_MAX_WARN:
                rep.add('warn', lineno,
                        '单张图 %.1f MB，`.md` 会非常大；先用 --max-edge 1600 压一下' % (size / 1048576.0))
            elif size > IMAGE_MAX_HINT:
                rep.add('hint', lineno,
                        '单张图 %d KB，偏大；单张控制在 200—300KB（或用 --max-edge 1600）' % (size // 1024))
            continue
        if low.startswith(('http://', 'https://', '//')):
            rep.add('warn', lineno,
                    '外链图片在离线打印 / 导出里不可靠；下载后用 scripts/img2base64.py 转 base64 内嵌')
            continue
        if low.startswith('file:'):
            rep.add('warn', lineno,
                    'file: 图片在浏览器里读不到；用 scripts/img2base64.py 转 base64 内嵌')
            continue
        rep.add('warn', lineno,
                '本地路径图片（%s）浏览器读不到，打印 / 导出会丢图；'
                '用 scripts/img2base64.py 转 base64 内嵌（或在 md2pdf 里点「🖼 图片」重插）' % target[:60])

H1_RE = re.compile(r'^ {0,3}#{1,6}[ \t]+\S')
HEADING_RE = re.compile(r'^ {0,3}(#{1,6})[ \t]+\S')
TABLE_SEP_RE = re.compile(r'^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$')


class Report(object):
    def __init__(self):
        self.items = []          # (level, line, msg)
        self.img_alt_hinted = False   # 「图片没写 alt」只提醒一次，不刷屏

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
    所以判断「是否单独成行」要看剥掉容器记号之后剩下什么。
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


def split_directive_line(content):
    """整行只有指令（可并排多个，空白分隔）→ 返回 token 列表；否则 None。

    判定与工具一致：指令扫出来之后，指令之间和行首行尾都只能有空白；
    只要某个片段不是合法指令，或还夹着别的文字，整行就不生效。
    """
    toks, pos, n = [], 0, len(content)
    while pos < n:
        m = re.match(r'[ \t\u3000]*', content[pos:])
        pos += m.end()
        if pos >= n:
            break
        tm = DIRECTIVE_TOKEN_RE.match(content, pos)
        if not tm:
            return None
        toks.append(tm)
        pos = tm.end()
    return toks or None


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
    """检查内置排版指令：写法、单位、上限、是否单独成行（一行可并排多个）。

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

    toks = split_directive_line(content)
    if toks:
        total_lines = total_mm = total_rules = 0.0
        cap_reported = False
        for tm in toks:
            kind = tm.group(1).lower()
            arg = tm.group(2)
            has_mm = bool(tm.group(3))
            token = tm.group(0)
            if kind == 'pagebreak':
                if arg is not None:
                    rep.add('error', lineno,
                            '%s 带了参数，会被当普通文字显示；只写 [[pagebreak]]' % token)
                    cap_reported = True
                continue
            if arg is None:
                rep.add('error', lineno,
                        '%s 缺少数量，应写成 [[%s:数字]] 或 [[%s:数字mm]]'
                        % (token, kind, kind))
                cap_reported = True
                continue
            val = float(arg)
            if val <= 0:
                rep.add('error', lineno,
                        '%s 的数量必须大于 0；0 会被当普通文字显示' % token)
                cap_reported = True
                continue
            if kind == 'rules':
                if has_mm:
                    rep.add('error', lineno,
                            '%s 只按行数算，没有毫米单位；改成 [[rules:3]] 这种写法' % token)
                    cap_reported = True
                else:
                    total_rules += val
                    if val > DIRECTIVE_MAX_LINES:
                        rep.add('error', lineno,
                                '%s 超过上限 %d 条，工具会截断到上限'
                                % (token, DIRECTIVE_MAX_LINES))
                        cap_reported = True
                continue
            if has_mm:
                total_mm += val
                if val > DIRECTIVE_MAX_MM:
                    rep.add('error', lineno,
                            '%s 超过上限 %d mm，工具会截断到上限'
                            % (token, DIRECTIVE_MAX_MM))
                    cap_reported = True
            else:
                total_lines += val
                if val > DIRECTIVE_MAX_LINES:
                    rep.add('error', lineno,
                            '%s 超过上限 %d 行，工具会截断到上限'
                            % (token, DIRECTIVE_MAX_LINES))
                    cap_reported = True
        # 并排多个时工具按「一行合计」截断，合计超了也要报
        if not cap_reported:
            if total_lines > DIRECTIVE_MAX_LINES:
                rep.add('error', lineno,
                        '这一行留白合计 %.0f 行，超过上限 %d 行，工具会截断；拆成几行或减少数量'
                        % (total_lines, DIRECTIVE_MAX_LINES))
            elif total_mm > DIRECTIVE_MAX_MM:
                rep.add('error', lineno,
                        '这一行留白合计 %.1f mm，超过上限 %d mm，工具会截断'
                        % (total_mm, DIRECTIVE_MAX_MM))
            elif total_rules > DIRECTIVE_MAX_LINES:
                rep.add('error', lineno,
                        '这一行横线合计 %.0f 条，超过上限 %d 条，工具会截断'
                        % (total_rules, DIRECTIVE_MAX_LINES))
        return

    # 整行不是合法指令：先看是不是「并排写法里混了一个写错的」，否则就是「指令夹在正文里」
    looks = list(DIRECTIVE_LOOK_RE.finditer(content))
    for am in looks:
        tok = am.group(0)
        if DIRECTIVE_TOKEN_RE.fullmatch(tok):
            continue
        kind = am.group(1).lower()
        rep.add('error', lineno,
                '%s 会原样显示成文字：%s' % (tok, directive_problem(tok, kind)))
        return
    if looks:
        rep.add('hint', lineno,
                '排版指令必须单独成行：整行除了指令不能有别的文字'
                '（一行可以并排写多个，用空格隔开），否则会原样显示成文字')
        return


def check_underscores(line, lineno, rep):
    """下划线在 md2pdf 里是「填空」：连续 2 个以上会排成等宽答题空线，不再表示加粗。

    所以 `__文字__` 当加粗用会被排成两条空线；一整行只有 `___` 会被当成分隔线。
    代码围栏由主循环跳过，行内代码里的示例被屏蔽，不误报。
    """
    if '_' not in line:
        return
    plain = mask_inline_code(line)
    if '_' not in plain:
        return
    content = strip_container_prefix(plain)
    if UNDERSCORE_LINE_RE.match(content):
        rep.add('hint', lineno,
                '整行只有下划线会被当成分隔线；填空请和下划线所在文字写在同一行'
                '（如「答案：____」），整行答题线用 [[rules:N]]')
        return
    for m in BOLD_CJK_RE.finditer(content):
        inner = m.group(1)
        if CJK_RE.search(inner):
            rep.add('hint', lineno,
                    '`%s` 在中文里会排成填空空线（不是加粗）；加粗请写 **%s**'
                    % (m.group(0), inner))
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

        # 图片：本地路径 / 外链 / base64
        check_images(line, lineno, rep)

        # 下划线：填空空线（不是加粗）
        check_underscores(line, lineno, rep)

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
