"""Markdown 查看器控件（支持自定义超链接点击响应）.

对外只暴露两个公开方法:

- ``set_markdown(text)``: 设置要显示的 Markdown 字符串
- ``set_link_callback(fn)``: 设置超链接点击回调. ``fn(url)`` 返回真值表示
  回调已经自行处理, 控件不再执行默认动作; 返回假值（或未设置回调、
  回调传入 ``None``）时执行默认动作: 文档内锚点原地跳转（``#锚点``, 两种渲染
  路径下都可用）, 其余链接交给系统浏览器（在 IGG-Hydrate 里则是 GUI 标签页）打开.

**默认优先用第三方 ``markdown`` 库**: 设置 ``MarkdownView.SETTING_KEY``（即
``md_by_html``）默认为 ``'Yes'`` —— 只要装了 ``markdown`` 库, 就把 md 转成 HTML 再
``setHtml`` 渲染（表格 / 脚注 / 自定义 CSS 等效果更完整）; 没装则回退到 Qt 自带的
``QTextBrowser.setMarkdown()``, 并提醒一次. 把该项写成 ``'No'`` 可以强制只用 Qt 实现.
该设置由 ``app_data.getenv`` 读取, 每次渲染时重新读取, 因此改完设置再
``set_markdown()`` 即可生效.

右键菜单里有一项可勾选的渲染方式开关（写入设置, 跨进程保留）, 但**只有在装了
``markdown`` 库时这一项才存在**; 没装就压根不显示. 该库不在模块顶层导入: 只有
真的要渲染 HTML 时才按需导入.

本文件是新增文件; 已在 ``zmlx/ui/widget/__init__.py`` 里注册, 可以直接::

    from zmlx.ui.widgets import MarkdownView

Created by DeepSeek, 2026-10-06
"""

import importlib.util
import os
import re
import sys

if __name__ == '__main__':  # 直接运行本文件时, 把仓库根目录加入搜索路径
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))))

from zmlx.system import app_data
from zmlx.ui.alg import create_action
from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets
from zmlx.ui.widgets.text_browser import TextBrowser


