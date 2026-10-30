#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把本地图片转成 base64 内嵌进 Markdown（给 md2pdf 用，纯标准库）。

为什么需要它：浏览器读不到 `C:\\…\\图1.png` 这种本地路径，`![](图1.png)` 在 md2pdf
里会显示成破图；而 base64（`data:image/png;base64,…`）直接写在 `.md` 里，打印、
导出 HTML、换电脑、发给别人都不会丢图。md2pdf 顶栏的「🖼 图片」按钮做的是同一件事，
这个脚本是给「直接产出 .md 文件」的场景用的——AI 不需要把几 MB 的 base64 读进上下文。

用法:
    # 1) 最省事（推荐给 AI）：先在 .md 里放占位符 <!--img-->，再插入
    python img2base64.py --insert 讲义.md 图1.png 图2.jpg
    #    · 有几个 <!--img--> 就逐个替换；没有占位符就追加到文末
    #    · 也可以 --marker "[[图片]]" 自定义占位符

    # 2) 只拿 Markdown 片段（stdout 只有片段，提示信息走 stderr）
    python img2base64.py 图1.png
    #    输出：![图1](data:image/png;base64,iVBORw0KGgo…)

    # 3) 只要 data URI（自己拼 HTML / CSS）
    python img2base64.py --uri logo.svg

    # 4) 机器可读（不含 base64 全文，只给元数据）
    python img2base64.py --json 图1.png 图2.png

    # 5) 先压一下再嵌（需要 Pillow；没装就原样嵌入并提示）
    python img2base64.py --max-edge 1600 --quality 86 --insert 讲义.md 照片.jpg

    # 6) 片段写到单独文件
    python img2base64.py --out 图片片段.md 图1.png

支持: png / jpg / gif / webp / avif / bmp / svg / ico（按文件头判断，不看扩展名）。
退出码: 0 = 全部成功；1 = 有文件读不了 / 不是图片；2 = 参数错误。

注意:
    · 单张图 base64 会比原文件大约 +33%，`.md` 会明显变大——大照片建议 --max-edge 1600，
      单张控制在 200—300KB 比较合适（md2pdf 插入时也是按长边 1600px 压的）。
    · 透明背景：Pillow 压缩时有 alpha 的图会保留 PNG，其余转 JPEG（不会变黑底）。
    · SVG 不栅格化，原样 base64 内嵌（打印出来仍是矢量）。
"""

import argparse
import base64
import io
import os
import re
import sys

# ---------------------------------------------------------------- 常量

# md2pdf 的图片白名单（isImageName）：png/jpeg/gif/webp/avif/bmp/svg/ico
MIME_BY_MAGIC = [
    (b'\x89PNG\r\n\x1a\n', 'image/png'),
    (b'\xff\xd8\xff', 'image/jpeg'),
    (b'GIF87a', 'image/gif'),
    (b'GIF89a', 'image/gif'),
    (b'BM', 'image/bmp'),
    (b'\x00\x00\x01\x00', 'image/x-icon'),
]
RIFF_PREFIX = b'RIFF'
RIFF_WEBP = b'WEBP'
JPEG_START = b'\xff\xd8\xff'

DEFAULT_MARKER = '<!--img-->'
DEFAULT_MAX_KB = 400          # 单张（base64 后）超过就提醒
DEFAULT_MAX_EDGE = 1600       # 压缩时长边上限，和 md2pdf 的「🖼 图片」一致
DEFAULT_QUALITY = 86

BAD_ALT = '[]()<>{}`'


def _setup_stdout():
    """Windows 控制台默认是 GBK：中文提示可能编码失败，能改就改成 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            try:
                stream.reconfigure(errors='replace')
            except Exception:
                pass


def sniff_mime(path, data):
    """按文件头判断图片类型；认不出来返回 None。"""
    for magic, mime in MIME_BY_MAGIC:
        if data.startswith(magic):
            return mime
    if data[:4] == RIFF_PREFIX and data[8:12] == RIFF_WEBP:
        return 'image/webp'
    if data[4:12] in (b'ftypavif', b'ftypavis'):
        return 'image/avif'
    head = data[:4096].lstrip(b'\xef\xbb\xbf \t\r\n').lower()
    if head.startswith(b'<?xml') or head.startswith(b'<svg') or b'<svg' in head[:1024]:
        if b'<svg' in data[:8192].lower():
            return 'image/svg+xml'
    return None


def clean_alt(text, fallback='image'):
    """alt 里不能有 ] ( ) < > 这类会截断 ![](...) 的字符。"""
    s = re.sub(r'[\[\]()<>{}\s`]+', ' ', str(text or '')).strip()
    s = s[:80].strip()
    return s or fallback


def alt_from_path(path):
    name = os.path.splitext(os.path.basename(path))[0]
    return clean_alt(name)


