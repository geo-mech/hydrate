# ** name = '图片浏览'
# ** desc = '扫描工作路径下的图片，左侧缩略图相册 + 右侧大图预览，支持连续播放'
"""「图片浏览」菜单动作（菜单「文件 → 图片浏览」）.

把 :class:`~zmlx.ui.tabs.image_browser.ImageBrowser` 挂到界面上：菜单项在
**「文件」**下，点击即打开（或切到）那个标签页。

为什么是插件（``plugins/``）而不是 ``extra_setups/``
--------------------------------------------------

``ImageBrowser`` 本身是**顶层控件**（只被装配层打开成标签页、不被任何控件复用），
按 [`../tabs/AGENTS.md`](../tabs/AGENTS.md) 的判据归 ``tabs/``。而「把它挂进菜单」
这一步：图片浏览是**工具型、非核心**的功能，不该出现在「必须提供」的菜单里 ——
所以做成插件，用户不需要时可以在「设置 → 插件」里关掉，菜单项随之消失。

⚠️ 2026-10-18 由 ``extra_setups/image_browser.py`` 移到这里（同理还有
``vtk_view.py`` / ``zip_files.py``）。两者的分工见 :mod:`zmlx.ui.plugins`：
**产品功能**（授权查询、用户管理）留 ``extra_setups``，**可关闭的扩展**放这里。

挂出来的两个入口
----------------

========================  ============================================
入口                       调用
========================  ============================================
菜单「文件 → 图片浏览」      :func:`show_image_browser`
GUI 命令                  ``gui.show_image_browser()``
========================  ============================================

⚠️ **``gui.show_image_browser()`` 是给 ``gui_restore`` 用的**：标签页被存进标签
状态后，重启时按这串原文重放，所以命令名一旦发布就**不能再改**（照
[`license_query.py`](license_query.py) 末尾那两条旧名别名的既定纪律）。

⚠️ 命令名**必须与 ``MainWindow`` 已有的方法名不撞车**：``__init_gui_api`` 会把主窗口
的所有公开方法自动注册进命令表，撞名就会把那个方法悄悄顶掉。``show_image_browser``
在 ``main.py`` 里不存在（这正是「不动 ``main.py``」的实现方式），所以安全。

只切页、不重扫
--------------

``get_widget`` 在窗口里**按「类型 + 标题」复用**已有的标签页：反复点菜单只会把
「图片浏览」那一页切到前面，**不会越开越多**。

⚠️ 因此 ``oper`` 里**只**记 ``gui_restore``，不调刷新 —— ``get_widget`` 每次调用都会
跑到 ``oper``（点菜单也不例外），在里面刷新就等于「点一次菜单重扫一次目录」。
本控件也不实现 ``refresh()``（切标签页**不**自动重扫，刷新只由页面上的「刷新」按钮
触发），两处口径一致：**重建视图只发生在真的新建标签页时**。

Created by DeepSeek, 2026-10-16
"""

from zmlx.system import execute_once


def show_image_browser():
    """打开（或切到）「图片浏览」标签页；同时也是 GUI 命令 ``gui.show_image_browser()``.

    目录由 :class:`~zmlx.ui.tabs.image_browser.ImageBrowser` 自己决定：**默认跟随工作路径**
    （每次刷新都现取 ``os.getcwd()``），所以用户改了工作路径再点刷新，看到的就是新目录。

    ⚠️ 这里走 ``gui.command`` 而不是直接开标签页：菜单项是从 GUI 线程调的，但
    ``gui.show_image_browser()`` 也可能被**脚本 / 后台线程**调用 —— 走命令表才能保证
    「无论谁调，开标签页这件事都发生在 GUI 线程里」。

    ⚠️ 标签页按「类型 + 标题」复用：重复点菜单只会切到那一页。也正因为复用，
    **不能**在 ``type_kw`` 里传 ``folder``（那会把目录固定在第一次打开时的值上）。
    """
    from zmlx.ui import gui

    gui.command('show_image_browser')


def _open():
    """真正打开标签页（注册成命令 ``show_image_browser``，故只在 GUI 线程里执行）."""
    from zmlx.ui import gui
    from zmlx.ui.tabs.image_browser import ImageBrowser

    def _oper(w):
        # ⚠️ 只做「记住怎么重放我」这一件事，不要在这里刷新（见模块文档）。
        w.gui_restore = 'gui.show_image_browser()'

    gui.get_widget(
        the_type=ImageBrowser,
        caption='图片浏览',
        on_top=True,
        oper=_oper,
        tooltip='浏览工作路径下的图片：左侧缩略图相册，点选后在右侧查看大图，'
                '支持上一张/下一张、按帧率连续播放与循环',
        # ⚠️ **刻意不传 folder**：不传 = 控件跟随工作路径，每次刷新都现取
        #    ``os.getcwd()``。传了 ``folder=os.getcwd()`` 反而会把它**固定**在
        #    打开菜单那一刻的目录上 —— 之后用户改了工作路径、再点刷新，
        #    看到的还是老目录（这正是要避免的行为）。
        #    标签页被复用（get_widget 按「类型+标题」）时也不会残留旧目录。
    )


@execute_once(file=__file__)
def setup_ui():
    """注册 GUI 命令与菜单项（由 ``plugins.run_setup`` 执行本文件时触发）."""
    from zmlx.ui import gui

    # 先注册命令：gui.show_image_browser() 与菜单项指向**同一个**函数，
    # 保证「菜单」与「命令」不会各写一套。
    gui.add_func('show_image_browser', _open)

    gui.add_action(
        menu='文件',
        name='image_browser',
        text='图片浏览',
        slot=show_image_browser,
        overwritable=False,
    )


# ⚠️ 作为**插件**被 ``run_setup`` 执行时，没人会替我们调 ``setup_ui()``：
#    插件文件必须在**顶层自己调**（``extra_setups/*.py`` 则由
#    ``extra_setups/__init__.py`` 统一调用 —— 这是两者唯一的区别）。
setup_ui()