class MarkdownView(TextBrowser):
    """Markdown 查看控件（``QTextBrowser`` 子类, 支持自定义链接点击响应）.

    继承 :class:`~zmlx.ui.widgets.text_browser.TextBrowser`, 因此同样带有
    "清除内容"右键菜单与 ``set_status`` 状态栏提示.

    Attributes:
        SETTING_KEY: 渲染方式设置的名字（``app_data`` 的键）. 默认 ``'Yes'``：装了第三方
            ``markdown`` 库就优先用它转 HTML 渲染; 写成 ``'No'`` 则强制只用 Qt 自带的
            ``setMarkdown``. 库没装时自动回退到 Qt 实现.

    Example:
        >>> view = MarkdownView()
        >>> view.set_markdown('# 标题\\n\\n[主页](https://gitee.com/geomech/hydrate)')
        >>> view.set_link_callback(lambda url: (print(url), True)[1])
    """

    SETTING_KEY = 'md_by_html'

    def __init__(self, parent=None):
        super().__init__(parent)
        self._markdown = ''
        self._base_url = None
        self._link_callback = None
        self._html_action = None
        self._warned_no_lib = False  # 设置要库、但库不在时, 只提醒一次
        # 关闭内置导航, 改由 anchorClicked 信号统一分发:
        # 这样"点击链接之后做什么"完全可控, 也才能插入用户回调.
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        self.anchorClicked.connect(self._on_anchor_clicked)
        self._add_html_action()

    # ------------------------------------------------------------------
    # 公开接口（两个）
    # ------------------------------------------------------------------
    def set_markdown(self, text, base_url=None):
        """设置要显示的 Markdown 字符串.

        Args:
            text: Markdown 源码. 传入 ``None`` 等价于空字符串; 可重复调用.
            base_url: 文档中相对链接/图片的基准位置（可选）. 目录路径按本地
                目录处理, 文件路径按该文件处理, 其余按 URL 处理
                （如 ``'https://gitee.com/geomech/'``）.
        """
        self._markdown = '' if text is None else str(text)
        self._base_url = base_url
        self._apply_base_url()
        self._render()

    def set_link_callback(self, callback):
        """设置超链接点击之后的回调函数.

        Args:
            callback: ``fn(url: str) -> bool``, 其中 ``url`` 是链接目标地址
                （如 ``'https://...'``、``'#第5节'``、``'zmlx://demo'``）.
                返回真值表示回调已自行处理, 控件不再执行默认动作; 返回假值
                或未设置回调时, 控件执行默认动作. 传入 ``None`` 表示清除回调.

        Raises:
            ValueError: ``callback`` 既不是 ``None`` 也不是可调用对象.
        """
        if callback is not None and not callable(callback):
            raise ValueError('link callback must be callable or None')
        self._link_callback = callback

    # ------------------------------------------------------------------
    # 渲染方式设置, 以及可选的第三方库
    # ------------------------------------------------------------------
    def _md_by_html(self, value=None):
        """读取 / 写入「是否用第三方 markdown 库转 HTML 渲染」的设置.

        Args:
            value: ``None`` 表示读取; 传入布尔值则写入设置（由 ``app_data.setenv``
                落到磁盘, 下次启动仍然生效）.

        Returns:
            bool: 是否允许用 markdown 库渲染. 默认 ``True`` —— 装了库就优先用它;
            只有显式写成 ``'No'`` 才强制走 Qt 自带的 ``setMarkdown``.
        """
        try:
            if value is not None:
                app_data.setenv(key=self.SETTING_KEY, value='Yes' if value else 'No')
            text = app_data.getenv(key=self.SETTING_KEY, default='Yes', ignore_empty=True)
        except Exception as err:  # 读不到设置时按默认处理, 不影响显示
            print(f'Warning: failed to read/write setting <{self.SETTING_KEY}>: {err}')
            return True
        return str(text).strip().lower() != 'no'

    def _has_markdown(self):
        """第三方 ``markdown`` 库是否已安装（用 ``find_spec`` 判断, **不导入**）.

        ``find_spec`` 只查 ``sys.path``（importlib 自带缓存, 开销极小）, 不执行这个库,
        因此每次调用都没有副作用, 也就不需要额外的缓存变量. 只有为真时, 右键菜单里
        才会出现渲染方式开关.

        Returns:
            bool: 已安装为 ``True``.
        """
        try:
            return importlib.util.find_spec('markdown') is not None
        except Exception as err:
            print(f'Warning: failed to look up the optional module <markdown>: {err}')
            return False

    def _get_markdown(self):
        """按需导入可选的第三方 ``markdown`` 库（不在模块顶层导入）.

        只会在设置要求 HTML 渲染、并且 :meth:`_has_markdown` 已确认库存在时被调用, 所以
        这里的失败基本只剩"装了但装坏了"这一种可能; 仍然告警并返回 ``None``, 由调用方
        回退到 Qt 自带的 ``setMarkdown()``. 反复调用没有额外开销 —— 已导入的模块在
        ``sys.modules`` 里, 函数内的 ``import`` 只是一次字典查找.

        Returns:
            ``markdown`` 模块; 不可用时返回 ``None``.
        """
        try:
            import markdown
        except Exception as err:  # 未安装(或安装已损坏)都按"不可用"处理
            print(f'Warning: the optional module <markdown> is not available: {err}\n'
                  f'可选的 markdown 库不可用, MarkdownView 将回退到 Qt 自带的 setMarkdown。\n'
                  f'如需完整效果, 请运行:  pip install markdown')
            return None
        return markdown

    def _use_html(self):
        """当前是否用第三方库转 HTML 渲染: 设置允许 **且** 库真的可用.

        默认设置是 ``'Yes'``: 装了 ``markdown`` 库就优先用它（表格/脚注/自定义 CSS 更完整）;
        没装就回退到 Qt 自带的 ``setMarkdown``, 并提醒一次（每个控件一次, 免得刷屏）。
        把设置写成 ``'No'`` 可以强制只用 Qt 的实现.
        """
        if not self._md_by_html():
            return False
        if self._has_markdown():
            return True
        if not self._warned_no_lib:
            self._warned_no_lib = True
            print(f'MarkdownView: 环境里没有可选的 markdown 库, 本次用 Qt 自带的 setMarkdown 渲染;'
                  f' 装上之后会自动优先用它（pip install markdown）。\n'
                  f'要固定用 Qt 实现, 把设置 {self.SETTING_KEY} 改成 No:'
                  f' {app_data.root("env", self.SETTING_KEY)}')
        return False

    # ------------------------------------------------------------------
    # 右键菜单里的渲染方式开关
    # ------------------------------------------------------------------
    def _add_html_action(self):
        """装了 ``markdown`` 库时, 在右键菜单里加一个渲染方式开关; 没装则不加."""
        if not self._has_markdown():
            return
        action = create_action(self, '用 markdown 库渲染（md → HTML）',
                               slot=self._toggle_html)
        action.setCheckable(True)
        action.setChecked(self._use_html())
        action.setToolTip(
            f'勾选: 用第三方 markdown 库转成 HTML 后再渲染（表格/脚注/CSS 更完整）;\n'
            f'不勾选: 只用 Qt 自带的 setMarkdown。\n'
            f'该开关写入设置 {self.SETTING_KEY}, 跨进程保留。')
        self._html_action = action
        self.context_actions.append(action)

    def _toggle_html(self):
        """右键菜单回调: 切换渲染方式, 并立即按新方式重画当前内容."""
        use = bool(self._html_action is not None and self._html_action.isChecked())
        self._md_by_html(use)
        self._render()
        print(f'MarkdownView: 渲染方式已切换为 '
              f'{"markdown 库 -> setHtml" if use else "Qt 自带 setMarkdown"}'
              f' ({self.SETTING_KEY}={self._md_by_html()})')

    # ------------------------------------------------------------------
    # 渲染
    # ------------------------------------------------------------------
    def _render(self):
        """把当前 Markdown 源码渲染到控件中.

        默认走 Qt 自带的解析器; 只有设置打开且第三方库可用时, 才改成
        「库 -> HTML -> setHtml」（这样自定义样式表才生效）.
        """
        if self._use_html():
            body = self._to_html_body(self._markdown)
            if body is not None:
                self.document().setDefaultStyleSheet(self._style_sheet())
                self.setHtml(body)
                return
        # 默认 / 回退: Qt 自带的 Markdown 解析器（Qt >= 5.14 提供 setMarkdown）
        set_markdown = getattr(self, 'setMarkdown', None)
        if set_markdown is not None:
            # 补全未自闭合的空元素, 否则 <img> 之后的内容会被 Qt 整段吞掉
            set_markdown(self._close_void_tags(self._markdown))
        else:
            self.setPlainText(self._markdown)

    def _apply_base_url(self):
        """按 ``base_url`` 设置文档基准位置与图片搜索路径."""
        base_url = self._base_url
        if base_url is None:
            self.setSearchPaths([])
            self.document().setBaseUrl(QtCore.QUrl())
            return
        path = os.path.abspath(base_url)
        if os.path.isdir(path):
            self.setSearchPaths([path])
            self.document().setBaseUrl(QtCore.QUrl.fromLocalFile(path + os.sep))
        elif os.path.isfile(path):
            self.setSearchPaths([os.path.dirname(path)])
            self.document().setBaseUrl(QtCore.QUrl.fromLocalFile(path))
        else:
            self.setSearchPaths([])
            self.document().setBaseUrl(QtCore.QUrl(base_url))

    def _style_sheet(self):
        """按当前调色板生成样式, 让深色/浅色主题下都能正常阅读（仅 HTML 路径生效）."""
        palette = self.palette()
        text = palette.color(QtGui.QPalette.ColorRole.Text)
        link = palette.color(QtGui.QPalette.ColorRole.Link)
        dark = palette.color(QtGui.QPalette.ColorRole.Base).lightness() < 128
        code_bg = '#3c3c3c' if dark else '#f0f0f0'
        border = '#5a5a5a' if dark else '#d0d0d0'
        quote_fg = '#b8b8b8' if dark else '#606060'
        return f'''
        body {{ color: {text.name()}; }}
        p {{ margin: 6px 0; }}
        h1 {{ font-size: 22px; margin: 14px 0 8px 0; }}
        h2 {{ font-size: 18px; margin: 12px 0 6px 0; }}
        h3 {{ font-size: 16px; margin: 10px 0 6px 0; }}
        a {{ color: {link.name()}; }}
        code {{ background-color: {code_bg}; font-family: Consolas, "Courier New", monospace; }}
        pre {{ background-color: {code_bg}; padding: 8px; }}
        blockquote {{ color: {quote_fg}; margin-left: 18px; }}
        th, td {{ border: 1px solid {border}; padding: 3px 8px; }}
        '''

    def _to_html_body(self, text):
        """用第三方 ``markdown`` 库把源码转成 HTML 片段; 库不可用时返回 ``None``."""
        md = self._get_markdown()
        if md is None:
            return None
        if len(text) == 0:
            return ''
        try:
            # extra: 表格/围栏代码块/脚注/attr_list; sane_lists: 更严格的列表解析
            body = md.markdown(text, extensions=['extra', 'sane_lists'])
        except Exception as err:
            print(f'Warning: failed to convert markdown to html: {err}')
            return None
        return self._ensure_heading_ids(body)

    def _ensure_heading_ids(self, body):
        """给标题补 ``id``, 保证 ``[文字](#锚点)`` 能在文档内原地跳转.

        Qt 的富文本引擎会把标题的 ``id`` 注册成锚点（``scrollToAnchor`` 可用, 已实测）,
        因此只要保证每个标题都带 id 就够了; 若标题已由 attr_list 显式指定 ``id``, 则沿用.

        刻意不用 ``<a name="...">``: Qt 会把该锚点的字符格式顺延到标题的**第一个字符**
        上, 于是标题首字符变成 href 为空的"链接"（点它会触发一次 anchorClicked）.
        """
        heading = re.compile(r'<(h[1-6])([^>]*)>(.*?)</\1>', re.DOTALL)
        explicit_id = re.compile(r'id="([^"]+)"')

        def repl(match):
            tag, attrs, inner = match.group(1), match.group(2), match.group(3)
            if explicit_id.search(attrs) is not None:
                return match.group(0)
            name = self._slugify(inner)
            if len(name) == 0:
                return match.group(0)
            return f'<{tag}{attrs} id="{name}">{inner}</{tag}>'

        return heading.sub(repl, body)

    def _slugify(self, text):
        """标题文本 -> 锚点名: 保留中文, 转小写, 标点去掉, 空白转 ``-``.

        刻意不使用 markdown 自带 ``toc`` 扩展的默认 slugify: 它会把非 ASCII 字符
        整段丢掉, 于是 ``## 5. 关于自定义协议`` 只会得到 ``id="5"``, 中文标题之间
        还会互相撞车.
        """
        text = re.sub(r'<[^>]+>', '', text).lower()
        text = re.sub(r'[^\w\s-]', '', text)
        return re.sub(r'\s+', '-', text).strip('-')

    def _close_void_tags(self, text):
        """把 ``<img src=...>`` 这类**未自闭合**的空元素补成 ``<img src=... />``.

        只为绕开 Qt 的 Markdown 导入器(md4c)的一个坑: 它遇到未自闭合的空元素, 会把它
        当成一个没有结束的 HTML 块, 把其后**整篇文档**都吞掉. 实测::

            AAA\\n\\n<img src=x>\\n\\nBBB   ->  Qt 路径下只剩 AAA
            AAA\\n\\n<img src=x />\\n\\nBBB ->  正常

        围栏代码块（``` / ~~~）与行内代码（反引号）里的内容原样保留, 免得把代码示例改了;
        缩进式代码块不做特殊处理. 标签允许跨行书写.
        """
        void_tag = re.compile(r'<(area|base|br|col|embed|hr|img|input|link|meta|param|'
                              r'source|track|wbr)(\s[^<>]*?)?\s*(/?)>', re.IGNORECASE)
        fence_open = re.compile(r'^\s*(`{3,}|~{3,})')       # 围栏开始(可带语言标记)
        fence_close = re.compile(r'^\s*(`{3,}|~{3,})\s*$')  # 围栏结束(只有围栏字符)
        inline_code = re.compile(r'`+[^`\n]*`+')  # ⚠️ 不跨行, 免得配出很长的假区间

        def fix(match):
            tag, attrs, slash = match.group(1), match.group(2) or '', match.group(3)
            if len(slash) > 0:
                return match.group(0)
            return f'<{tag}{attrs} />'

        def fix_text(chunk):
            """给一段正文补自闭合斜杠; 跳过其中的行内代码."""
            spans = [(m.start(), m.end()) for m in inline_code.finditer(chunk)]
            parts = []
            last = 0
            for match in void_tag.finditer(chunk):
                if any(start <= match.start() < end for start, end in spans):
                    continue
                parts.append(chunk[last:match.start()])
                parts.append(fix(match))
                last = match.end()
            parts.append(chunk[last:])
            return ''.join(parts)

        # 按围栏代码块切分. ⚠️ 围栏那一行本身算代码块的一部分: 若把它留在正文片段里,
        # 它开头的三个反引号会被当成行内代码的起点, 与后面某个反引号配成一段很长的假
        # 代码区间, 让本该补全的空元素被跳过（实测踩过: 整篇演示文档的第 7 节因此被吞）。
        chunks = []
        buf = []
        in_fence = False
        for line in text.splitlines(keepends=True):
            if in_fence:
                buf.append(line)
                if fence_close.match(line) is not None:
                    chunks.append(''.join(buf))
                    buf = []
                    in_fence = False
            elif fence_open.match(line) is not None:
                chunks.append(fix_text(''.join(buf)))
                buf = [line]
                in_fence = True
            else:
                buf.append(line)
        chunks.append(''.join(buf) if in_fence else fix_text(''.join(buf)))
        return ''.join(chunks)

    # ------------------------------------------------------------------
    # 链接点击
    # ------------------------------------------------------------------
    def _on_anchor_clicked(self, url):
        """内部槽: 分发超链接点击（先问回调, 未处理时执行默认动作）."""
        text = url.toString()
        callback = self._link_callback
        if callback is not None:
            try:
                if callback(text):
                    return
            except Exception as err:  # 回调异常不应打断界面
                print(f'Warning: markdown link callback failed for <{text}>: {err}')
        self._default_link_action(url)

    def _default_link_action(self, url):
        """默认动作: 文档内锚点原地跳转, 其余交给系统打开."""
        if len(url.scheme()) == 0 and len(url.path()) == 0 and len(url.fragment()) > 0:
            self._scroll_to_anchor(url.fragment())
            return
        text = url.toString()
        if len(text) == 0:
            # 空目标(例如 Markdown 里的 [文字]() )不做任何事: 否则 open_url('')
            # 会让浏览器打开一个空白页.
            return
        try:
            from zmlx.ui.alg import open_url  # 项目统一入口: GUI 标签页/系统浏览器
            open_url(text)
        except Exception as err:
            print(f'Warning: failed to open <{text}>: {err}')
            QtGui.QDesktopServices.openUrl(url)

    def _scroll_to_anchor(self, fragment):
        """跳到文档内锚点.

        先走 Qt 的 ``scrollToAnchor``; 它找不到时（Qt 自带的 Markdown 导入器不会为标题
        建立命名锚点）再按标题文本用同样的 :meth:`_slugify` 规则搜索, 保证两种渲染路径下
        ``[文字](#锚点)`` 都能原地跳转.
        """
        bar = self.verticalScrollBar()
        before = bar.value()
        self.scrollToAnchor(fragment)
        if bar.value() != before:
            return
        block = self.document().begin()
        while block.isValid():
            if block.blockFormat().headingLevel() > 0:
                if self._slugify(block.text()) == fragment:
                    self.setTextCursor(QtGui.QTextCursor(block))
                    self.ensureCursorVisible()
                    return
            block = block.next()


