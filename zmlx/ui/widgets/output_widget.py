"""控制台输出控件（OutputWidget — 标准输出捕获、进度条、命令输入行）.

``print`` 中的 ANSI 转义码会被解释成颜色（``\033[31m`` 等，见 :class:`_Ansi`）；
控件**不支持**的序列（擦行 / 清屏 / 光标定位 / OSC 标题……）会被**删除**，
不会在界面上显示成乱码。

保存 / 恢复（:meth:`OutputWidget.save_text` / :meth:`OutputWidget.load_text`）用 **HTML**
（:attr:`OutputWidget.SUFFIX`）而不是纯文本：颜色、粗体等都是存在文本片段的
``QTextCharFormat`` 里的，``toPlainText()`` 会把它们**全部丢掉** —— 早先正是这样存的，
于是「重启后加载的历史没有颜色」（2026-10-26 修复）。旧版本留下的 ``.txt`` 仍按纯文本打开。

内嵌图片（2026-11-02）
---------------------
``print`` 里**独占一行**的标记会被就地渲染成图片::

    print('[[image: path="a.png", w=640]]')
    print('[[image: a.png]]')                       # path 可省引号
    print('[[image: path="a.png", w=640, caption="温度场"]]')

⚠️ **图片就是一个超链接，控件不管理它的任何数据**：

1. 图片在 ``QTextDocument`` 里只是**一个字符**，带一份 ``QTextImageFormat``，其 ``name``
   就是**图片的绝对路径**；
2. 控件**从不** ``addResource``，**从不**缓存、编码、复制图片，也不判断「该不该保留它」——
   文件存不存在、什么时候删，都由 ``print`` 的调用者负责；
3. 因此「显示」= 把路径告诉文档（``insertImage``），「恢复」= 原样 ``setHtml``。实测
   ``toHtml()`` 写出的 ``src`` 就是**裸绝对路径**（不是 ``file://``，Windows 反斜杠不转义，
   中文路径也原样），``setHtml()`` 只凭它就能把图加载回来，**所以恢复路径零改动**。

⚠️ **文件不存在时不插入图片**，该位置只留一行灰字 ``[图片] a.png``（见
:meth:`OutputWidget._add_image`）—— 不画破裂图标、不弹窗、不报错。

⚠️ ``_trim()`` **不为图片做任何特殊处理**：图片在 ``characterCount()`` 里只算 1 个字符，
显示宽度不参与计数，所以裁剪行为与没有图片时完全一致。

大图：解码尺寸封顶（2026-11-02 改）
----------------------------------
⚠️ **判据从「像素尺寸」改成「文件大小」**：原先「超过 3200 万像素就不显示」，于是
8K 截图、相机原图这类**本来完全能看**的图片全被一句「图片过大，未显示」挡在门外。
现在改为：

1. **原始文件 ≤ 30 MB ⇒ 一律显示**（``_ImageFit.MAX_FILE_BYTES``）；
2. 显示时**先把解码尺寸缩到 1000×1000 以内**（``_ImageFit.MAX_CACHED_EDGE``，保持宽高比），
   再交给 :meth:`_ImageFit.fit` 放进面板 —— 界面负载与「原始像素数」**彻底解耦**；
3. 所以**不再有像素上限**：一亿像素的图，只要文件没超 30 MB，就缩到 384 万像素以内再显示
   （约 16 MB 位图）。

⚠️ **缩过的大图要换路径**：``QTextImageFormat.name`` 直接指向原文件时，``QTextDocument``
会**按原分辨率解码**（缩小显示不等于省内存，一亿像素照样要 400 MB 位图）。所以缩过的图先
写成**缓存文件**（``app_data.temp('console_images')``），渲染时指向它；
**没缩过的小图仍然是「超链接」**，按原路径显示，一个字节都不碰。

⚠️⚠️ **记录的永远是原图，显示路径是算出来的**（2026-11-02 按用户要求定）：

| | 是什么 | 存在哪 |
|---|---|---|
| **原图** | 「这个位置是哪张图」的唯一真相 | 图片字符的 :attr:`OutputWidget.IMAGE_PROP` 属性 |
| **预览** | 「这次渲染用哪个文件」 | ``QTextImageFormat.name`` |

缓存路径是原图路径的**纯函数**（:meth:`OutputWidget._cached_image_size`：原图路径 + 大小 +
修改时间 + 目标边长 → SHA1 文件名），**不查任何映射表、不落任何清单文件**。
所以「缓存 → 原图」随时可以**重新算一遍**，不需要维护第二份状态：
缓存被删掉就重建，原图改了自动换新哈希。

⚠️ 代价是历史 HTML 里**只存得下原图路径**（``toHtml()`` 只写 ``name``，自定义属性不落盘），
而大图渲染需要预览路径 —— 所以 :meth:`OutputWidget.set_html` 之后要调
:meth:`OutputWidget._rebind_images` 按原图**重新算一遍**预览路径。这是本机制唯一的
「事后修补」，**别删它**，否则恢复出的大图会让 ``QTextDocument`` 按原分辨率解码。

⚠️ **控制台里的图是「预览」**：双击图片（或右键「在新标签页中打开原图」/「复制图片路径」）
一律给**原图**（从 :attr:`OutputWidget.IMAGE_PROP` 取，不从缓存文件名反推）。

尺寸规则见 :meth:`_ImageFit.fit`：**等比缩放进「面板宽 × 面板高」的包围盒，保证整张可见**，
且**任何情况下都不超过可用宽度**（``w=`` 只是上限，同样会被可用宽度截断）。

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-07: add_text 支持 ANSI 颜色，并过滤不支持的转义序列
Modified by DeepSeek, 2026-10-08: 「内核并行」开关移到主窗口状态栏（原 parallel_edit 属性移除）
Modified by DeepSeek, 2026-10-26: 输出历史改存 HTML，重启后颜色不再丢失
Modified by DeepSeek, 2026-11-02: 控制台内嵌图片（``[[image: ...]]`` 整行标记，图片即超链接）
Modified by DeepSeek, 2026-11-02: 大图改为「只限文件大小（30 MB）+ 解码尺寸封顶 1000×1000」，
取消原来的 3200 万像素上限（超过就缩到缓存文件再显示，不再整张丢弃）
Modified by DeepSeek, 2026-11-02: 去掉 ``_index.json`` 清单 —— 缓存路径改为由原图路径纯函数
推导，文档里永远记录原图（``IMAGE_PROP`` 属性），显示时才换成缓存
"""

import hashlib
import os
import re
import sys
from typing import Optional, Tuple, List, Union

from zmlx.system import app_data
from zmlx.ui.alg import create_action, get_last_exec_history, clear_exec_history
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets
from zmlx.ui.widgets.attr_view import AttrView
from zmlx.ui.widgets.text_browser import TextBrowser


