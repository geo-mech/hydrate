# ** name = '地热'
# ** desc = '地热算例集：井截面取热（参数界面 + 高渗 / 近不可渗两个工况）挂到一级菜单「地热」'
# ** enabled = False
"""地热场景的**插件入口**（菜单栏一级菜单「地热」）.

挂了三个入口（「地热」是**一级菜单**，不在「帮助」之下）：

========================================  ===========================================
菜单                                       执行
========================================  ===========================================
地热 → 井截面取热                         打开**参数界面**（``widgets/well_cross_section.py``），
                                          填完点「开始求解」走同一条 create / solve
地热 → 测试 → 高渗                         ``cases.case_02.test_high_perm``
地热 → 测试 → 近不可渗                      ``cases.case_02.test_low_perm``
========================================  ===========================================

「井截面取热」是**交互式**入口：把 ``create`` 的 9 个参数摆成表单，空着就用默认值；
「测试」下两项是**固定工况**，区别只在渗透率（``1e-11`` vs ``1e-20`` m²）——
高渗时对流补热明显，近不可渗时基本只靠导热，放在一起便于对比。
三者最终跑的都是同一套 ``create`` + ``solve``。

经**控制台线程**（``gui.start``）执行；初始状态与实时状态都走 ``_show.show()``
（``plt`` 绘图：界面里开标签页，无界面时存文件）。

最小插件
--------

按 ``ui/plugins/AGENTS.md`` §0，插件就是「界面启动时在控制台线程里被执行的一段代码」，
本文件是最小形态：**只有装配，没有实现**。算例本体（建模 ``_well_cross_section`` /
绘图 ``_show`` / 求解 / 各个 case）都在同目录其它模块里，本文件不复制其中任何一行。

⚠️ **默认不加载**（``# ** enabled = False``）：它会真的跑一次约 10 年的耦合求解，
不该随界面启动白白占着控制台。要用就在「设置 → 插件」里勾上「默认加载」并重启，
或者对那一行点「临时加载」（不必重启、不写任何设置）。

⚠️ **求解必须经 ``gui.start``**：``tfc.solve`` 是长任务（分钟级），直接放进菜单的
``slot`` 会在 **GUI 线程**里跑，界面整个冻住。``gui.start`` 把它放到控制台线程，
于是工具栏的「暂停 / 继续 / 停止」对它生效 —— 算例里 ``tfc.solve`` 的迭代回调
已经调了 ``gui.break_point()``（无界面时是 no-op）。

⚠️ **控制台是单槽位**（``ui/AGENTS.md`` §6.3）：已经有别的东西在跑时 ``gui.start``
会**静默丢弃**请求、只响一声。所以点菜单前先查 ``gui.is_running()`` 并给出提示，
不让用户面对「点了没反应」（统一由 :func:`_start` 处理）。

⚠️ **不设 ``gui_restore``**：``show()`` 在标签页容器里开图，那只是 ``plt`` 的输出，
不是本插件持有的控件；标签页恢复由 ``plt`` 自己记，这里不必也不该代劳。

Created by DeepSeek, 2026-11-04: 首个入口（仅挂一个自然对流算例）
Modified by DeepSeek, 2026-11-04: 加「地热 → 测试 → Case1」（调用 ``cases.case_01.test``），
    并把「控制台忙检查 + gui.start」抽成 ``_start()`` 供两个入口共用
Modified by DeepSeek, 2026-11-04: 「地热」由「帮助 → 地热」改为**一级菜单**
Modified by DeepSeek, 2026-11-04: 删除「热-流自然对流」与「测试 → Case1」两项
    （``_create.py`` 与 ``cases/case_01.py`` 已移除），只保留 Case2
Modified by DeepSeek, 2026-11-04: 把「测试 → Case2」拆成「高渗」与「近不可渗」两项，
    对应 ``case_02`` 里重命名后的 ``test_high_perm`` / ``test_low_perm``；
    接线逻辑抽成 ``_run_case_02(func_name, label)`` 供两项共用
"""