def test_1():
    """直接运行本文件时的演示: 显示示例 Markdown, 并演示两个公开方法."""
    # 演示用的内容只放在这个函数内部, 不占用模块级命名空间
    icons = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'zml_icons')
    demo_md = '''# MarkdownView 控件演示

这是一个**独立可用**的 Markdown 查看控件, 只暴露两个公开方法:

- `set_markdown(text)`: 设置要显示的 Markdown 字符串
- `set_link_callback(fn)`: 设置超链接点击之后的回调函数

## 1. 排版效果

普通段落。行内代码 `view.set_markdown(text)`, **粗体**, *斜体*, 以及
[带下划线的链接](#1-排版效果)。

> 引用块: 点击下面的链接, 观察窗口底部的"链接点击记录"。

## 2. 表格

| 链接类型 | 回调返回值 | 控件的动作 |
| --- | --- | --- |
| `zmlx://` 自定义协议 | `True` | 回调自己弹窗处理, 控件不再做别的 |
| `#` 文档内锚点 | `False` | 滚动到本文档内对应的标题 |
| `https://` 外部链接 | 见下方复选框 | 交给系统浏览器打开 |

## 3. 代码块

```python
view = MarkdownView()
view.set_markdown(text)          # 方法一: 设置 md 字符串
view.set_link_callback(on_link)  # 方法二: 设置点击链接的回调
```

## 4. 各种链接

- 外部链接: [IGG-Hydrate 主页](https://gitee.com/geomech/hydrate)
- 自定义协议: [zmlx://demo/hello](zmlx://demo/hello)
- 文档内锚点: [跳到第 5 节](#5-关于自定义协议)

## 5. 关于自定义协议

`zmlx://` 之类的自定义协议, 由 `set_link_callback` 注册的回调处理;
只要回调返回 `True`, 控件就不会打开任何外部程序。

取消勾选下面的"启用超链接回调", 就等于调用 `set_link_callback(None)`,
这时所有链接都走控件的默认动作。

## 6. 图片

下面这些图标来自 `zmlx/ui/data/zml_icons`。Markdown 里只写文件名, 基准目录由
`set_markdown(text, base_url=...)` 给出:

![console](console.jpg) ![demo](demo.jpg) ![python](python.jpg) ![matplotlib](matplotlib.jpg)
![home](home.jpg) ![info](info.jpg) ![save](save.jpg) ![stop](stop.jpg)
![refresh](refresh.jpg) ![cwd](cwd.jpg) ![gitee_hydrate](gitee_hydrate.jpg) ![reg](reg.jpg)

表格里同样可以放图片:

| 图标 | 说明 | 图标 | 说明 |
| --- | --- | --- | --- |
| ![cwd](cwd.jpg) | 当前目录 | ![demo](demo.jpg) | Demo 浏览器 |
| ![console](console.jpg) | 控制台 | ![matplotlib](matplotlib.jpg) | 绘图 |

需要控制显示大小时, 可以直接写行内 HTML（见第 7 节, 仅 markdown 库路径有效）:

<img src="export.jpg" width="180"> <img src="iggcas.jpg" width="80"> <img src="clock.jpg" width="56">

## 7. 渲染方式（默认优先用 markdown 库）

本控件**默认优先用第三方 `markdown` 库**渲染（md → HTML → `setHtml`）：只要环境里装了这个库，
表格、脚注、定义列表、attr_list、自定义 CSS（代码块底色、引用块配色）都齐全; 没装则自动回退到
Qt 自带的 `setMarkdown`（表格、删除线、任务列表、图片（Markdown 语法）也都有，但自定义 CSS 无效）。

在正文里点右键，菜单中会有一项可勾选的「用 markdown 库渲染（md → HTML）」：

- 勾选（默认）：`markdown` 库转 HTML 后用 `setHtml` 渲染;
- 不勾选：只用 Qt 自带的 `setMarkdown`。

开关会写入设置 `md_by_html`, 跨进程保留; 改完立即按新方式重画当前内容。
**没装 `markdown` 库时, 这一项不会出现**（此时只能用 Qt 的实现）。
'''

    app = QtWidgets.QApplication(sys.argv)

    window = QtWidgets.QWidget()
    window.setWindowTitle('MarkdownView 演示')
    window.resize(900, 680)
    layout = QtWidgets.QVBoxLayout(window)

    view = MarkdownView()
    view.set_status('MarkdownView 演示')
    layout.addWidget(view, 1)

    # ---- 演示 set_link_callback: 回调的返回值决定控件是否执行默认动作 ----
    check_allow_http = QtWidgets.QCheckBox(
        '回调放行 https 链接 (返回 False -> 默认动作: 系统浏览器打开)')
    check_callback = QtWidgets.QCheckBox('启用超链接回调 set_link_callback(fn)')
    check_callback.setChecked(True)
    button_reload = QtWidgets.QPushButton('重新调用 set_markdown()')

    row = QtWidgets.QHBoxLayout()
    row.addWidget(check_callback)
    row.addWidget(check_allow_http)
    row.addStretch(1)
    row.addWidget(button_reload)
    layout.addLayout(row)

    layout.addWidget(QtWidgets.QLabel('链接点击记录:'))
    log = QtWidgets.QPlainTextEdit()
    log.setReadOnly(True)
    log.setMaximumHeight(130)
    layout.addWidget(log)

    def log_line(text):
        now = QtCore.QTime.currentTime().toString('HH:mm:ss')
        log.appendPlainText(f'[{now}] {text}')

    def on_link(url):
        """示例回调: 自定义协议自行处理, 锚点与可选的 http 链接交给默认动作."""
        if url.startswith('zmlx://'):
            log_line(f'回调已处理(返回 True): {url}')
            QtWidgets.QMessageBox.information(window, '自定义协议',
                                              f'链接由回调处理:\n{url}')
            return True
        if url.startswith('#'):
            log_line(f'回调未处理(返回 False), 由控件滚动到锚点: {url}')
            return False
        if url.startswith('http') and check_allow_http.isChecked():
            log_line(f'回调未处理(返回 False), 由系统浏览器打开: {url}')
            return False
        log_line(f'回调拦截(返回 True), 不做默认动作: {url}')
        return True

    def on_toggle_callback(checked):
        view.set_link_callback(on_link if checked else None)
        log_line('已调用 set_link_callback(on_link)' if checked
                 else '已调用 set_link_callback(None): 所有链接走默认动作')

    def on_reload():
        view.set_markdown(demo_md, base_url=icons)  # 图片靠 base_url 找到
        log_line('已重新调用 set_markdown(示例 Markdown, base_url=zml_icons)')

    check_callback.toggled.connect(on_toggle_callback)
    button_reload.clicked.connect(on_reload)

    # ---- 方法一: 设置 Markdown 字符串 ----  ---- 方法二: 设置回调 ----
    view.set_markdown(demo_md, base_url=icons)
    view.set_link_callback(on_link)
    log_line('已调用 set_markdown(示例 Markdown, base_url=zml_icons) 与 set_link_callback(on_link)')
    log_line('当前渲染方式: '
             f'{"markdown 库 -> setHtml" if view._use_html() else "Qt 自带 setMarkdown"}'
             f' ({view.SETTING_KEY}={view._md_by_html()})')
    log_line('提示: 点击正文里的链接, 这里会记录每次点击与回调的处理结果')
    if view._has_markdown():
        log_line('提示: 在正文里点右键, 可勾选「用 markdown 库渲染（md → HTML）」切换渲染方式')
    else:
        log_line('提示: 环境里没有 markdown 库, 因此右键菜单里没有渲染方式开关（默认用 Qt 渲染）')

    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    test_1()