def shrink(data, mime, max_edge, quality):
    """有 Pillow 就按长边压一下；没有就原样返回（并告诉调用方没压）。

    返回 (data, mime, note)；note 是给 stderr 的说明。
    """
    if max_edge <= 0:
        return data, mime, ''
    if mime == 'image/svg+xml':
        return data, mime, 'SVG 不栅格化，按原文件内嵌'
    if mime == 'image/gif':
        return data, mime, 'GIF 原样内嵌（动图不会被压缩）'
    try:
        from PIL import Image
    except Exception:
        return data, mime, '没装 Pillow，原样嵌入（想压缩可 pip install pillow，或用 md2pdf 的「🖼 图片」按钮）'
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception as exc:
        return data, mime, 'Pillow 打不开这张图（%s），原样嵌入' % exc
    w, h = im.size
    if not w or not h:
        return data, mime, '读不到尺寸，原样嵌入'
    if max(w, h) <= max_edge:
        return data, mime, '长边 %dpx 已在 %dpx 以内，不重编码' % (max(w, h), max_edge)
    scale = float(max_edge) / max(w, h)
    tw, th = max(1, round(w * scale)), max(1, round(h * scale))
    try:
        im = im.resize((tw, th), Image.LANCZOS)
    except Exception:
        im = im.resize((tw, th))
    # 有 alpha 的图留 PNG，否则转 JPEG（和 md2pdf 的插入逻辑一致）
    has_alpha = im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info)
    out = io.BytesIO()
    try:
        if has_alpha:
            im.save(out, format='PNG', optimize=True)
            mime2 = 'image/png'
        else:
            if im.mode in ('RGBA', 'LA', 'P'):
                bg = Image.new('RGB', im.size, (255, 255, 255))
                bg.paste(im.convert('RGBA'), mask=im.convert('RGBA').split()[-1])
                im = bg
            elif im.mode != 'RGB':
                im = im.convert('RGB')
            im.save(out, format='JPEG', quality=int(quality), optimize=True)
            mime2 = 'image/jpeg'
    except Exception as exc:
        return data, mime, 'Pillow 编码失败（%s），原样嵌入' % exc
    shrunk = out.getvalue()
    if len(shrunk) >= len(data):
        return data, mime, '压缩后反而更大，用原图'
    return shrunk, mime2, '长边 %dpx → %dpx，%s → %s' % (
        max(w, h), max_edge, human(len(data)), human(len(shrunk)))