from zmlx.system import execute_once
from zmlx.ui import gui

#: 菜单路径与文字。⚠️ 菜单名一旦发布就不能改：标签页状态里存的就是这串原文。
#: ⚠️ 「地热」是**一级菜单**（挂在菜单栏根部），不在「帮助」之下 —— 地热是一个
#: 独立的应用场景，算例会越加越多，埋在「帮助 → 地热」里既难找也压不住层级。
MENU = "地热"

#: 「地热 → 测试」子菜单。
#: ⚠️ 一级菜单 ``MENU`` 是 ``str``，拼子菜单要显式写成 list（``str + list`` 会报错）。
#: ⚠️ 测试算例放在该子菜单下，不和平时的算例混在一层。
CASE_MENU = [MENU, "测试"]


def _start(func, *, text_beg, text_end, busy_hint):
    """在**控制台线程**里执行 ``func``（点菜单时统一走这里）.

    ⚠️ 先判 ``gui.is_running()``：控制台忙时 ``gui.start`` 会**静默丢弃**请求、
    只响一声，必须自己把「忙」说清楚（``ui/AGENTS.md`` §6.3 第 1 条）。

    Args:
        func: 要执行的算例函数（无参）。``gui.start`` 会把它放到控制台内核线程，
            于是工具栏的「暂停 / 继续 / 停止」对它生效 —— 算例里 ``tfc.solve``
            的迭代回调本就会调 ``gui.break_point()``。
        text_beg: 开始提示（打印到控制台）。
        text_end: 结束提示。
        busy_hint: 「忙」对话框里说明这次想跑什么。

    Returns:
        bool: 真的提交了任务返回 True；控制台忙、没提交返回 False。
    """
    if gui.exists() and gui.is_running():
        gui.information(
            "控制台正忙",
            "控制台已经在执行其它任务，请等它结束后再运行「{0}」。\n"
            "（控制台同一时刻只能跑一个任务，这是为了避免两个求解互相抢占。）".format(
                busy_hint
            ),
        )
        return False
    gui.start(func, text_beg=text_beg, text_end=text_end)
    return True


def _run_case_02(func_name, label):
    """把「地热 → 测试 → <label>」接到 ``cases.case_02.<func_name>`` 上（内部共用）.

    ⚠️ **只接线到算例自己的函数**：网格、时长、渗透率、参考圆都由 ``case_02`` 决定，
    插件不替它设参 —— 两个工况的区别（渗透率）也完全由算例那边表达。

    ⚠️ 模块在**函数内**才 import：``case_02`` 会顺手拉起 ``tfc`` 与绘图栈，
    放在插件加载期会把这段时间加到界面启动的关键路径上
    （``plugins/AGENTS.md`` §0.5「加载期只接线，不干活」）。

    Args:
        func_name: ``case_02`` 里的函数名，如 ``'test_high_perm'``。
        label: 菜单文字与控制台提示里用的短名，如 ``'高渗'``。
    """
    from zmlx.scen.geothermal.cases import case_02

    _start(
        getattr(case_02, func_name),
        text_beg="开始求解：地热 Case2（井截面，{0}）".format(label),
        text_end="求解结束：地热 Case2（{0}）".format(label),
        busy_hint="Case2 " + label,
    )


def run_high_perm():
    """点「地热 → 测试 → 高渗」时执行：在控制台线程里跑 ``case_02.test_high_perm``."""
    _run_case_02("test_high_perm", "高渗")


def run_low_perm():
    """点「地热 → 测试 → 近不可渗」时执行：在控制台线程里跑 ``case_02.test_low_perm``."""
    _run_case_02("test_low_perm", "近不可渗")


