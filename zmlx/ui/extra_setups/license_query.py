"""「帮助 → 查询」下的两个在线查询页面（登录记录 / 反馈记录）.

⚠️ 2026-10-19：菜单由 ``用户 → 查询 → {登录记录, 反馈记录}`` 改为
``帮助 → 查询 → {登录记录, 反馈记录}`` —— 「用户」整个并回了「帮助」，所以
「查询」这一层**跟着上提一层**。★ 最终结构是**两级**：两条记录页位于
帮助 → 查询 → X，与「帮助 → 用户 → 登录」同深，**没有任何三级菜单**。
命令名与 action name **一律不动**。

为什么在这里而不是 ``main.py``
------------------------------

这两个页面各**只是一个菜单条目**：控件本体在 ``zmlx/ui/tabs/``（``CheckCountView``
与 ``FeedbacksView``），除了这个菜单项与 ``gui.show_xxx()`` 之外，``MainWindow``
里的任何东西都不需要它们。所以按 ``extra_setups`` 的既有约定把「注册菜单 + 打开
页面」收在这里，``MainWindow`` 只保留它自己真正要用的东西。

★ **控件本体一律留在 ``zmlx/ui/tabs/``**，这里只做界面接线。

GPU 线程与 ``gui_restore``
--------------------------

⚠️ **``gui.show_check_count_view`` / ``gui.show_feedbacks_view`` 这两个名字必须
逐字保留**：它们既是控制台里用户会敲的命令，也是标签页的 ``gui_restore``（重启后
按这段代码恢复标签页，见 ``main.py`` 的 ``__save_tabs``）。所以本模块用
``gui.add_func`` **自己把这两个名字注册进 GUI 命令表**。

⚠️ **只改显示文字，命令名与控件类名一律不动**：菜单项 / 标签页标题由「查询统计」
「查询反馈」改为 **「授权记录」「反馈记录」**，``show_check_count_view`` /
``CheckCountView`` / ``show_feedbacks_view`` / ``FeedbacksView`` 这些标识符保持
原样 —— 它们是 ``gui_restore`` 里存着的历史状态、也是控制台命令。

⚠️ 改这套名字时（``show_license_count`` → ``show_check_count_view``、
``show_license_feedback`` → ``show_feedbacks_view``）**必须同时注册旧名**
（见 ``setup_ui``）：老标签页的 ``gui_restore`` 里存的是旧名，只改名会让它恢复不了。

★ **命名规则只有一条：命令名 = ``show_`` + 控件类名的小写化。**
**一个字都不许改词形**（别写成 ``..._viewer``、别截掉 ``_view``）。两个控件名本身
则统一为「接口名去掉动词 + ``View``」。

⚠️ ``gui.add_func`` / ``gui.add_action`` 会被 GuiApi 派发到**主线程**执行。

⚠️ **``oper`` 每次调用都会执行**（见 ``TabWidget.get_widget``），所以里面只放
``gui_restore``；自动查询挂在控件自己的 ``showEvent`` 上。

Created by DeepSeek, 2026-10-08
"""

from zmlx.system import execute_once
from zmlx.ui.gui_buffer import gui


def show_check_count_view():
    """显示「授权记录」控件（某个邮箱对应用的许可查询次数，按天柱状图）。

    数据来自 ``web_license.check_count``。
    查询本身在后台线程里跑（最长 30 秒），且**不做缓存** —— 每次都是真的发出去，
    见 ``zmlx.ui.tabs.check_count_view`` 的模块文档。

    ⚠️ 只通过 ``gui.get_widget`` 打开（而不是直接 ``CheckCountView()``）：这样标签页
    只会有**一个**，重复调用只是把已有页面切到前面。

    名字的由来: 原先叫 ``show_license_count``、控件叫 ``LicenseCount``（由
    ``MainWindow`` 的公开方法自动注册而来）。那个名字说的其实是**数据来源**
    （``check_count`` 这个接口），而不是"这个控件是什么"；而 ``check_count`` 查的也
    不是"授权检查"，是**被数出来的那些 check 的次数**。故与控件一起改为
    ``CheckCountView``（与 ``FeedbacksView`` 配成一对：接口名去掉动词 + ``View``）。
    """
    from zmlx.ui.tabs import CheckCountView

    def oper(w):
        w.gui_restore = 'gui.show_check_count_view()'

    gui.get_widget(
        CheckCountView,
        caption='登录记录',
        on_top=True,
        icon='info',
        oper=oper,
        tooltip='某个邮箱对应用的许可查询次数，按天统计（原生 Qt 柱状图）',
    )