def human(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return ('%d %s' % (n, unit)) if unit == 'B' else ('%.1f %s' % (n, unit))
        n /= 1024.0


def to_markdown(alt, mime, data):
    return '![%s](data:%s;base64,%s)' % (alt, mime, base64.b64encode(data).decode('ascii'))


def convert_one(path, args):
    """返回 dict（含 markdown / uri / 诊断信息）。"""
    if not os.path.isfile(path):
        raise IOError('找不到文件：%s' % path)
    with open(path, 'rb') as f:
        raw = f.read()
    if not raw:
        raise IOError('文件是空的：%s' % path)
    mime = sniff_mime(path, raw)
    if not mime:
        raise IOError('这不是认识的图片格式（按文件头判断）：%s' % path)
    data, mime2, note = shrink(raw, mime, args.max_edge, args.quality)
    alt = clean_alt(args.alt) if args.alt else alt_from_path(path)
    uri = 'data:%s;base64,%s' % (mime2, base64.b64encode(data).decode('ascii'))
    md = '![%s](%s)' % (alt, uri)
    kb = len(md) / 1024.0
    warn = ''
    if kb > args.max_kb:
        warn = ('单张图 base64 后约 %.0f KB，超过建议上限 %d KB；'
                '先压缩（--max-edge 1600）或别塞太多大图' % (kb, args.max_kb))
    return {
        'file': path,
        'mime': mime2,
        'alt': alt,
        'src_bytes': len(raw),
        'out_bytes': len(data),
        'md_chars': len(md),
        'markdown': md,
        'uri': uri,
        'note': note,
        'warn': warn,
    }


# ---------------------------------------------------------------- 插入到 .md

def insert_into(path, snippets, marker, force=False):
    """把片段插进 .md：有占位符就逐个替换，没有就追加到文末。

    返回说明文字（给 stdout，告诉 AI 插到哪一行了）。
    """
    with open(path, 'r', encoding='utf-8-sig') as f:
        text = f.read()
    nl = '\n'
    if not text.endswith(nl):
        text += nl

    block = (nl + nl).join(snippets) + nl
    if marker and marker in text:
        # 逐个占位符替换；占位符多于图片时，剩下的原样保留（不擅自删）
        out, pos, used, placed = [], 0, 0, []
        while True:
            at = text.find(marker, pos)
            if at < 0 or used >= len(snippets):
                break
            line_no = text.count(nl, 0, at) + 1
            placed.append(line_no)
            out.append(text[pos:at])
            out.append(snippets[used])
            pos = at + len(marker)
            used += 1
        out.append(text[pos:])
        text = ''.join(out)
        msg = '已替换 %d 个占位符（%s）' % (used, '、'.join('L%d' % n for n in placed))
        if used < len(snippets):
            msg += '；剩余 %d 张图追加到文末' % (len(snippets) - used)
            rest = (nl + nl).join(snippets[used:])
            text = text.rstrip('\n') + nl + nl + rest + nl
    else:
        text = text.rstrip('\n') + nl + nl + block
        msg = '文末追加了 %d 张图（文件里没有占位符 %s）' % (len(snippets), marker)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    return msg


def main(argv=None):
    _setup_stdout()
    ap = argparse.ArgumentParser(
        description='把本地图片转成 base64，内嵌进 Markdown（给 md2pdf 用）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='例：python img2base64.py --insert 讲义.md 图1.png 图2.jpg')
    ap.add_argument('images', nargs='+', help='图片文件（可多个）')
    ap.add_argument('--insert', metavar='MD', help='把片段插入这个 .md（替换 <!--img-->，没有就追加到文末）')
    ap.add_argument('--marker', default=DEFAULT_MARKER, help='占位符，默认 %s' % DEFAULT_MARKER)
    ap.add_argument('--out', metavar='FILE', help='把 Markdown 片段写到这个文件（不打印到 stdout）')
    ap.add_argument('--uri', action='store_true', help='只输出 data URI（stderr 仍有提示）')
    ap.add_argument('--json', action='store_true', help='输出 JSON 元数据（不含 base64 全文）')
    ap.add_argument('--alt', help='alt 文字（单张图时用；默认取文件名）')
    ap.add_argument('--max-edge', type=int, default=0, metavar='N',
                    help='有 Pillow 时长边压到 N 像素（0 = 不压；建议 1600）')
    ap.add_argument('--quality', type=int, default=DEFAULT_QUALITY, metavar='Q',
                    help='JPEG 质量（默认 %d）' % DEFAULT_QUALITY)
    ap.add_argument('--max-kb', type=int, default=DEFAULT_MAX_KB, metavar='KB',
                    help='单张 base64 后超过多少 KB 就提醒（默认 %d）' % DEFAULT_MAX_KB)
    args = ap.parse_args(argv)
    if args.max_edge < 0 or args.quality < 1 or args.quality > 100:
        ap.error('--max-edge 不能是负数；--quality 要在 1—100 之间')
    if args.insert and args.out:
        ap.error('--insert 和 --out 只能二选一')

    items, failed = [], 0
    for p in args.images:
        try:
            items.append(convert_one(p, args))
        except Exception as exc:
            failed += 1
            print('[跳过] %s' % exc, file=sys.stderr)
    if not items:
        print('[FAIL] 没有一张图转换成功。', file=sys.stderr)
        return 1

    for it in items:
        name = os.path.basename(it['file'])
        msg = '[%s] %s：原图 %s → base64 %s（%s）' % (
            'OK', name, human(it['src_bytes']), human(it['md_chars']), it['mime'])
        if it['note']:
            msg += '；' + it['note']
        print(msg, file=sys.stderr)
        if it['warn']:
            print('[提醒] %s' % it['warn'], file=sys.stderr)

    snippets = [it['markdown'] for it in items]

    if args.insert:
        try:
            msg = insert_into(args.insert, snippets, args.marker)
        except Exception as exc:
            print('[FAIL] 写不进 %s：%s' % (args.insert, exc), file=sys.stderr)
            return 1
        print(msg)
        print('下一步：在 md2pdf 里打开这份 .md，预览确认图片出来了再打印。', file=sys.stderr)
    elif args.out:
        try:
            with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
                f.write(('\n\n'.join(snippets)) + '\n')
        except Exception as exc:
            print('[FAIL] 写不进 %s：%s' % (args.out, exc), file=sys.stderr)
            return 1
        print('片段已写入 %s（%d 张）' % (args.out, len(snippets)), file=sys.stderr)
    elif args.uri:
        for it in items:
            print(it['uri'])
    elif args.json:
        import json
        slim = []
        for it in items:
            small = dict(it)
            small.pop('markdown', None)
            small.pop('uri', None)
            small['md_chars'] = it['md_chars']
            small['has_markdown'] = True
            slim.append(small)
        print(json.dumps(slim, ensure_ascii=False, indent=2))
    else:
        for s in snippets:
            print(s)
        total = sum(len(s) for s in snippets)
        if total > 200 * 1024:
            print('[提醒] 上面的输出约 %s（base64）。要写进 .md 建议用 --insert 讲义.md，'
                  '免得把这一大段读进上下文。' % human(total), file=sys.stderr)

    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