def open_widget():
    """点「地热 → 井截面取热」时执行：打开参数界面（一个标签页）.

    ⚠️ 用 ``gui.get_widget`` 而不是自己建控件：它保证**同一标题只开一个**，
    重复点菜单只是切到已经打开的那个。

    ⚠️ 控件构造时**不做任何求解**，只摆出参数表单 —— 求解要在用户点
    「开始求解」后才经 ``gui.start`` 进控制台线程
    （见 :class:`zmlx.scen.geothermal.widgets.well_cross_section.WellCrossSectionWidget`）。

    ⚠️ 写 ``gui_restore``：这串会被存盘、重启时按原文用 ``gui.xxx(...)`` 重放，
    所以命令名 ``show_geothermal_widget`` **一旦发布不能改**。
    """
    from zmlx.scen.geothermal.widgets.well_cross_section import WellCrossSectionWidget

    def oper(widget):
        """``get_widget`` 每次调用都会执行：记下 ``gui_restore`` 以便重启后自动恢复.

        ⚠️ 写的命令名一旦发布不能改 —— 这串会被原样存盘、重启时按原文重放。
        """
        widget.gui_restore = "gui.show_geothermal_widget()"

    return gui.get_widget(
        the_type=WellCrossSectionWidget,
        caption=WellCrossSectionWidget.CAPTION,
        icon="matplotlib",
        oper=oper,
        tooltip="井截面取热：填参数后求解（等效于跑一遍 case_02）",
    )


@execute_once(file=__file__)
def setup_ui():
    """挂菜单 + 注册命令（**加载期只接线，不干活**）.

    挂三项菜单、注册三条命令，都在加载期完成、不碰任何控件：

    ==============================  ==========================  ===================================
    菜单                              命令                         执行
    ==============================  ==========================  ===================================
    地热 → 井截面取热                 ``show_geothermal_widget``   打开参数界面（``widgets/well_cross_section.py``）
    地热 → 测试 → 高渗                ``show_geothermal_case_02``  ``case_02.test_high_perm``
    地热 → 测试 → 近不可渗             ``..._case_02_low_perm``     ``case_02.test_low_perm``
    ==============================  ==========================  ===================================

    由 :func:`zmlx.system.execute_once` 保证只执行一次 ——
    ``load_all`` 在一次运行里可能被调用多次（启动 + 临时加载）。

    Returns:
        None。
    """
    gui.add_action(
        menu=MENU,
        text="井截面取热",
        slot=open_widget,
        icon="matplotlib",
        tooltip="打开参数界面：填完后按同样的 create / solve 流程求解",
        overwrite=False,
    )
    gui.add_action(
        menu=CASE_MENU,
        text="高渗",
        slot=run_high_perm,
        icon="matplotlib",
        tooltip="井截面取热：高渗（perm=1e-11 m²），对流补热明显",
        overwrite=False,
    )
    gui.add_action(
        menu=CASE_MENU,
        text="近不可渗",
        slot=run_low_perm,
        icon="matplotlib",
        tooltip="井截面取热：近不可渗（perm=1e-20 m²），基本只靠导热",
        overwrite=False,
    )
    gui.add_func("show_geothermal_widget", open_widget)
    gui.add_func("show_geothermal_case_02", run_high_perm)
    gui.add_func("show_geothermal_case_02_low_perm", run_low_perm)


if __name__ == "__zml_plugin__":
    # 插件机制执行时 ``__name__`` 是 ``'__zml_plugin__'``：只注册，不开窗口。
    setup_ui()

if __name__ == "__main__":
    # ``python zml_plugin.py`` 直接运行：开一个界面，菜单里能看到这一项。
    # ⚠️ 用独立的 ``if`` 而不是 ``elif``：两种运行方式的判断互不相干。

    def main():
        """直接运行本文件时的入口：挂菜单（供 ``gui.execute`` 调用）."""
        setup_ui()
        gui.show_geothermal_widget()

    gui.execute(main, close_after_done=False)