def show_feedbacks_view():
    """显示「反馈记录」控件（某个用户某一天的反馈文件名 + 单条内容）。

    数据来自 ``web_license.list_feedbacks`` / ``web_license.get_feedback``
    （**本人或管理员**可用）。两个查询都在后台线程里跑
    （各最长 30 秒），且**不做缓存** —— 每次都是真的发出去，见
    ``zmlx.ui.tabs.feedbacks_view`` 的模块文档。

    ⚠️ 与 :meth:`show_check_count_view` 逐字同构（两个页面的权限模型与线程纪律完全
    相同）；差别只在显示：那边画柱状图，这边显示**文本**。

    名字的由来: 原先叫 ``show_license_feedback``（由 ``MainWindow`` 的公开方法自动
    注册而来），但它干的只是**看反馈**这一件事, 与 ``license_`` 前缀暗示的"授权查询"
    无关 —— ``web_license.get_feedback`` 只是碰巧挂在 license 服务上。既然这是本轮
    新加的登记（见模块文档），就一并改成语义清楚的名字。
    """
    from zmlx.ui.tabs import FeedbacksView

    def oper(w):
        w.gui_restore = 'gui.show_feedbacks_view()'

    gui.get_widget(
        FeedbacksView,
        caption='反馈记录',
        on_top=True,
        icon='info',
        oper=oper,
        tooltip='某个用户某一天的反馈：列出文件名并查看内容（本人或管理员）',
    )


@execute_once(file=__file__)
def setup_ui():
    """注册 GUI 函数与菜单项（在 ``extra_setups.setup_ui`` 里被调用）.

    ⚠️ ``gui.add_func`` 补的是原先由 ``MainWindow.__init_gui_api`` 自动注册的
    两个名字（方法搬到本模块之后那条链就断了），见模块文档。
    """
    gui.add_func('show_check_count_view', show_check_count_view)
    gui.add_func('show_feedbacks_view', show_feedbacks_view)
    # ★ **两个旧名都保留为别名**：改名前打开过的标签页把
    #   ``gui_restore = 'gui.show_license_count()'`` / ``'gui.show_license_feedback()'``
    #   存进了标签状态（见 main.py 的 ``__save_tabs``），重启时按原文重放 —— 少了别名，
    #   那些标签页就再也打不开（``gui function <show_license_count> not found``）。
    #   一份别名换老状态能恢复，值得。新代码请用新名（见模块文档「名字的由来」）。
    #   ⚠️ 别名同时也留在控制台命令表里，用户敲惯的旧命令不会失效。
    gui.add_func('show_license_count', show_check_count_view)
    gui.add_func('show_license_feedback', show_feedbacks_view)

    # ★ 两个查询项都带 ``is_enabled=not_running``：查询要联网，正在跑仿真时点它
    #   只会排队等，不如直接置灰。
    #   ⚠️ 判据写成 ``not gui.is_running()``（``main.py`` 与其它菜单也这么做）：主窗口的
    #   ``not_running`` 是 ``__init_actions`` 里的闭包，本模块拿不到；而
    #   ``gui.is_running()`` 正是它内部调的那一个，语义完全一致。
    #   ⚠️ ``add_action`` 的 ``is_enabled`` 会**动态地**调用（见 ``Action.is_enabled``），
    #   所以这里传函数即可，不必在注册时求值。
    def not_running():
        return not gui.is_running()

    # ⚠️ 菜单标题与 ``main.py`` 里那两行 ``get_menu`` **逐字一致**
    #   （``['帮助', '查询']``），否则 ``get_menu`` 会另建一个同名子菜单，
    #   界面上出现两个「查询」。
    #   ``menu`` 用 list 形式时，``get_menu`` 会**按层级逐个查找、缺哪层就建哪层**，
    #   所以即使 ``main.py`` 没有先建出「查询」，这里也会自己建 —— 但那样它会
    #   排在「帮助」的**末尾**（见 ``main.py`` 的说明），所以仍在那边先建。
    #   ⚠️ 本模块在 ``MainWindow`` **构造之后**（由控制台内核调用）才执行，
    #   所以这里只负责**往已有的「查询」子菜单里填条目**，不影响它的位置。
    # ⚠️ ``name`` 是 ``get_action`` / ``list_actions`` / ``refresh_action`` 的键（也是
    #   ``Action.objectName()``）。全仓核对过：**没有任何地方按字符串取这两项**
    #   （``get_action`` 的调用者只有 ``main.py`` 里按局部变量名查的那几处），所以两个键
    #   与各自的函数名、控件名一起改了（``license_count`` → ``check_count_view``、
    #   ``license_feedback`` → ``feedbacks_view``）—— 让三处名字彼此对得上。
    #   ⚠️ 唯一的用途是 ``gui.refresh_action(name)``；将来若要单独刷新，请用新键。
    #   （注意 ``name`` 与 gui 函数名**不是一回事**：前者是菜单项的键，后者是命令名。）
    gui.add_action(
        menu=['帮助', '查询'],
        name='check_count_view',
        text='登录记录',
        icon='info',
        tooltip='查看某个邮箱对应用的许可查询次数（按天统计）',
        slot=show_check_count_view,
        is_enabled=not_running,
        overwritable=False,
    )

    gui.add_action(
        menu=['帮助', '查询'],
        name='feedbacks_view',
        text='反馈记录',
        icon='info',
        tooltip='查看某个用户某一天的反馈内容（本人或管理员）',
        slot=show_feedbacks_view,
        is_enabled=not_running,
        overwritable=False,
    )
