"""README.md 控件（左侧标题目录 + 右侧正文）.

本文件提供两个类:

- :class:`_ReadMeContent`（私有）: ReadMe 的**正文**. 继承
  :class:`~zmlx.ui.widget.md_view.MarkdownView` —— ReadMe 本质就是一个 Markdown 文档, 交给
  MarkdownView 渲染即可, 于是自动获得「装了 ``markdown`` 库就转 HTML 渲染、否则回退 Qt 自带
  ``setMarkdown``」的行为、右键菜单里的渲染方式开关, 以及文档内 ``#锚点`` 原地跳转.
- :class:`ReadMeBrowser`（对外）: 本控件, 一个 ``QWidget`` 容器 —— 内部用 ``QSplitter`` 并排
  摆放**左侧标题目录**（``QTreeWidget``）和**右侧正文**（``_ReadMeContent``）, 效果类似
  GitHub / gitee 在线仓库的侧边目录: 点目录项跳到对应小节, 滚动正文时目录高亮当前小节.

⚠️ 对外的类型名（``ReadMeBrowser``）与构造签名（``ReadMeBrowser(parent=None)``）**保持不变**,
因此 ``MainWindow.show_readme()`` 等处无需任何改动.

目录数据取自**已渲染的文档**（``_ReadMeContent.get_headings()``, 读 ``QTextDocument`` 里的
heading 块）, 而不是重新解析 markdown 源码 —— 这样目录与正文必然一致, 且两条渲染路径都通用.
点击跳转复用 MarkdownView 现成的 ``_scroll_to_anchor``.

正文里点击链接的处理见 :meth:`_ReadMeContent._on_link`: 除了交给
:func:`zmlx.ui.alg.open_url`, ReadMe 里那几个"能在本地做"的链接会被就地处理 ——
微信/联系作者 → 显示本地二维码图片; 帮助 → 用户 → 登录 → 打开登录控件; ``zmlx/demo`` → 打开 GUI
自带的 Demo 浏览器; ``zmlx/demos/ReadMe.md`` → 用 MarkdownView 打开本地文件;
新建Issue → 打开 GUI 自带的反馈工具。

另有一类**gui 链接** ``zmlx://gui/<gui 函数名>``: 点它等于点了对应的那个菜单项（见
:meth:`_ReadMeContent._trigger_gui`）。正文里写「设置 → 系统」这类**说明文字**的地方
有好几处, 我们不去猜哪些该变成入口 —— 只有正文自己写成 ``zmlx://gui/...`` 的才挂上动作
（目前是「隐私声明」一节的 ``show_env_edit`` 与 ``show_feedbacks_view``）。加新链接时写
**gui 函数名**（即 ``gui.xxx()`` 里的 ``xxx``, 也是 ``gui.add_func`` 注册的那个名字）。

Modified by DeepSeek, 2026-09-14
Modified by DeepSeek, 2026-10-06: 改为继承 MarkdownView（原先直接继承 TextBrowser 并自行 setMarkdown）
Modified by DeepSeek, 2026-10-06: 给 ReadMe 里的几个链接加上本地处理（微信二维码 / 登录 / Demo 浏览器等）
Modified by DeepSeek, 2026-10-07: 拆为 _ReadMeContent(正文) + ReadMeBrowser(左目录容器)，逻辑仍只在本文件内
Modified by DeepSeek, 2026-10-10: 支持 ``zmlx://gui/<gui 函数名>``（正文里点一下就打开对应页面）
"""

import os

from zmlx.system import app_data, log
from zmlx.ui.alg import create_action, open_url
from zmlx.ui.gui_buffer import gui
from zmlx.ui.pyqt import QtCore, QtWidgets
from zmlx.ui.widgets.md_view import MarkdownView