class _Ansi:
    """ANSI 转义序列的最小实现（供 :meth:`OutputWidget.add_text` 上色用）。

    **只解释 SGR**（``\\033[<参数>m``：颜色 / 粗体 / 斜体 / 下划线 / 删除线）；其余序列
    （``\\033[K`` 擦行、``\\033[2J`` 清屏、``\\033[1;1H`` 定位、OSC 标题……）在
    QTextBrowser 上无法实现，一律**删除**——留着只会在界面上显示成乱码。
    被 ``write`` 从中间切断的序列（如 ``'\\033[3'`` + ``'1m红'``）会暂存到下一次调用。

    ⚠️ 四条实测得到的约束（改这个类之前先读）：

    1. PyQt 的 :class:`QtGui.QTextCharFormat` 是**可变引用**：同一个对象若被放进多个
       文本段，后面的 ``\\033[3xm`` 会**追溯**改掉前面段落的颜色。故每次改属性前都要
       ``QTextCharFormat(fmt)`` 拷贝一份。
    2. 「不设置颜色」必须用**空** format（``foreground().style()`` 为 ``NoBrush``）表示，
       这样文字跟随样式表 / 主题；写成 ``setForeground(palette 里的色)`` 在暗色模式下
       就会看不见。
    3. ``\\033[38;5;n`` / ``\\033[38;2;r;g;b``（256 色 / 真彩）必须连**参数**一起吃掉，
       否则剩下的数字会当作普通文本显示出来。
    4. 基础 8 色（30-37 / 90-97 / 40-47 / 100-107）按终端惯例是给**浅色背景**设计的，
       暗色主题下要用另一套取色，见 :attr:`DARK`。
    """

    #: CSI：ESC [ 参数 中间字节 终止字节（``m`` 才是 SGR，其余丢弃）
    CSI = re.compile(r'\x1b\[([0-9;?]*)[ -/]*([@-~])')
    #: 其它完整的转义序列：OSC（BEL 或 ST 结束）、字符集选择、Fe / nF 转义
    OTHER = re.compile(
        r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)'
        r'|\x1b[()#][0-9A-Za-z]'
        r'|\x1b[@-Z\\^_]'
        r'|\x1b[0-9<=>?]')
    #: 可能是「被切断的序列开头」——只对文本**末尾**有意义，故用 ``\Z``（不能用 ``$``，
    #: 它会匹配到换行符之前，把换行也一起吞进暂存区）
    PARTIAL = re.compile(r'\x1b(?:\][^\x07\x1b]{0,120}|\[[0-9;?]{0,32})?\Z')

    #: 浅色背景下的基础 8 色 + 亮色（背景色用同一张表）
    LIGHT = {
        30: '#000000', 31: '#c0392b', 32: '#1a7f37', 33: '#b9770e',
        34: '#1f5fa9', 35: '#8e44ad', 36: '#148f77', 37: '#606060',
        90: '#4d4d4d', 91: '#e74c3c', 92: '#2e9e4f', 93: '#c9a227',
        94: '#3b82f6', 95: '#a855f7', 96: '#0d9488', 97: '#111111',
    }
    #: 暗色背景下的同一组颜色（纯黑 / 纯白都要挪开，否则看不见）
    DARK = {
        30: '#5c6370', 31: '#e06c75', 32: '#98c379', 33: '#e5c07b',
        34: '#61afef', 35: '#c678dd', 36: '#56b6c2', 37: '#abb2bf',
        90: '#7f8c8d', 91: '#ff7b72', 92: '#a5e075', 93: '#f0d27a',
        94: '#79b8ff', 95: '#d2a8ff', 96: '#76e3d6', 97: '#ffffff',
    }

    @classmethod
    def palette(cls, dark):
        """返回当前主题下使用的基础色表。"""
        return cls.DARK if dark else cls.LIGHT

    @classmethod
    def color256(cls, index, dark):
        """xterm 256 色索引 → ``'#rrggbb'``（越界返回 None）。"""
        if index < 0 or index > 255:
            return None
        if index < 8:
            return cls.palette(dark)[30 + index]
        if index < 16:
            return cls.palette(dark)[90 + index - 8]
        if index < 232:
            n = index - 16
            return '#%02x%02x%02x' % tuple(
                0 if v == 0 else 55 + v * 40 for v in (n // 36, (n // 6) % 6, n % 6))
        gray = (index - 232) * 10 + 8  # 232-255：24 级灰阶
        return '#%02x%02x%02x' % (gray, gray, gray)

    @classmethod
    def sgr(cls, fmt, params, dark):
        """按 SGR 参数更新并返回 format（无法识别的参数忽略）。

        Args:
            fmt: 当前生效的 QTextCharFormat（**不会被修改**）
            params: SGR 参数字符串，如 ``'1;38;5;208'``
            dark: 是否暗色主题（决定基础 8 色的取色）

        Returns:
            新的 QTextCharFormat
        """
        if '?' in params:  # 私有模式（\033[?25m 之类）不是 SGR
            return fmt
        codes = [int(x) for x in params.split(';') if x != ''] or [0]
        fmt = QtGui.QTextCharFormat(fmt)  # ⚠️ 必须拷贝，见类文档第 1 条
        table = cls.palette(dark)

        def set_color(color, background=False):
            if color is None:
                return
            if background:
                fmt.setBackground(QtGui.QColor(color))
            else:
                fmt.setForeground(QtGui.QColor(color))

        i = 0
        while i < len(codes):
            code = codes[i]
            i += 1
            if code == 0:  # 全部复位
                fmt = QtGui.QTextCharFormat()
            elif code == 1:
                fmt.setFontWeight(QtGui.QFont.Weight.Bold)
            elif code == 2:
                fmt.setFontWeight(QtGui.QFont.Weight.Light)
            elif code == 3:
                fmt.setFontItalic(True)
            elif code in (4, 21):
                fmt.setFontUnderline(True)
            elif code == 9:
                fmt.setFontStrikeOut(True)
            elif code == 22:
                fmt.setFontWeight(QtGui.QFont.Weight.Normal)
            elif code == 23:
                fmt.setFontItalic(False)
            elif code == 24:
                fmt.setFontUnderline(False)
            elif code == 29:
                fmt.setFontStrikeOut(False)
            elif code == 39:  # 默认前景（跟随主题）
                fmt.clearForeground()
            elif code == 49:  # 默认背景
                fmt.clearBackground()
            elif code in table:  # 30-37 / 90-97：前景
                set_color(table[code])
            elif 40 <= code <= 47:  # 背景
                set_color(table[code - 10], background=True)
            elif 100 <= code <= 107:  # 亮色背景
                set_color(table[code - 10], background=True)
            elif code in (38, 48):  # 256 色 / 真彩
                background = code == 48
                if i < len(codes) and codes[i] == 5 and i + 1 < len(codes):
                    set_color(cls.color256(codes[i + 1], dark), background)
                    i += 2
                elif i < len(codes) and codes[i] == 2 and i + 3 < len(codes):
                    rgb = [min(255, max(0, v)) for v in codes[i + 1:i + 4]]
                    set_color('#%02x%02x%02x' % tuple(rgb), background)
                    i += 4
                else:  # 语法不对：丢掉剩余参数，避免把数字当文本显示
                    i = len(codes)
        return fmt

    @classmethod
    def split(cls, text, fmt, dark=False):
        """把文本拆成「纯文本 + 该段生效的 format」，同时过滤掉不支持的序列。

        Args:
            text: 待处理的文本
            fmt: 上一次调用后仍然生效的 format（跨 write 延续）
            dark: 是否暗色主题

        Returns:
            ``(segments, fmt, pending)``——``segments`` 为 ``[(文本, format)]``；
            ``fmt`` 为末尾仍生效的 format；``pending`` 为**被切断、留待下次处理**的尾部
            （如 ``'\\033[3'``，没有就是空串）。
        """
        segments = []
        pos = i = 0
        n = len(text)
        while i < n:
            if text[i] != '\x1b':
                i += 1
                continue
            found = cls.CSI.match(text, i)
            if found is not None:  # 完整的 CSI
                segments.append((text[pos:i], fmt))
                if found.group(2) == 'm':
                    fmt = cls.sgr(fmt, found.group(1), dark)
                pos = i = found.end()
                continue
            found = cls.OTHER.match(text, i)
            if found is not None:  # 其它完整的转义序列：删掉
                segments.append((text[pos:i], fmt))
                pos = i = found.end()
                continue
            if cls.PARTIAL.match(text, i):  # 尾巴被切断：留给下一次调用
                segments.append((text[pos:i], fmt))
                return segments, fmt, text[i:]
            i += 1  # 零散的 ESC：删掉这个字符
            segments.append((text[pos:i - 1], fmt))
            pos = i
        if pos < n:
            segments.append((text[pos:], fmt))
        return segments, fmt, ''

    @classmethod
    def strip(cls, text):
        """删除文本中的**全部** ANSI 转义序列（含被切断的尾部），返回纯文本。"""
        text = cls.CSI.sub('', text)
        text = cls.OTHER.sub('', text)
        text = cls.PARTIAL.sub('', text)
        return text.replace('\x1b', '')


class _ImageMark:
    """图片标记 ``[[image: path="a.png", w=640]]`` 的解析器（纯文本，无 Qt 依赖）.

    **只认独占一行的标记**：整行除两端空格外只有这一个标记时才生效，行内出现一律当
    普通文本处理。这条是「不误吞用户输出」的唯一保证 —— 自然语言日志几乎不会出现
    ``[[image: ...]]`` 这种整行形状。

    解析失败（缺 ``path`` / ``w`` 不是正整数 / 有无法解释的内容）时返回 ``None``，
    调用方因此把它**原样当文本显示**，什么都不会丢。

    ⚠️ 与 :class:`_Ansi` 的分工：``_Ansi`` 只负责颜色、**不碰**图片标记；本类只负责
    「这一行是不是标记」、**也不碰**颜色。两者在 :meth:`OutputWidget.add_text` 里先后使用。
    """

    #: 整行匹配：两端空白 + ``[[image:`` + 参数 + ``]]``（大小写不敏感）
    LINE = re.compile(
        r'^[ \t]*\[\[\s*image\s*:(?P<body>.*?)\]\][ \t]*$',
        re.IGNORECASE)
    #: 一行可能的最长长度；超过直接当文本（防恶意长串）
    MAX_LINE = 8192
    #: 键值分隔：``key=value``，值可带单 / 双引号；也接受**裸值**（无 ``key=`` 的路径）
    ARG = re.compile(
        r'(?:(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*)?'
        r'(?:"(?P<dq>[^"]*)"|\'(?P<sq>[^\']*)\'|(?P<bare>[^,]*?))'
        r'\s*(?:,|$)')

    @classmethod
    def parse(cls, line):
        """解析**一整行**；不是标记或语法不合法时返回 ``None``.

        Args:
            line: 一行文本（**可以**带结尾换行，内部会先去掉）。

        Returns:
            Optional[dict]: ``{'path': str, 'w': int | None, 'caption': str | None,
            'raw': str}``；``raw`` 是去掉首尾空白的标记原文（用于退化成文本显示）。
            路径为空 / ``w`` 不是正整数时返回 ``None``（按普通文本处理）。
        """
        if not isinstance(line, str) or len(line) > cls.MAX_LINE:
            return None
        found = cls.LINE.match(line.rstrip('\n').rstrip('\r'))
        if found is None:
            return None
        body = found.group('body').strip()
        if not body:
            return None
        path = None
        width = None
        caption = None
        pos = 0
        while pos < len(body):
            if body[pos] in ' \t,':
                pos += 1
                continue
            arg = cls.ARG.match(body, pos)
            if arg is None:  # 有无法解释的内容：整行当文本
                return None
            key = (arg.group('key') or '').lower()
            value = (arg.group('dq') if arg.group('dq') is not None
                     else arg.group('sq') if arg.group('sq') is not None
                     else arg.group('bare')).strip()
            if key in ('', 'path'):  # 裸值 = 路径
                if path is None:
                    path = value
                # 出现第二个裸值（如 `[[image: a.png, caption=...]]`）时忽略
            elif key in ('w', 'width'):
                try:
                    width = int(value)
                except ValueError:
                    return None
                if width <= 0:
                    return None
            elif key in ('caption', 'title'):
                caption = value
            # 其它键：忽略（原文保留在 raw 里），将来扩展不会让老写法失效
            pos = arg.end()
            if pos <= 0:  # 防御：正则未前进（理论上不会发生），直接放弃
                return None
        if not path:
            return None
        return {'path': path, 'w': width, 'caption': caption,
                'raw': line.rstrip('\n').strip()}

    @classmethod
    def is_partial(cls, text):
        """``text``（已确认不以换行结尾）是否可能是**尚未写完的标记**.

        用于行缓冲的放行判断：真标记一定以 ``\\n`` 结尾，所以半行先进缓冲；
        但若这半行看起来是标记的开头，就**留着等下一段**（否则 ``print`` 成
        ``'[[image: a.png'`` + ``']]\\n'`` 两次写会把标记拆坏）。
        """
        head = text.lstrip(' \t')[:16].lower()
        if not head.startswith('[['):
            return False
        rest = head[2:].lstrip()
        return rest == '' or 'image'.startswith(rest) or rest.startswith('image')


class _ImageFit:
    """图片显示尺寸与「多大的图值得解码」的计算（纯算术，无 Qt 依赖，可脱离界面单测）.

    显示尺寸规则（2026-11-02 与用户确认）：**等比缩放，整张放进「面板宽 × 面板高」的包围盒**。

    1. 可用宽 ``avail_w = max(cw - PAD, MIN_W)``，可用高 ``avail_h = ch - PAD``；
    2. ``w=`` 只是**上限**，先被 ``avail_w`` 截断 —— **给定的宽度再大也撑不开窗口**；
    3. ``scale = min(1, limit_w / W, avail_h / H)``：小图不放大；
    4. 高的下限 ``MIN_H``：极端细长图（如 4000×200）在高度不够时**仍保 MIN_H**，
       超出部分交给滚动条，而不是缩成一条 20px 的细线；
    5. **最后再夹一次宽度**：第 4 步可能把宽算回来，必须保证 ``dw <= avail_w`` 恒成立。

    「要不要显示」的规则（2026-11-02 改）：**只按原始文件大小判断**，不按像素。

    - 原文件的像素尺寸**不再是拒绝的理由** —— 一亿像素的图只要文件没超
      :attr:`MAX_FILE_BYTES` 就照常显示，靠 :meth:`decode_size` 把**解码尺寸**压到
      :attr:`MAX_CACHED_EDGE` 以内来控制界面负载；
    - 超过 :attr:`MAX_FILE_BYTES` 的**不尝试解码**（``QImage`` 一张 30 MB 以上的
      位图展开后可能上 GB，解码它的代价与内存都不可控）。
    """

    #: 左右内边距 + 滚动条余量（像素）
    PAD = 24
    #: 可用宽的下限，防止面板还没布局（cw 为 0）时算出负数
    MIN_W = 120
    #: 显示高度的下限（方案 B 的兜底，见上文第 4 条）
    MIN_H = 240
    #: 视口高度低于此值视为「尚未布局」：忽略高度约束，只按宽度适配
    MIN_READY_H = 120

    #: 原始**文件**大小上限：超过就不尝试解码（30 MB）
    MAX_FILE_BYTES = 30 * 1024 * 1024
    #: 解码尺寸上限（长边，像素）：超过就**先缩小再显示**（不是不显示）
    MAX_CACHED_EDGE = 1000
    #: 缩小后的图超过这个像素数才算「值得换文件」（约 400 万像素、16 MB 位图）
    #: ⚠️ 设成 ``MAX_CACHED_EDGE ** 2``：长边 1000 的方图正好落在这条线上，
    #: 不会被「缩了等于没缩」的判断挡掉
    MAX_CACHED_PIXELS = MAX_CACHED_EDGE * MAX_CACHED_EDGE

    @classmethod
    def fit(cls, width, height, view_w, view_h, limit_w=None):
        """计算显示宽高.

        Args:
            width: 原图宽（像素，须为正）。
            height: 原图高（像素，须为正）。
            view_w: 面板视口宽（像素）。
            view_h: 面板视口高（像素）。
            limit_w: 显式 ``w=`` 上限；``None`` 表示没有。

        Returns:
            Optional[Tuple[int, int]]: ``(dw, dh)``；参数非法时返回 ``None``。
        """
        if width <= 0 or height <= 0:
            return None
        avail_w = max(int(view_w) - cls.PAD, cls.MIN_W)
        if limit_w is not None and limit_w > 0:
            avail_w = max(min(avail_w, int(limit_w)), 1)
        avail_h = int(view_h) - cls.PAD
        ratio = min(1.0, avail_w / float(width))
        if avail_h >= cls.MIN_READY_H:  # 视口还没布局时不用高度约束
            ratio = min(ratio, avail_h / float(height))
        dw = max(1, int(round(width * ratio)))
        dh = max(1, int(round(height * ratio)))
        if dh < cls.MIN_H and width * cls.MIN_H / float(height) <= avail_w:
            # 高的下限（方案 B）：保可读高度，宽度按比例回来
            dh = cls.MIN_H
            dw = max(1, int(round(width * cls.MIN_H / float(height))))
        dw = min(dw, avail_w)  # ⚠️ 最后再夹一次：任何路径都不许超过可用宽
        return dw, dh

    @classmethod
    def is_too_large(cls, nbytes):
        """原始**文件**是否大到不该尝试解码（只用于「不显示」，不报错）.

        ⚠️ 判据是**文件字节数**，不是像素：像素只影响「要不要先缩小」，由
        :meth:`decode_size` / :meth:`needs_cache` 决定。
        """
        return nbytes is not None and nbytes > cls.MAX_FILE_BYTES

    @classmethod
    def decode_size(cls, width, height):
        """返回**解码**用的 ``(w, h)``：保持宽高比，长边不超过 :attr:`MAX_CACHED_EDGE` .

        小图原样返回（绝不放大）；参数非法时返回 ``None``。
        """
        if width <= 0 or height <= 0:
            return None
        scale = cls.MAX_CACHED_EDGE / float(max(width, height))
        if scale >= 1.0:
            return int(width), int(height)
        return max(1, int(round(width * scale))), max(1, int(round(height * scale)))

    @classmethod
    def needs_cache(cls, width, height):
        """是否需要**先缩小再显示**（即必须换成一个缩过的缓存文件）.

        判据是**原图**的像素数超过 :attr:`MAX_CACHED_PIXELS`（= :attr:`MAX_CACHED_EDGE`
        的平方）—— 也就是「缩了确实省事」才缩：

        - 4000×3000 的相机原图：原文件路径交给文档会按 1200 万像素解码 ⇒ **要缩**；
        - 9000×200 的长条图：文件头说长边超 1000，但整张只有 180 万像素（≈ 8 MB 位图），
          缩完也只有 1000×22 —— 按原路径显示毫无压力，**不该缩**（省一次 IO，
          历史 HTML 也不必依赖缓存）；
        - 不缩的小图**绝不放大**（``decode_size`` 不会超过原尺寸）。

        ⚠️ 这里判的是**原图**：不能拿 ``decode_size`` 的结果去比 —— 那个值本身已被夹到
        1000 以内，永远不可能超过 :attr:`MAX_CACHED_PIXELS`（那样判断恒为假）。
        """
        if width <= 0 or height <= 0:
            return False
        return width * height > cls.MAX_CACHED_PIXELS


class OutputWidget(QtWidgets.QWidget):
    #: 控制台保留的最大字符数（超出后从头丢掉一半，见 :meth:`_trim`）
    MAX_CHARS = 10000
    #: 行缓冲上限（字符数）：超过就不再等「标记的另一半」，原样吐出（防内存无上限增长）
    LINE_BUFFER_MAX = 4096
    #: 图片字符格式上记录**原图绝对路径**的自定义属性（``QTextCharFormat.Property`` 编号）.
    #: ⚠️ 渲染用的 ``QTextImageFormat.name`` 可能是预览缓存，只有这个属性才是「这张图是谁」。
    #: 取值需避开 Qt 自己占用的 ``UserProperty`` 起始编号（内部已跳过 0x100000~0x10FFFF）。
    IMAGE_PROP = QtGui.QTextFormat.Property.UserProperty + 1

    #: 本次进程内**预览缓存创建失败过**的原图路径（绝对路径）.
    #: ⚠️ 失败一次就不再重试：失败发生在 ``setCharFormat`` 期间，文档会立刻再请求同一张图，
    #:    不记住就会变成 GUI 线程里的死循环（见 :meth:`_cached_image_size`）。
    _CACHE_FAILED = set()
    #: 正在计算中的原图路径（防重入：文档重绘会在计算途中再次请求同一张图）.
    _CACHE_BUSY = set()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.text_browser = TextBrowser(self)
        layout.addWidget(self.text_browser)

        # ⚠️ 「并行」复选框（CoreParallelEdit，2026-10-26 前叫「内核并行」）**已经搬到主窗口的状态栏**里了
        #    （见 MainWindow.__init__）：它是**全局**开关，而本面板可以不开 / 被收起，
        #    开关就跟着看不见了。不要在这里再放一个 —— 两个 QCheckBox 不会自动同步
        #    （各自只在构造时 setChecked 一次），会显示同一个状态却各说各话。
        #    本类原先的 ``parallel_edit`` 公开属性随之移除（仓内没有外部读取）。

        self.attr_view = AttrView(self)
        self.attr_view.setVisible(False)
        layout.addWidget(self.attr_view)

        # 添加进度条（这也是作为标准输出）
        self.progress_label = QtWidgets.QLabel(self)
        self.progress_bar = QtWidgets.QProgressBar(self)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)
        self.progress(visible=False)

        # ── 命令输入行 ──
        self._cmd_history = self._load_history()
        self._cmd_history_idx = len(self._cmd_history)
        self._first_cmd = True

        # ── ANSI 状态（跨 write 延续；见 _Ansi）──
        self._ansi_fmt = QtGui.QTextCharFormat()  # 当前仍生效的颜色 / 字体
        self._ansi_pending = ''  # 被 write 切断、留到下一次的转义序列
        self._ansi = self._load_ansi()  # 是否解释 ANSI 转义码

        # ── 图片状态（见 _ImageMark / _ImageFit）──
        self._image = self._load_image()  # 是否把 [[image: ...]] 渲染成图片
        self._line_pending = ''  # 尚未凑成完整行的半行（只可能是标记的开头）

        self.cmd_input = QtWidgets.QLineEdit(self)
        self.cmd_input.setPlaceholderText('输入 Python 命令，按 Enter 执行...')
        self.cmd_input.returnPressed.connect(self._exec_cmd)
        self.cmd_input.installEventFilter(self)
        layout.addWidget(self.cmd_input)

        # 覆盖text_browser的右键菜单
        get_context_menu = self.text_browser.get_context_menu

        def f2():
            menu = get_context_menu()
            menu.addSeparator()
            for ac in self.get_context_actions():
                menu.addAction(ac)
            return menu

        self.text_browser.get_context_menu = f2  # 替换

        # ── 图片上的右键菜单（「在新标签页中打开原图 / 复制路径」）──
        # ⚠️ 只**追加**动作，不改变非图片处的行为：那里必须与替换之前完全一致
        #    （标准文本菜单 + 「清除内容」等）。判定方式与 AI 助手一致 ——
        #    光标处的字符格式是不是 image format。
        browser = self.text_browser
        # ⚠️⚠️ **必须在替换之前**把原实现存成绑定方法，兜底时调用**它**。两种错误写法：
        #    ① ``QtWidgets.QTextBrowser.contextMenuEvent(browser, event)`` —— 那是 Qt 的
        #       基类实现，走另一条内部路径，既不经 ``TextBrowser.get_context_menu``、
        #       也不弹菜单 ⇒ **整个右键菜单消失**（2026-11-02 实测：6 项 → 0 项）；
        #    ② ``browser.contextMenuEvent(event)`` —— 那时它是本函数自己 ⇒ 无限递归
        #       （同日另一处 RecursionError 就是它）。
        original_context_menu_event = browser.contextMenuEvent

        def _context_menu_event(event):
            try:
                if self._image_at(event.pos()) is not None:
                    menu = f2()
                    menu.addSeparator()
                    menu.addAction(create_action(
                        self, '在新标签页中打开原图',
                        slot=lambda: self._open_image_at(event.pos())))
                    menu.addAction(create_action(
                        self, '复制图片路径',
                        slot=lambda: self._copy_image_path_at(event.pos())))
                    menu.exec(event.globalPos())
                    return
            except Exception as err:  # 右键菜单失败不该影响控件
                print(f'Error: {err}')
            original_context_menu_event(event)  # 原样交还给 TextBrowser 的实现

        browser.contextMenuEvent = _context_menu_event

        # ── 双击图片 → 在新标签页中打开原图 ──
        # ⚠️ 与右键菜单同样的纪律：替换前先存原实现，非图片处**原样交还**
        #    （双击的默认行为是「选中一个词」，那是用户还在用的基本操作，不能吞掉）。
        original_double_click_event = browser.mouseDoubleClickEvent

        def _mouse_double_click_event(event):
            try:
                if event.button() == QtCore.Qt.MouseButton.LeftButton:
                    if self._image_at(event.pos()) is not None:
                        self._open_image_at(event.pos())
                        return
            except Exception as err:  # 双击失败不该影响控件
                print(f'Error: {err}')
            original_double_click_event(event)

        browser.mouseDoubleClickEvent = _mouse_double_click_event

    def _image_at(self, pos):
        """返回 ``pos``（视口坐标）处**内嵌图片**的原图绝对路径；不是图片返回 ``None``.

        ⚠️ 返回的是 :attr:`IMAGE_PROP` 里记录的**原图**，不是渲染用的 ``name``
        （后者对大图是预览缓存）。拿不到原图属性时才退回 ``name`` —— 那是
        旧版历史 HTML 恢复出来的图，它本来就是原图路径。
        """
        try:
            cursor = self.text_browser.cursorForPosition(pos)
            fmt = cursor.charFormat()
            if fmt.isImageFormat():
                origin = fmt.property(self.IMAGE_PROP)
                if isinstance(origin, str) and origin:
                    return origin
                return fmt.toImageFormat().name() or None
        except Exception:
            pass
        return None

    def _open_image_at(self, pos):
        """在**新标签页**中打开 ``pos`` 处的原图（双击与右键菜单共用）.

        大图在控制台里只是**预览**（已缩到长边 1000），看不清的细节靠这里打开原图看 ——
        所以「打开原图」**永远打开用户自己的那个文件**，不是预览缓存。
        原图路径来自 :attr:`IMAGE_PROP`，不是从缓存文件名反推的。

        ⚠️ 图片已被删除时**不调** ``gui.open_image``（它对不存在的文件什么都不做，
        用户会以为「点了没反应」），改为在输出面板里补一句可读的说明。
        """
        path = self._image_at(pos)
        if not path:
            return
        if not os.path.isfile(path):
            self._feed(f'[图片] 已不存在：{path}\n', None)
            return
        try:
            gui.open_image(path, caption=os.path.basename(path), on_top=True)
        except Exception as err:
            self._feed(f'[图片] 打开失败：{err}\n', None)

    def _copy_image_path_at(self, pos):
        """右键菜单：把**原图**路径复制到剪贴板."""
        path = self._image_at(pos)
        if path:
            QtWidgets.QApplication.clipboard().setText(path)

    def _choose_image_and_show(self):
        """右键菜单「打开图片…」：选一个图片文件，**追加显示**到输出面板.

        ⚠️ 这是「把图贴进控制台」，**不是**在标签页里打开 —— 后者用 ``gui.open_image``
        （图片上双击 / 右键「在新标签页中打开原图」）。
        ⚠️ 追加的内容就是**同一套标记**（:meth:`_add_image`），所以尺寸规则、缺图退化、
        「显示图片」开关全部一致，没有第二条渲染路径。
        """
        filters = (
            '图片文件 (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp);;'
            '所有文件 (*.*)')
        try:
            fname, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, '打开图片（显示到输出窗口）', '', filters)
        except Exception as err:  # 拿不到对话框（无界面等）也不该影响控件
            self._feed(f'[图片] 打开对话框失败：{err}\n', None)
            return
        if not fname:
            return  # 用户取消
        self._add_image({'path': fname, 'w': None, 'caption': None, 'raw': fname})

    def show_attrs(self, **attrs):
        self.attr_view.show_attrs(**attrs)
        self.attr_view.setVisible(self.attr_view.get_count() > 0)

    def progress(
            self, label: Optional[str] = None, val_range: Optional[Union[List[int], Tuple[int, int]]] = None,
            value: Optional[int] = None, visible: Optional[bool] = None):
        """
        显示进度
        """
        if label is not None:
            visible = True
            self.progress_label.setText(label)
        if val_range is not None:
            visible = True
            assert len(val_range) == 2
            self.progress_bar.setRange(*val_range)
        if value is not None:
            visible = True
            self.progress_bar.setValue(value)
        if visible is not None:
            self.progress_bar.setVisible(visible)
            self.progress_label.setVisible(visible)

    def _exec_cmd(self):
        """执行输入的命令."""
        code = self.cmd_input.text().strip()
        self.cmd_input.clear()
        if not code:
            return

        self._cmd_history.append(code)
        self._cmd_history_idx = len(self._cmd_history)
        if len(self._cmd_history) > 500:
            self._cmd_history = self._cmd_history[-500:]
        self._save_history()

        if self._first_cmd:
            self._first_cmd = False
            gui.show_memory()
        self.add_text(f'>>> {code}\n')

        def task():
            try:
                try:
                    c = compile(code, '<console>', 'eval')
                    r = eval(c, app_data.space)
                    if r is not None:
                        print(repr(r))
                except SyntaxError:
                    exec(code, app_data.space)
            except Exception as ex:
                print(f'{type(ex).__name__}: {ex}', file=sys.stderr)

        if gui.exists():
            gui.start_func(task, add_history=False)
        else:
            task()

    @property
    def _history_file(self):
        from zmlx.system import app_data
        return app_data.temp('console_cmd_history.txt')

    def _load_history(self):
        try:
            if os.path.isfile(self._history_file):
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    return [line.rstrip('\n') for line in f if line.strip()]
        except Exception:
            pass
        return []

    def _save_history(self):
        try:
            from zmlx.system import make_parent
            with open(make_parent(self._history_file), 'w', encoding='utf-8') as f:
                for line in self._cmd_history[-500:]:
                    f.write(line + '\n')
        except Exception:
            pass

    def eventFilter(self, obj, event):
        """拦截输入框的上下箭头，浏览命令历史."""
        if obj == self.cmd_input and event.type() == QtCore.QEvent.Type.KeyPress:
            key = event.key()
            if key == QtCore.Qt.Key.Key_Up:
                if self._cmd_history:
                    self._cmd_history_idx = max(0, self._cmd_history_idx - 1)
                    self.cmd_input.setText(self._cmd_history[self._cmd_history_idx])
                return True
            elif key == QtCore.Qt.Key.Key_Down:
                if self._cmd_history:
                    idx = min(len(self._cmd_history) - 1, self._cmd_history_idx + 1)
                    if idx < len(self._cmd_history):
                        self._cmd_history_idx = idx
                        self.cmd_input.setText(self._cmd_history[idx])
                return True
        return super().eventFilter(obj, event)

    def get_context_actions(self):
        act_ansi = create_action(
            self, 'ANSI 颜色', slot=self._toggle_ansi)
        act_ansi.setCheckable(True)
        act_ansi.setChecked(self._ansi)
        act_image = create_action(
            self, '显示图片', slot=self._toggle_image)
        act_image.setCheckable(True)
        act_image.setChecked(self._image)
        # 「打开图片…」：选一个文件，**追加**显示到输出窗口（见 _choose_image_and_show）。
        # ⚠️ 名字里带「…」以区别图片上的「在新标签页中打开原图」：这一个不建标签页。
        # ⚠️ 图标用 ``open``：图标库里没有 image / photo 之类，``load_icon`` 拿不到会返回空图标。
        act_open_image = create_action(
            self, '打开图片…', icon='open',
            slot=self._choose_image_and_show)
        result = [act_ansi, act_image, act_open_image, create_action(
            self, '隐藏', icon='console',
            slot=lambda: gui.hide_console())]
        if gui.is_running():
            if gui.is_paused():
                result.append(create_action(
                    self, '继续', icon='begin',
                    slot=lambda: gui.set_paused(False))
                )
            else:
                result.append(create_action(
                    self, '暂停', icon='pause',
                    slot=lambda: gui.set_paused(True))
                )
            result.append(create_action(
                self, '停止', icon='stop',
                slot=lambda: gui.stop_console())
            )
        else:
            if get_last_exec_history() is not None:
                result.append(create_action(
                    self, '再次运行', slot=lambda: gui.start_last())
                )
                result.append(create_action(
                    self, '清除历史', slot=clear_exec_history)
                )
            result.append(create_action(
                self, '脚本运行历史',
                slot=lambda: gui.show_code_history(
                    folder=app_data.root('console_history'),
                    caption='运行历史'))
            )
            result.append(create_action(
                self, '输出历史',
                slot=gui.show_output_history)
            )

        if app_data.get('DISABLE_PAUSE', False):
            result.append(create_action(
                self, '启用pause', slot=lambda: app_data.put('DISABLE_PAUSE', False))
            )
        else:
            result.append(create_action(
                self, '禁用pause', slot=lambda: app_data.put('DISABLE_PAUSE', True))
            )

        return result

    @staticmethod
    def _load_ansi():
        """是否解释 ANSI 转义码（持久化在 ``console_ansi``，右键菜单可切换）。"""
        return app_data.getenv(
            key='console_ansi', default='Yes', ignore_empty=True) != 'No'

    @staticmethod
    def _load_image():
        """是否把 ``[[image: ...]]`` 渲染成图片（持久化在 ``console_image``）."""
        return app_data.getenv(
            key='console_image', default='Yes', ignore_empty=True) != 'No'

    @staticmethod
    def plain_text(text):
        """返回去掉全部 ANSI 转义序列的纯文本（状态栏等只放一行的地方用）。"""
        return _Ansi.strip(str(text))

    def _dark(self):
        """当前是否暗色主题（决定 ANSI 基础 8 色用哪一套取色）。

        ⚠️ 这里**不**调 ``gui.in_dark_mode()``：那要经过 GuiApi 的通道往返，而本方法在
        ``print`` 的热路径上（每写一次都要判），直接读控件自己的调色板就够了。
        """
        base = self.text_browser.palette().color(QtGui.QPalette.ColorRole.Base)
        return base.lightness() < 128

    def _toggle_ansi(self):
        """右键菜单：切换是否解释 ANSI 转义码（状态落盘，下次启动仍然生效）。"""
        self._ansi = not self._ansi
        app_data.setenv(key='console_ansi', value='Yes' if self._ansi else 'No')

    def _toggle_image(self):
        """右键菜单：切换 ``[[image: ...]]`` 是否渲染成图片（状态落盘，下次启动仍然生效）.

        ⚠️ 关掉时**整行标记原样显示**（连 ``[图片] xxx`` 那行说明都不加），
        即「关掉图片就完全看不到图片机制的痕迹」。缓冲区里残留的半行也要先冲掉。
        """
        self.flush_pending()
        self._image = not self._image
        app_data.setenv(key='console_image', value='Yes' if self._image else 'No')

    def add_text(self, text, ansi=None):
        """
        在控制台末尾追加文本。

        Args:
            text: 要追加的文本。其中的 ANSI 转义码会被解释成颜色，控件不支持的序列
                （擦行 / 清屏 / 光标定位 / OSC……）会被**删除**，不会显示成乱码。
                独占一行的 ``[[image: ...]]`` 标记会被渲染成图片（见模块文档）。
            ansi: 是否解释 ANSI 转义码。None（默认）表示按用户设置 ``console_ansi``
                （右键菜单可切换）；False 表示只过滤转义码、不着色
        """
        if not isinstance(text, str):
            text = str(text)
        if ansi is None:
            ansi = self._ansi
        if self._image:
            # ⚠️ 只有「显示图片」打开时才需要行缓冲：关掉时标记本来就当文本，
            #    直接走原来的路径，热路径上不增加任何开销。
            # ⚠️ 必须**逐段**（以 \n 为界）处理：一次 write 里可能既有完整行、又有
            #    被切断的尾巴，整块当一行判会把标记拆坏（2026-11-02 实测踩到）。
            pending = self._line_pending + text
            self._line_pending = ''
            start = 0
            while True:
                cut = pending.find('\n', start)
                if cut < 0:
                    break
                self._add_line(pending[start:cut + 1], ansi)
                start = cut + 1
            if start < len(pending):
                self._add_line(pending[start:], ansi)
            return
        self._feed(text, ansi)

    def flush_pending(self):
        """把行缓冲里残留的半行冲刷出来（内核结束 / 保存历史前调用）.

        ⚠️ 不冲刷的话，``print('...', end='')`` 写出的最后半行会**永远留在缓冲区里**
        —— 它不会自己冒出来，用户看到的是「少了最后一段」。``\\r`` 进度输出同理。
        """
        if self._line_pending:
            rest = self._line_pending
            self._line_pending = ''
            self._feed(rest, self._ansi)

    def _add_line(self, line, ansi):
        """处理一段**已经按 ``\\n`` 切开**的文本：完整行可能是标记，半行视情况缓冲."""
        if line.endswith('\n'):
            found = _ImageMark.parse(line) if self._image else None
            if found is not None:
                self._line_pending = ''
                self._add_image(found)
                return
            self._feed(line, ansi)
            self._line_pending = ''
            return
        if not line:
            return
        # 半行（``print(..., end='')`` 的进度输出 / 被切断的标记）：
        # 只有「看起来像标记开头」才留着等下一段，否则立刻放行（不做任何延迟）。
        if _ImageMark.is_partial(line):
            self._line_pending += line
            if len(self._line_pending) > self.LINE_BUFFER_MAX:
                # 缓冲区上限：过长的「疑似标记」就放弃等待，原样吐出（防内存无上限增长）
                rest = self._line_pending
                self._line_pending = ''
                self._feed(rest, ansi)
        else:
            self._feed(line, ansi)

    def _feed(self, text, ansi):
        """走原来的 ANSI 着色路径（本轮之前的行为，一行未改）."""
        if ansi:
            segments, self._ansi_fmt, self._ansi_pending = _Ansi.split(
                self._ansi_pending + text, self._ansi_fmt, dark=self._dark())
        else:
            segments = [(_Ansi.strip(self._ansi_pending + text), None)]
            self._ansi_pending = ''
        self._insert(segments)

    def _add_image(self, mark):
        """把一条解析成功的图片标记渲染成「灰色说明行 + 图片字符」.

        ⚠️ **文档里记录的永远是原图路径**（2026-11-02 按用户要求定）：先按原图算出
        :attr:`IMAGE_PROP` 属性里的**预览路径**，再把预览路径填进 ``QTextImageFormat.name``
        （文档渲染用的就是 ``name``），同时把原图路径记在字符格式的自定义属性里。

        为什么要分成「记录」和「渲染」两份：

        - ``QTextImageFormat.name`` 指向哪个文件，``QTextDocument`` 就按那个文件
          **原分辨率解码** —— 直接填原图，一亿像素照样要 400 MB 位图，缩小的只是显示尺寸。
        - 但「这个位置究竟是哪张图」必须永远说得清楚，所以原图路径单独记一份。

        预览路径由原图路径**纯函数推导**（见 :meth:`_cached_image_size`），不查任何清单；
        小图没有预览（就是原图本身），两份东西完全相同。

        ⚠️ **文件不存在 / 不是图片 / 原文件超过 30 MB 时什么都不插入**，只留那行灰字，
        于是「原位显示」的是一句可读说明（``[图片] a.png``），而不是破裂图标。
        """
        raw_path = mark['path']
        path = self._resolve_path(raw_path)
        nbytes = self._file_size(path) if path is not None else None
        if nbytes is None:
            self._feed(f'[图片] {raw_path}\n', None)
            return
        if _ImageFit.is_too_large(nbytes):
            self._feed(
                f'[图片] {raw_path}（文件过大，未显示：'
                f'{nbytes / 1024 / 1024:.1f} MB，上限 '
                f'{_ImageFit.MAX_FILE_BYTES / 1024 / 1024:.0f} MB）\n', None)
            return
        size = self._image_size(path)
        if size is None:
            self._feed(f'[图片] {raw_path}\n', None)
            return
        shown = self._preview_of(path)  # 大图 = 预览缓存（不存在就当场创建），小图 = 原图
        if shown is None:  # 解不出来：退化为文本行
            self._feed(f'[图片] {raw_path}\n', None)
            return
        shrunk = self._is_cached_name(shown)
        shown_size = self._image_size(shown)
        if shown_size is not None:
            size = shown_size
        width, height = size
        viewport = self.text_browser.viewport()
        fitted = _ImageFit.fit(width, height, viewport.width(), viewport.height(),
                               limit_w=mark['w'])
        if fitted is None:
            self._feed(f'[图片] {raw_path}\n', None)
            return
        dw, dh = fitted
        note_fmt = QtGui.QTextCharFormat()
        note_fmt.setForeground(QtGui.QBrush(QtGui.QColor('#808080')))
        note = f'[图片] {raw_path}'
        if shrunk:
            # ⚠️ 说明这是「预览」：控制台里只给看得清的整体，细节靠双击打开原图，
            #    不然用户会以为自己的原图就这么糊。
            note += (f'（预览：已缩放到长边 {_ImageFit.MAX_CACHED_EDGE} 像素，'
                     f'双击打开原图）')
        self._insert([(note + '\n', note_fmt)])
        image_fmt = QtGui.QTextImageFormat()
        image_fmt.setName(shown)   # 渲染用：大图是缓存，小图就是原图
        image_fmt.setWidth(dw)     # ⚠️ 宽高都要设：只设宽的话高按原比例算，会顶出面板
        image_fmt.setHeight(dh)
        # ⚠️ 记录用：原图绝对路径。渲染时换了文件，这里也不变 —— 它才是「这张图是谁」。
        image_fmt.setProperty(self.IMAGE_PROP, os.path.abspath(path))
        cursor = self.text_browser.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        cursor.insertImage(image_fmt)
        cursor.insertText('\n')
        self.text_browser.setTextCursor(cursor)
        self._trim()

    @staticmethod
    def _resolve_path(path):
        """把标记里的路径解析成绝对路径；找不到就返回 ``None``.

        顺序（**确定性优先**）：绝对路径 → 相对当前工作目录 → 相对脚本所在目录
        （``app_data.space['__file__']``）。不做「每次重绘再解析」—— 一旦找到就把
        绝对路径写进文档，避免「后来 cwd 变了，图片变成另一张」这种难查的行为。
        """
        try:
            if os.path.isabs(path):
                return path if os.path.isfile(path) else None
            if os.path.isfile(path):
                return os.path.abspath(path)
            script = app_data.space.get('__file__')
            if isinstance(script, str) and script:
                candidate = os.path.join(os.path.dirname(os.path.abspath(script)), path)
                if os.path.isfile(candidate):
                    return candidate
        except Exception:
            return None
        return None

    @staticmethod
    def _file_size(path):
        """原文件的字节数；读不到（不存在 / 没权限）返回 ``None``."""
        try:
            return os.path.getsize(path)
        except Exception:
            return None

    @classmethod
    def _cached_image_size(cls, path):
        """返回原图的**预览缓存路径**；不存在就先创建，创建失败返回 ``None``.

        Args:
            path: 原图路径（必须已存在、且文件大小已通过检查）。

        Returns:
            Optional[str]: 缓存文件路径（已创建就绪）；读不出图片时返回 ``None``。

        ⚠️⚠️ **缓存路径是原图路径的纯函数，不查任何清单**（2026-11-02 按用户要求改成这样）：
        文件名 = ``sha1(原图绝对路径 + 文件大小 + 修改时间 + 目标边长)`` 的前 16 位。
        于是「原图 → 缓存」随时可以**重新算出来**，不需要记住任何映射关系；
        唯一的记录永远是**原图路径本身**，这也是文档里存的东西。

        ⚠️ 把修改时间算进哈希是**有意的**：原图被改过之后，旧缓存自动不再匹配，
        不需要任何「失效」逻辑。代价是原图每改一次就多一份缓存文件 ——
        这可以接受（缓存本来就是可清理的中间产物，且同一张图在未修改期间只写一次）。

        ⚠️ 格式取**文件头**里的真实格式（用户把 JPEG 存成 ``.png`` 时仍按 JPEG 写出去）。
        ⚠️ 写入不是原子的，所以先写临时名再 ``os.replace``：并发的另一个进程 / 线程
        不会读到写了一半的图。

        ⚠️⚠️ **这是「失败即放弃、且整个进程只试一次」的接口**（2026-11-03）：

        - **目录缺失是常态**（``temp/console_images`` 从来不会预先存在：它只在第一次用到
          时由 ``app_data.temp()`` 顺带创建），所以这里**自己先建目录**并确认可写。
          以前不建就 ``image.save()``，目标目录不存在时 ``save()`` 直接失败 —— 而失败
          发生在 :meth:`_rebind_images` 的 ``setCharFormat`` 期间，文档会**再次**请求
          同一张图、又一次失败……GUI 线程于是死循环，启动画面永远不消失（2026-11-03
          实测：历史里 8 张图时 CPU 满核、内存涨到 2.1 GB）。
        - 任何一步失败（建目录 / 目录不可写 / 解码 / 保存 / 改名）都**记进
          :attr:`_CACHE_FAILED` 并立即返回 ``None``**，同一路径在本次进程内**不再重试**
          —— 调用方据此直接沿用原图路径，代价只是「这张图按原分辨率显示」，绝不会卡住。
        """
        key = os.path.abspath(path)
        if key in cls._CACHE_FAILED or key in cls._CACHE_BUSY:
            # 已经失败过 / 正在算（重入，见 set_html 之后的 _rebind_images）：
            # 一律不再动手。重入时不设防的话就是无限递归。
            return None
        cls._CACHE_BUSY.add(key)
        try:
            folder = app_data.temp('console_images')
            if not cls._ensure_folder(folder):
                cls._CACHE_FAILED.add(key)
                return None
            stat = os.stat(path)
            digest = hashlib.sha1(
                f'{os.path.abspath(path)}|{stat.st_size}|{stat.st_mtime_ns}|'
                f'{_ImageFit.MAX_CACHED_EDGE}'.encode('utf-8')).hexdigest()[:16]
            reader = QtGui.QImageReader(path)
            if not reader.canRead():
                return None  # 不是图片：调用方本来就该退化成文本，不必记成「失败」
            fmt = bytes(reader.format()).decode('ascii', 'ignore').lower() or 'png'
            target = os.path.join(folder, f'{digest}.{fmt}')
            if cls._cache_ready(target):
                return target  # 已经缩过一次：不重复解码、不重复写盘
            scaled = _ImageFit.decode_size(
                reader.size().width(), reader.size().height())
            if scaled is None:
                return None
            # ⚠️ setScaledSize = 解码时就按目标尺寸解，不是「先解全图再缩小」：
            #    后者正是本方法要避免的那次「原图字节数 × 数倍」的峰值。
            reader.setScaledSize(QtCore.QSize(*scaled))
            image = reader.read()
            if image.isNull():
                return None
            temp = target + '.tmp'
            try:
                if not image.save(temp, fmt):
                    cls._CACHE_FAILED.add(key)  # 写盘失败：本次进程内不再重试
                    return None
                os.replace(temp, target)
            finally:
                if os.path.isfile(temp):
                    try:
                        os.remove(temp)
                    except Exception:
                        pass
            if cls._cache_ready(target):
                return target
            cls._CACHE_FAILED.add(key)
            return None
        except Exception:
            cls._CACHE_FAILED.add(key)
            return None
        finally:
            cls._CACHE_BUSY.discard(key)

    @staticmethod
    def _ensure_folder(folder):
        """确保预览缓存目录存在**且可写**；做不到返回 ``False``（调用方直接放弃）.

        ⚠️ 只 ``os.path.isdir`` 不算数：目录可能因为没有权限 / 磁盘满而写不进去，
        那样 ``QImage.save()`` 照样失败。所以这里**真的写一个探针文件**再删掉 ——
        一次几十微秒，换掉「反复失败 → 死循环」的风险很划算。
        """
        try:
            os.makedirs(folder, exist_ok=True)
            probe = os.path.join(folder, f'.probe_{os.getpid()}.tmp')
            with open(probe, 'wb') as file:
                file.write(b'\x00')
            os.remove(probe)
            return True
        except Exception:
            return False

    @staticmethod
    def _cache_ready(target):
        """缓存文件是否**可用**（存在、非空、而且读得出来）.

        ⚠️ 必须能读出来才算数：进程被杀 / 磁盘满时会留下 0 字节或半截文件，只看
        ``isfile`` 会让文档一直指向一个坏文件（渲染成裂图）。
        """
        try:
            if not os.path.isfile(target) or os.path.getsize(target) <= 0:
                return False
            return not QtGui.QImageReader(target).size().isEmpty()
        except Exception:
            return False

    @staticmethod
    def _is_cached_name(path):
        """``path`` 是不是本控件生成的预览缓存（而不是用户自己的图片文件）."""
        try:
            folder = app_data.temp('console_images')
            return os.path.dirname(os.path.abspath(path)) == os.path.abspath(folder)
        except Exception:
            return False

    @staticmethod
    def _image_size(path):
        """用 ``QImageReader`` **只读文件头**拿尺寸（不解码）；读不出来返回 ``None``.

        ⚠️ 这正是「不管理图片数据」的体现：只问「多宽多高」，拿到就放手，连像素都
        不留在内存里。读文件头失败 = 不是图片 / 文件不可读 ⇒ 调用方退化为文本。
        """
        try:
            reader = QtGui.QImageReader(path)
            size = reader.size()
            if size.isValid() and size.width() > 0 and size.height() > 0:
                return size.width(), size.height()
        except Exception:
            pass
        return None

    def _insert(self, segments):
        """把 ``[(文本, format)]`` 追加到末尾（format 为 None 表示跟随主题）。

        ⚠️ 必须走**控件自己的光标**（``moveCursor`` + ``setCurrentCharFormat`` +
        ``insertPlainText``），不能另建 ``QTextCursor`` 直接插：那样控件不会跟着滚动 ——
        实测追加 300 行后滚动条仍停在顶部（另建的 cursor 与控件光标无关）。
        ⚠️ 每段都要显式 ``setCurrentCharFormat``：当前格式会一直生效，不设置的话下一段
        会继承上一段的颜色。
        """
        self.text_browser.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        for text, fmt in segments:
            if len(text) > 0:
                self.text_browser.setCurrentCharFormat(
                    QtGui.QTextCharFormat() if fmt is None else fmt)
                self.text_browser.insertPlainText(text)
        self._trim()

    def _trim(self):
        """字符数超过 :attr:`MAX_CHARS` 时，从头丢掉一半。

        ⚠️ 必须用光标删除。早先是 ``toPlainText()`` / ``setPlainText()`` 整篇重写，那会把
        所有段落的格式**统一成当前格式**（实测整篇变成同一个颜色），而且每次追加都要复制
        近万个字符；光标删除保留其余文本的格式，也更快。
        """
        doc = self.text_browser.document()
        while doc.characterCount() > self.MAX_CHARS:
            cursor = QtGui.QTextCursor(doc)
            cursor.setPosition(0)
            cursor.setPosition(
                doc.characterCount() // 2,
                QtGui.QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()

    def set_text(self, text):
        self.text_browser.clear()
        self._ansi_fmt = QtGui.QTextCharFormat()
        self._ansi_pending = ''
        self._line_pending = ''
        self.add_text(text)

    #: 历史文件扩展名。用 HTML 而不是 txt：颜色 / 粗体等是存在文本片段的
    #: ``QTextCharFormat`` 里的，``toPlainText()`` 会把它们**全部丢掉**，于是重启后
    #: 只剩无色文本（2026-10-26 修的就是这个）；``toHtml()`` 才能把它们写进文件。
    SUFFIX = '.html'
    #: 非 HTML 的老历史文件（旧版本存的是纯文本）
    SUFFIX_LEGACY = '.txt'

    def load_text(self, filename):
        """从历史文件恢复输出内容（``.html`` 保留颜色，``.txt`` 按纯文本解析）。

        Args:
            filename: 历史文件路径。按**扩展名**决定走富文本还是纯文本 —— 旧版本存的
                是 ``.txt``（纯文本，颜色本就已丢失），仍要能打开。
        """
        try:
            if os.path.isfile(filename):
                # ⚠️ 必须显式 encoding='utf-8'：默认会用系统编码（中文 Windows 上是 GBK），
                #    而文件是 UTF-8 写的，含中文时抛 UnicodeDecodeError（被下面的 except
                #    吞成空内容，现场表现为「历史加载不出来」）。
                if str(filename).lower().endswith(self.SUFFIX):
                    self.set_html(filename)
                else:
                    with open(filename, 'r', encoding='utf-8') as file:
                        self.set_text(file.read())
        except Exception as err2:
            print(err2)
            self.text_browser.setPlainText('')

    def save_text(self, filename):
        """把当前输出保存为历史文件（``.html`` 保留颜色，其余按纯文本保存）。

        ⚠️ 保存前先 :meth:`flush_pending`：否则被行缓冲扣住的最后半行不会写进历史。
        ⚠️ **历史里存的图片路径是原图**（见 :meth:`get_html`）：图片本体仍在调用者那里。
        """
        try:
            self.flush_pending()
            text = (self.get_html()
                    if str(filename).lower().endswith(self.SUFFIX)
                    else self.text_browser.toPlainText())
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(text)
        except Exception as err2:
            print(err2)

    def get_html(self):
        """返回当前输出的 HTML（保留颜色 / 粗体等全部字符格式）。

        ⚠️⚠️ **图片的 ``src`` 会被换成原图路径**（2026-11-02）：``toHtml()`` 只会把
        ``QTextImageFormat.name``（渲染用的**预览缓存**路径）写进 ``src``，而自定义属性
        :attr:`IMAGE_PROP` **不落盘** —— 直接存下去，历史里就只剩一串哈希文件名，
        「真正记录的永远是原图」这条就不成立了。

        所以这里把每张图的 ``src`` 改写成它的原图路径：缓存随时能由原图重新算出来
        （:meth:`_preview_of`），而原图路径**推不回缓存** —— 该存哪一个不言自明。
        恢复时由 :meth:`_rebind_images` 再换回缓存路径，两边一一对应。
        """
        html = self.text_browser.toHtml()
        return self._html_with_original_src(html)

    def _html_with_original_src(self, html):
        """把 ``html`` 里每张内嵌图的 ``src``（预览缓存）换成原图路径."""
        try:
            doc = self.text_browser.document()
            # 文档里渲染路径 → 原图路径；同一个缓存文件只可能对应一张原图
            mapping = {}
            block = doc.begin()
            while block.isValid():
                it = block.begin()
                while not it.atEnd():
                    frag = it.fragment()
                    if frag.isValid() and frag.charFormat().isImageFormat():
                        fmt = frag.charFormat()
                        origin = fmt.property(self.IMAGE_PROP)
                        shown = fmt.toImageFormat().name()
                        if shown and isinstance(origin, str) and origin and shown != origin:
                            mapping[shown] = origin
                    it += 1
                block = block.next()
            if not mapping:
                return html

            def replace(match):
                head, src, tail = match.group(1), match.group(2), match.group(3)
                origin = mapping.get(src)
                if origin is None:
                    return match.group(0)
                # ⚠️ 不用做 HTML 转义：实测 toHtml() 写出的 src 就是**裸绝对路径**
                #    （不是 file://、反斜杠不转义、中文原样），setHtml() 也是按裸路径读回的
                return f'{head}{origin}{tail}'

            return re.sub(r'(<img\b[^>]*?\bsrc=")([^"]*)(")',
                          replace, html, flags=re.IGNORECASE)
        except Exception as err:  # 换不成也不要紧：退化成「src 是缓存路径」
            print(f'Error when rewritting image src: {err}')
            return html

    def set_html(self, filename):
        """用历史 HTML 文件的内容替换当前输出（保留颜色 / 粗体等字符格式）。

        ⚠️ 与 :meth:`set_text` 一样要复位 :attr:`_ansi_fmt` / :attr:`_ansi_pending`：
        否则重启后第一条 ``print`` 会**继承**上一份输出残留的 ANSI 状态，把新内容
        染成旧颜色。

        ⚠️ **恢复后要把图片的渲染路径重新算一遍**（:meth:`_rebind_images`）：
        HTML 里存的 ``src`` 是**原图路径**（``toHtml()`` 只写得出 ``name``，自定义属性
        不落盘），而大图渲染要用预览缓存 —— 不重算的话，恢复出来的大图会让
        ``QTextDocument`` 按原分辨率解码，正是本机制要避免的那件事。
        """
        if not os.path.isfile(filename):
            return
        with open(filename, 'r', encoding='utf-8') as file:
            html = file.read()
        self.text_browser.setHtml(html)
        try:
            self._rebind_images()
        except Exception as err:  # 理论上到不了：_rebind_images 内部已兜住
            # ⚠️ 「重新算预览缓存」失败不算错，更不许卡住（2026-11-03）：回到刚 setHtml
            #    的文档（图片按原图路径显示，与旧行为一致），绝不让异常冒到调用方 ——
            #    这个调用点在启动的关键路径上（main.__restore_history），那时启动画面
            #    还挡着，一抛就是「卡在启动画面」。
            print(f'Error when rebinding images: {err}')
            try:
                self.text_browser.setHtml(html)  # 回滚成「图片按原图路径显示」
            except Exception:
                pass
        self._ansi_fmt = QtGui.QTextCharFormat()
        self._ansi_pending = ''
        self._line_pending = ''

    def _rebind_images(self):
        """按 ``src`` 把每张内嵌图重新绑定到「原图 + 预览缓存」，并刷新显示尺寸.

        ``setHtml`` 恢复出来的文档里，图片的 ``name`` 就是原图路径（历史 HTML 里只有它）。
        这里逐张把它当作**原图**处理：

        1. 记进 :attr:`IMAGE_PROP`（「这张图是谁」永远是原图）；
        2. 算出预览缓存（不存在就创建），写回 ``name``（渲染用它）；
        3. 保持文档里已存的显示宽高不变 —— 历史 HTML 里存的就是当时的显示尺寸。

        ⚠️ 原图已经不存在的，**什么都不改**：让它在原位置显示不出来即可，
        不做假数据、也不删掉那一行。用户仍能从灰色说明行里看到路径。

        ⚠️⚠️ **所有耗时的计算都在编辑块之外先做完**（2026-11-03）：编辑块内每改一次
        图片的字符格式，``QTextDocument`` 都可能立刻去加载 / 重排那张图 —— 把
        「解码 + 生成预览缓存」留在里面，历史里每多一张大图就多一次同步阻塞，启动时
        表现为**启动画面永远不消失**（2026-11-03 定位到 GUI 线程死在这一步上）。
        现在先收集 ``[(位置, 长度, 新格式)]``，再在一个编辑块里逐项写入，每张图仍只写一次。

        ⚠️⚠️ **只认「真正读得出来的图片」**（2026-11-03 实测踩到）：文档里只要有一张
        ``<img>`` 指向**不是图片的文件**（历史 HTML 被改坏、指向 ``.exe`` 等），在编辑块里
        重新设置它的格式后 ``QTextDocument`` 会**无限重排** —— 实测 GUI 线程死循环、
        ``os.path.isfile`` 之后再也没返回。所以这里先用 :meth:`_image_size` 确认「文件头
        说得清宽高」，读不出来的**原样不动**（渲染成裂图即可，与旧行为一致），
        绝不参与重新绑定。
        """
        try:
            doc = self.text_browser.document()
            plan = []
            block = doc.begin()
            while block.isValid():
                it = block.begin()
                while not it.atEnd():
                    frag = it.fragment()
                    if frag.isValid() and frag.charFormat().isImageFormat():
                        # ⚠️ PyQt6 里 **没有** QTextImageFormat(QTextCharFormat) 这个构造
                        #    重载（实测报 "argument 1 has unexpected type"），只能先拷贝成
                        #    QTextCharFormat / QTextImageFormat 再改属性。
                        fmt = QtGui.QTextImageFormat(frag.charFormat().toImageFormat())
                        origin = fmt.name()
                        if origin and self._image_size(origin) is None:
                            continue  # 不是图片 / 读不出来：原样不动，绝不重新设置格式
                        if origin and os.path.isfile(origin):
                            shown = self._preview_of(origin)  # 计时的大头：在这里、在编辑块外
                            if shown is None:
                                continue
                            # ⚠️ 属性**无条件**写回：哪怕预览路径和原图相同（小图），
                            #    「这张图是谁」也必须记下来 —— 否则恢复后的图双击会
                            #    拿着渲染路径当原图（2026-11-02 实测踩到）。
                            fmt.setName(shown)
                            fmt.setProperty(self.IMAGE_PROP, os.path.abspath(origin))
                            plan.append((frag.position(), frag.length(), fmt))
                    it += 1
                block = block.next()
            if not plan:
                return
            cursor = QtGui.QTextCursor(doc)
            cursor.beginEditBlock()
            for position, length, fmt in plan:
                cursor.setPosition(position)
                cursor.setPosition(
                    position + length,
                    QtGui.QTextCursor.MoveMode.KeepAnchor)
                cursor.setCharFormat(fmt)
            cursor.endEditBlock()
        except Exception as err:  # 恢复失败不该让历史打不开
            print(f'Error when rebind images: {err}')

    @classmethod
    def _preview_of(cls, path):
        """原图路径 → **应当渲染的文件**：大图给预览缓存（不存在就创建），小图就是原图.

        ⚠️ 这是「怎么显示」的唯一入口，:meth:`_add_image` 与 :meth:`_rebind_images`
        都走它 —— 两条路径的显示逻辑只有一份。
        ⚠️ 原图不存在 / 不是图片 / 超过 30 MB / 缓存创建失败时一律返回 ``None``，
        调用方据此退化成文本或不改。
        ⚠️ **计算失败绝不抛异常**（2026-11-03）：本函数是 ``_rebind_images`` 与文档重绘
        都会碰到的地方，抛出去就没人接，最坏的结果是界面卡死 —— 所以任何异常一律
        当作「没有预览」，退化成原图。
        """
        try:
            nbytes = os.path.getsize(path)
        except Exception:
            return None
        try:
            if _ImageFit.is_too_large(nbytes):
                return None
            size = cls._image_size(path)
            if size is None:
                return None
            if not _ImageFit.needs_cache(*size):
                return os.path.abspath(path)
            return cls._cached_image_size(path)
        except Exception:
            return None

    def get_image_count(self):
        """返回文档里**内嵌图片**的个数（自测 / 诊断用；不参与任何业务判断）."""
        try:
            doc = self.text_browser.document()
            count = 0
            block = doc.begin()
            while block.isValid():
                it = block.begin()
                while not it.atEnd():
                    fragment = it.fragment()
                    if fragment.isValid() and fragment.charFormat().isImageFormat():
                        count += 1
                    it += 1
                block = block.next()
            return count
        except Exception:
            return 0

    def get_plain_text(self):
        return self.text_browser.toPlainText()


def test_1():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = OutputWidget()
    w.resize(800, 600)
    w.show()

    # 示例数据：能看出控件的主要能力（ANSI 上色 + 过滤不支持的序列）
    w.add_text('普通文本  \033[31m红\033[32m绿\033[33m黄\033[34m蓝\033[0m 普通文本\n')
    w.add_text('\033[1;31m粗体红\033[0m \033[4m下划线\033[24m \033[3m斜体\033[23m\n')
    w.add_text('\033[38;5;208m256 色\033[0m \033[38;2;255;0;255m真彩\033[39m\n')
    w.add_text('不支持的序列会被删除: [\033[2J\033[1;1H\033[K]\033]0;标题\007<\n')
    w.add_text('被切断的序列也能续上: \033[3' + '5m紫色\033[0m\n')

    # 示例图片：**只造在临时目录里**（AGENTS.md §4：test_1 不落盘到用户目录）
    import tempfile
    folder = tempfile.mkdtemp(prefix='zml_output_images_')
    wide = os.path.join(folder, 'wide.png')
    tall = os.path.join(folder, 'tall.png')
    for path, (width, height), color in (
            (wide, (1600, 400), '#3366cc'),
            (tall, (300, 1200), '#cc6633')):
        image = QtGui.QImage(width, height, QtGui.QImage.Format.Format_RGB32)
        image.fill(QtGui.QColor(color))
        image.save(path)

    w.add_text('\n== 图片标记 ==\n')
    w.add_text(f'[[image: path="{wide}"]]\n')       # 宽图：按宽度适配
    w.add_text(f'[[image: path="{tall}"]]\n')       # 高图：收窄，保证整张可见
    w.add_text(f'[[image: {wide}, w=200]]\n')       # 裸路径 + 显式宽度
    w.add_text(f'[[image: path="{wide}", w=99999]]\n')  # 超宽请求：不得撑开窗口
    w.add_text('[[image: 不存在的图片.png]]\n')      # 缺图：原位显示文本行
    w.add_text('这一行不是标记（行内有 [[image: a.png]]）：应原样显示\n')

    sys.exit(app.exec())


if __name__ == "__main__":
    test_1()
