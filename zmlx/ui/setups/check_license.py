"""``gui.check_license`` —— 检查本机授权（**旧的** USB / 序列号授权），未授权时弹红字警告.

⚠️ **本文件 2026-10-31 新建**：原 `MainWindow.check_license` 的方法体**原样搬来**，
逻辑一字未改。

⚠️⚠️ **这是一个已弃用的方法，搬过来只是换个地方，语义一份不改**
-----------------------------------------------------------------

用户 2026-10-05 要求弃用：授权已迁移到 **web 授权**（``zmlx.exts.web_license``，见状态栏
右下角与「设置 → 系统」）。本方法读的 ``lic.valid`` 是**旧的**本机授权判据，对已用
web 授权注册的用户**会误报**。

⚠️ 它**至今没有任何调用方**（全仓 grep 只有定义处与注释）。保留的唯一理由是
「不破坏外部脚本里可能存在的调用」，所以：

1. **照旧发 ``DeprecationWarning``**（同一句文案，含 2027-10-05 的删除日期）；
2. **照旧不挂菜单、不自动触发**（原先的启动检查与「关于」页里的调用都已移除）；
3. 仍然注册成命令 ``gui.check_license`` —— 它原本靠「主窗口公开方法被自动注册」得来，
   搬走之后必须显式补上，否则外部调用会从「一条弃用警告」变成「找不到命令」，
   那是**更糟**的破坏。

⚠️ **为什么不删掉？** 没人调用 ≠ 没人依赖。外部脚本 / `igg-hydrate-works` 下的项目
可能仍在调；按仓库约定，**弃用要留到声明的删除日期（2027-10-05）**，届时再删。

为什么在 ``setups/`` 而不是别处
------------------------------

它是个**命令**（不是控件、不挂菜单），按 ``setups/AGENTS.md`` §1 的判据：
关掉它，``gui.check_license()`` 就报「找不到命令」—— 那是破坏性的。所以归 **必加载**的
``setups/``，与其它「命令型」装配并列（``open_url.py`` / ``text_in_tab.py``）。

⚠️ 由 ``setups/__init__.py`` 的 ``setup_ui()`` 统一调用（那里是**唯一**的登记点）。

行为契约（**搬迁前后完全一致**）
--------------------------------

1. 发 ``DeprecationWarning``（``stacklevel=2``，指向调用者）；
2. 清空 ``core`` 的日志队列；
3. ``lic.valid`` 为假时：先把日志打出来，再弹一句红字
   「此电脑未登录，请确保: 1、使用最新版；2、本机联网!」；
4. 全程 ``try/except``，任何异常只 ``print``，不向外抛。

⚠️ **第 3 步的「弹红字」走的是 ``gui.toolbar_warning(text)``**（不再是
``self.toolbar_warning``）：``toolbar_warning`` 是 ``MainWindow`` 上的 ``@staticmethod``，
本来就会被自动注册成同名命令，两者是同一个函数；它内部用 ``gui.add_message(text, color='red')``
（写「显示 → 通知」并落盘），拿不到界面时退回 ``print``。
"""

from zmlx.exts import core, lic
from zmlx.system import execute_once, warn
from zmlx.ui import gui


def check_license():
    """检查本机授权（旧的「USB / 序列号」授权），未授权时在工具栏弹一句红字警告。

    ⚠️ **已弃用**（用户 2026-10-05 要求）：授权已迁移到 web 授权
    （``zmlx.exts.web_license``，见状态栏右下角与「关于」页面），本方法读的
    ``lic.valid`` 是**旧的**本机授权判据，对已用 web 授权注册的用户会误报。
    因此它**不再有任何自动触发点**（原先的启动检查与 ``show_about`` 里的调用都已移除），
    保留只是为了不破坏既有调用方。

    ⚠️ 本方法还会取网络时间（``lic.valid`` → ``is_expired`` → ``os::webtime``），
    离线时可能被判过期 —— 这正是它被弃用的原因之一。

    ⚠️ 由 ``MainWindow.check_license`` **原样搬来**（2026-10-31）：那段代码靠「主窗口的
    公开方法被自动注册成 ``gui.xxx``」提供命令；方法搬走后那条链断了，所以本文件的
    :func:`setup_ui` 用 ``gui.add_func('check_license', check_license)`` **显式补上**。
    """
    warn(
        "MainWindow.check_license() is deprecated (will be removed after 2027-10-05), "
        "the license is now checked by the web license "
        "(see zmlx.exts.web_license and the status bar). This method will be removed.",
        DeprecationWarning,
        stacklevel=2,
    )
    try:
        while core.has_log():
            core.pop_log()
        if not lic.valid:
            while core.has_log():
                print(core.pop_log())
            print("\n\n")
            gui.toolbar_warning(
                "此电脑未登录，请确保: 1、使用最新版；2、本机联网!"
            )
    except Exception as err:
        print(f"Error: {err}")


@execute_once(file=__file__)
def setup_ui():
    """注册命令 ``gui.check_license``（由 ``setups/__init__.py`` 调用）.

    ⚠️ **本文件不挂菜单项、不加任何自动触发点**：它是已弃用的命令，只供外部脚本
    显式调用（调一次就收到一条弃用警告）。别「顺手」把它挂到启动流程或某个页面上 ——
    那正是 2026-10-05 被撤掉的东西。

    ⚠️ 报错文案里的 ``MainWindow.check_license()`` **保持原样**：它是这条弃用警告的
    历史原文，外部若有断言 / 日志匹配，改字会让人对不上。方法已经不在
    ``MainWindow`` 上了，但**警告文案不改**。
    """
    gui.add_func('check_license', check_license)