class _ReadMeContent(MarkdownView):
    """ReadMe 正文（原 ReadMeBrowser 的实现, 逻辑未变）.

    只负责把 markdown 渲染出来、并处理链接点击; 「左侧目录」由本文件末尾的
    :class:`ReadMeBrowser` 容器提供.
    """

    # 每次载入完 ReadMe 之后发出, 供容器按新正文重建左侧目录
    markdown_loaded = QtCore.pyqtSignal()

    # 正文里「点一下等于点了某个菜单」的链接协议: ``zmlx://gui/<gui 函数名>``
    GUI_SCHEME = 'zmlx://gui/'

    def __init__(self, parent=None):
        self._base_dir = None  # md 文件所在目录, 用来解析文档里的相对链接
        self._anchors = {}     # {链接文字: href}, 用来认出下面那些"特殊链接"
        super(_ReadMeContent, self).__init__(parent)
        self._load()
        self.context_actions.append(create_action(self, "重新载入ReadMe", slot=self._load))
        self.context_actions.append(create_action(self, "关于", slot=gui.show_about))
        self.context_actions.append(create_action(self, "登录", slot=gui.show_reg_tool))

    # ------------------------------------------------------------------
    # 加载
    # ------------------------------------------------------------------
    def _load(self):
        # README 只存在于包内 zmlx/data/ 目录（仓库根目录的副本已删除），直接读它即可：
        # pip 安装环境与开发环境读到的是同一个文件，不再需要任何同步步骤。
        from zmlx.data import get_path as data_path
        from zmlx.data import read_doc

        path = data_path('README.md')
        text = read_doc('README.md')
        if text is not None:
            self._base_dir = os.path.dirname(path)
            # 基准目录 = md 文件所在目录, 让文档里的相对链接/图片能解析
            self.set_markdown(text, base_url=self._base_dir)
            self._anchors = self._collect_anchors()
            # 明确指定"点击链接之后做什么"(见 _on_link)
            self.set_link_callback(self._on_link)
            self.set_status(path)
            self.markdown_loaded.emit()
        else:
            self.setText("未找到ReadMe文件, 并已经尝试打开代码库的主页")
            open_url(
                url='https://gitee.com/geomech/hydrate',
                on_top=True,
                caption='IGG-Hydrate',
                icon='home'
            )

    def get_headings(self):
        """返回正文里的标题列表 ``[(level, text, anchor)]``（按文档顺序）.

        从**已渲染的文档**里读（而不是重新解析 markdown 源码）, 因此与当前显示的内容必然
        一致, 且不依赖渲染方式 —— Qt 自带 ``setMarkdown`` 与 markdown 库 ``setHtml`` 两条
        路径都通用. ``anchor`` 复用 :meth:`_slugify`, 与 :meth:`_scroll_to_anchor` 的匹配
        规则同源, 保证按它一定跳得过去.

        Returns:
            list[tuple[int, str, str]]: 每项为 (标题层级, 标题文本, 锚点名).
        """
        result = []
        block = self.document().begin()
        while block.isValid():
            level = block.blockFormat().headingLevel()
            if level > 0:
                text = block.text().strip()
                anchor = self._slugify(text)
                if len(anchor) > 0:
                    result.append((level, text, anchor))
            block = block.next()
        return result

    def _collect_anchors(self):
        """把文档里的链接收集成 ``{链接文字: href}``.

        有了它, 那些要在本地特殊处理的链接就能**按文字**认出来: README 里换了网址（例如 issues
        的 ID 变了）也不会让这些处理失效.
        """
        result = {}
        block = self.document().begin()
        while block.isValid():
            it = block.begin()
            while not it.atEnd():
                frag = it.fragment()
                if frag.isValid() and len(frag.text().strip()) > 0:
                    fmt = frag.charFormat()
                    if fmt.isAnchor() and len(fmt.anchorHref()) > 0:
                        result.setdefault(frag.text().strip(), fmt.anchorHref())
                it += 1
            block = block.next()
        return result

    @staticmethod
    def _href_of(anchors, *texts):
        """按链接文字找 href: 先精确匹配, 再按传入顺序做包含匹配; 找不到返回 ``None``."""
        for text in texts:
            if text in anchors:
                return anchors[text]
        for text in texts:
            for key, href in anchors.items():
                if text in key:
                    return href
        return None

    # ------------------------------------------------------------------
    # 点击链接
    # ------------------------------------------------------------------
    def _on_link(self, url):
        """处理 ReadMe 里的超链接点击.

        Args:
            url: 链接目标地址（控件直接给出 ``href`` 原文）。

        Returns:
            bool: ``True`` 表示已自行处理（控件不再做别的）; ``False`` 表示交给控件的默认动作。

        通用的几条:

        - 空链接（如 ``[文字]()``）: 直接忽略（否则会被解析成基准目录并打开）;
        - 文档内 ``#锚点``: 返回 ``False``, 让控件原地滚动到对应标题;
        - 菜单协议 ``zmlx://gui/<gui 函数名>``: 见 :meth:`_trigger_gui`, 直接调用那个
          gui 函数 —— 它正是对应菜单项的 ``slot``（例如 ``zmlx://gui/show_env_edit``
          = 「设置 → 系统」）;
        - 相对路径（如 ``docs/xxx.md``）: 先按 md 文件所在目录解析成绝对路径, 存在就改用绝对路径
          —— 否则 ``open_url`` 拿到的是一个相对的"网址", 浏览器打不开;
        - 其余（``http(s)`` / ``mailto:`` / 自定义协议）: 交给 :func:`zmlx.ui.alg.open_url`
          —— 有 GUI 时开标签页, 否则交给系统浏览器。

        ReadMe 里这几个链接**能在本地做就不去开浏览器**（按链接文字识别, 网址变了也生效）:

        ========================  ==========================================================
        链接文字                   点击之后
        ========================  ==========================================================
        微信 / 联系作者             用 ``gui.open_image`` 显示 ``zml_icons/zzb_wechat.png``
        登录页面                    打开登录控件（``gui.show_reg_tool``）
        ``zmlx/demo``             打开 GUI 自带的 Demo 浏览器（``gui.show_demo``）
        ``zmlx/demos/ReadMe.md``   用 MarkdownView 打开本地的 ``zmlx/demos/ReadMe.md``
        新建Issue                  打开 GUI 自带的反馈工具（``gui.show_feedback``）
        ========================  ==========================================================

        ⚠️ **登录只认「登录页面」这一个链接文字**：README 的对应小节里, 正文多次提到
        「帮助 → 用户 → 登录」「未登录」等字样, 它们只是**说明文字**, 不该都变成
        入口 —— 否则把本机与邮箱关联那一段几乎每个词都能点开登录控件, 反而看不出该点哪一个。

        ⚠️ 而 ``zmlx://gui/...`` 恰恰相反: 它必须**由正文自己写出来**才会生效 —— 正文里那些
        「设置 → 系统」「帮助 → 查询 → 反馈记录」之类纯粹是**说明文字**（登录一节里
        就有好几处）, 我们不去猜哪一个该变成入口, 只有写成 ``zmlx://gui/...`` 的才挂上动作。

        本地处理失败时（例如没有 GUI、或本地文件不存在）会自动退回成"用 ``open_url`` 打开原网址"。
        """
        if len(url) == 0:
            return True
        if url.startswith('#'):
            return False
        if url.startswith(self.GUI_SCHEME):
            return self._trigger_gui(url)
        for texts, action in (
                (('微信', '联系作者'), self._show_wechat),
                (('登录页面', '注册页面'), self._show_reg_tool),
                (('zmlx/demos/ReadMe.md',), self._show_demo_readme),
                (('zmlx/demo', 'demo'), self._show_demo),
                (('新建Issue',), self._show_feedback),
        ):
            href = self._href_of(self._anchors, *texts)
            if href is not None and href == url:
                try:
                    action()
                    return True
                except Exception as err:
                    print(f'Warning: 本地处理 <{url}> 失败, 改为打开网页: {err}')
                    break
        target = url
        if '://' not in url and not url.startswith('mailto:') and self._base_dir is not None:
            path = os.path.normpath(os.path.join(self._base_dir, url))
            if os.path.exists(path):
                target = path
        open_url(url=target)
        return True

    # ------------------------------------------------------------------
    # 正文里的「菜单链接」: zmlx://gui/<gui 函数名>
    # ------------------------------------------------------------------
    @classmethod
    def _gui_func(cls, url):
        """``zmlx://gui/show_env_edit`` -> 注册在 gui 里的那个函数（认不出返回 ``None``）.

        链接里写的是 :attr:`GuiApi.funcs` 里的**函数名**（也就是 ``gui.xxx()`` 里的
        ``xxx``）—— 「设置 → 系统」是 ``show_env_edit``、「帮助 → 查询 → 反馈记录」
        是 ``show_feedbacks_view``（见 ``extra_setups/license_query.py`` 的
        ``gui.add_func``）。菜单项的 ``slot`` 就是它们, 所以点链接与点菜单**走同一个函数**。

        ⚠️ 为什么不写 ``zmlx://menu/<动作名>`` 再去 ``MainWindow.trigger``: 那样要多绕一层
        「按 ``objectName`` 反查 QAction」, 而 ``trigger`` 认不出时会打印一句 warning、
        再触发一个临时建出来的空 action（什么也不做）—— 名字对不对, 从它那里看不出来。
        直接取 gui 函数没有这个中间层: 名字不在表里就是 ``None``, 判得出来也说得清。

        ⚠️ 路径段按 ``/`` 切分时**不做 URL 解码**: Qt 给回调的就是 href 原文, 而 ``QUrl``
        会把非 ASCII 的 ``path()`` 编成百分号形式。
        """
        if not url.startswith(cls.GUI_SCHEME):
            return None
        parts = [p for p in url[len(cls.GUI_SCHEME):].split('/') if len(p) > 0]
        if len(parts) == 0:
            return None
        if not gui.exists():  # 无 GUI: 函数表是空的
            return None
        func = gui.get().get_func(parts[-1])
        return func if callable(func) else None

    def _trigger_gui(self, url):
        """调用 ``zmlx://gui/...`` 指向的 gui 函数（等价于点了对应的那个菜单项）.

        Returns:
            bool: 一定要返回 ``True`` —— 认不出的链接也**不能**退回 ``open_url``:
            否则会拿这个自定义协议去烦系统（要么弹"找不到应用", 要么真去开一个网页）。
        """
        func = self._gui_func(url)
        name = url[len(self.GUI_SCHEME):].split('/')[-1]
        if func is None:
            print(f'Warning: ReadMe 里的链接 <{url}> 找不到对应的 gui 函数, 已忽略')
            return True
        try:
            func()
        except Exception as err:
            print(f'Warning: 执行 gui.{name}() 失败: {err}')
            return True
        log(f'run <{name}>',  # 与在菜单里点它的日志一致
            tag=f'run <{name}>')
        self._restore_after_gui()
        return True

    def _restore_after_gui(self):
        """执行完 gui 函数后把焦点还给 ReadMe 正文.

        ⚠️ **千万不要在这里 ``gui.show_readme()``**: 这两个函数都是"打开某个标签页"
        （``show_env_edit`` / ``show_feedbacks_view``）, 再调一次会把 ReadMe 顶到前面,
        用户根本看不到刚打开的那一页。
        """
        try:
            self.setFocus()
        except Exception:
            pass  # 控件正被销毁时忽略即可

    # ------------------------------------------------------------------
    # 几个特殊链接的本地实现
    # ------------------------------------------------------------------
    @staticmethod
    def _show_wechat():
        """显示作者的微信二维码：本地图片, 用 ImageView 开一个新标签页（``gui.open_image``）."""
        from zmlx.ui.settings import find_icon_file
        path = find_icon_file('zzb_wechat')
        if path is None:
            raise FileNotFoundError('未找到 zzb_wechat 图片')
        gui.open_image(path, caption='微信')

    @staticmethod
    def _show_demo():
        """打开 GUI 自带的 Demo 浏览器（等价于菜单/工具栏里的 Demo 入口）."""
        gui.show_demo()

    @staticmethod
    def _show_feedback():
        """"新建 Issue" 在本地对应的入口: GUI 自带的反馈工具."""
        gui.show_feedback()

    @staticmethod
    def _show_reg_tool():
        """"菜单：帮助 → 用户 → 登录"在本地对应的入口: 直接打开登录控件."""
        gui.show_reg_tool()

    @staticmethod
    def _show_demo_readme():
        """用 MarkdownView 打开本地的 ``zmlx/demos/ReadMe.md``（而不是去开 gitee 网页）.

        ⚠️ 目录名用**新名** ``demos``：``demos/`` 由 ``demo/`` 改名为复数，
        ``get_path('demo', ...)`` 会拼出已不存在的 ``zmlx/demo/ReadMe.md``，
        于是本地处理失败、退回 ``open_url`` 去开网页。
        """
        from zmlx import get_path
        from zmlx.system import read_text
        path = get_path('demos', 'ReadMe.md')
        text = read_text(path, encoding='utf-8') if os.path.isfile(path) else None
        if text is None:
            raise FileNotFoundError(f'未找到本地的 {path}')

        def oper(w):
            w.set_markdown(text, base_url=os.path.dirname(path))
            w.set_status(path)

        gui.get_widget(the_type=MarkdownView, caption='Demo ReadMe',
                       on_top=True, icon='info', oper=oper)


class ReadMeBrowser(QtWidgets.QWidget):
    """ReadMe 控件: 左侧标题目录 + 右侧正文.

    对外的类型名与构造签名都和改造前一致（``ReadMeBrowser(parent=None)``）, 因此
    ``MainWindow.show_readme()`` 等处无需任何改动.

    Attributes:
        content: 右侧正文, :class:`_ReadMeContent` 实例（保留原控件的全部能力:
            渲染方式开关 / 链接就地处理 / 状态栏提示等）.
        toc: 左侧目录树（``QTreeWidget``）; 每项用 ``UserRole`` 存对应标题的锚点.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.content = _ReadMeContent()  # 构造时就已经完成了一次载入
        self.toc = self._create_toc()
        self._syncing = False  # 防止「点击目录 -> 滚动正文 -> 回写高亮」来回打环

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.toc)
        splitter.addWidget(self.content)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([220, 780])

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        # 正文「重新载入ReadMe」之后目录要跟着重建, 否则目录会与正文脱节
        self.content.markdown_loaded.connect(self.reload_toc)
        self.toc.itemClicked.connect(self._on_toc_clicked)
        self.content.verticalScrollBar().valueChanged.connect(self._sync_toc)
        self.reload_toc()  # 构造时那次载入发生在 connect 之前, 这里补建一次

    # ------------------------------------------------------------------
    # 目录
    # ------------------------------------------------------------------
    def reload_toc(self):
        """按当前正文重建左侧目录.

        标题层级做**归一化**（减去文档里的最小层级）: README 里只有 ``###`` / ``####``,
        若按绝对层级缩进, 整列会平白缩到第三级; 归一化后 ``###`` 顶格、``####`` 缩进一级
        —— GitHub 的侧边目录也是这么处理的.
        """
        tree = self.toc
        tree.clear()
        headings = self.content.get_headings()
        if len(headings) == 0:
            return
        base = min(level for level, _, _ in headings)
        stack = []  # [(深度, item)], 用来把标题挂成层级树
        for level, text, anchor in headings:
            item = QtWidgets.QTreeWidgetItem([text])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, anchor)
            item.setToolTip(0, text)
            depth = level - base
            while len(stack) > 0 and stack[-1][0] >= depth:
                stack.pop()
            if len(stack) == 0:
                tree.addTopLevelItem(item)
            else:
                stack[-1][1].addChild(item)
            stack.append((depth, item))
        tree.expandAll()
        self._sync_toc()

    @staticmethod
    def _create_toc():
        """创建左侧目录树（单列、无表头）."""
        tree = QtWidgets.QTreeWidget()
        tree.setHeaderHidden(True)
        tree.setColumnCount(1)
        tree.setIndentation(14)
        tree.setUniformRowHeights(True)
        tree.setMinimumWidth(120)
        return tree

    def _on_toc_clicked(self, item, column):
        """点击目录项: 滚动正文到对应标题.

        复用 MarkdownView 现成的 ``_scroll_to_anchor`` —— 它在两种渲染路径下都能定位
        （先走 Qt 的 ``scrollToAnchor``, 找不到再按标题文本匹配）, 不必另写一套.
        """
        anchor = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not anchor:
            return
        self._syncing = True
        try:
            self.content._scroll_to_anchor(anchor)
            self._align_to_top(anchor)
        finally:
            self._syncing = False
        self._sync_toc()         # 点击后立刻把高亮修正到这一小节
        self.content.setFocus()  # 焦点还给正文, 方便紧接着用滚轮

    def _align_to_top(self, anchor):
        """把锚点所在标题精确对齐到视口顶部.

        ``_scroll_to_anchor`` 走的是 Qt 的 ``scrollToAnchor``, 只保证标题"可见"（可能
        停在视口**底部**）; 目录跳转期望它停在**顶部** —— GitHub 的侧边目录就是这个行为,
        顺带也让高亮落回正确的小节.
        """
        block = self._find_heading_block(anchor)
        if block is None or not block.isValid():
            return
        rect = self.content.document().documentLayout().blockBoundingRect(block)
        self.content.verticalScrollBar().setValue(int(rect.top()))

    def _find_heading_block(self, anchor):
        """按锚点找到对应的标题块（找不到返回 ``None``）."""
        block = self.content.document().begin()
        while block.isValid():
            if block.blockFormat().headingLevel() > 0:
                if self.content._slugify(block.text().strip()) == anchor:
                    return block
            block = block.next()
        return None

    def _sync_toc(self):
        """正文滚动时, 把目录高亮同步到当前所在的小节."""
        if self._syncing:
            return
        anchor = self._current_anchor()
        if anchor is None:
            return
        item = self._find_toc_item(anchor)
        if item is None or item is self.toc.currentItem():
            return
        self._syncing = True
        try:
            self.toc.setCurrentItem(item)
            self.toc.scrollToItem(item)
        finally:
            self._syncing = False

    def _current_anchor(self):
        """视口顶部所在小节对应的锚点（还没到第一个标题时返回 ``None``）."""
        cursor = self.content.cursorForPosition(QtCore.QPoint(0, 0))
        block = cursor.block()
        while block.isValid():
            if block.blockFormat().headingLevel() > 0:
                anchor = self.content._slugify(block.text().strip())
                return anchor if len(anchor) > 0 else None
            block = block.previous()
        return None

    def _find_toc_item(self, anchor):
        """按锚点在目录树里查对应项（深度优先; 找不到返回 ``None``）."""
        stack = [self.toc.topLevelItem(i) for i in range(self.toc.topLevelItemCount())]
        while len(stack) > 0:
            item = stack.pop()
            if item.data(0, QtCore.Qt.ItemDataRole.UserRole) == anchor:
                return item
            stack.extend(item.child(i) for i in range(item.childCount()))
        return None


# ============================================================
# 测试
# ============================================================

def test_1():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = ReadMeBrowser()
    w.setWindowTitle('ReadMeBrowser 演示（左目录 + 右正文）')
    w.resize(900, 620)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test_1()
