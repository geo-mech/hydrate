# ** name = '界面桥'
# ** desc = '把运行中的界面暴露成本机 RPC：外部进程可查状态、截图、打开指定页面'
# ** enabled = False
"""「界面桥」插件入口（菜单「设置 → 界面桥（实验）」）.

这个插件做两件事：

1. **注册唯一的 gui 命令 ``bridge_call``** —— 外部 HTTP 请求最终都落到它，
   由它派发到 :mod:`~zmlx.scen.gui_bridge.methods`（在 GUI 线程执行）。
2. **挂一个测试面板**（:class:`~zmlx.scen.gui_bridge.test_panel.BridgeTestPanel`），
   让用户开两个实例就能自己验证「两个进程能不能通讯」。

⚠️ **默认不启用**（``# ** enabled = False``）：它一旦开放，信任边界就从「模型」
变成「本机任何进程」（设计见 ``ReadMe.md`` §9）。启用方式：
「设置 → 插件」里勾选「界面桥」。

⚠️ **服务不会随启动自动起**：插件只挂菜单与命令，端口要在测试面板里手动点「启动服务」。
这样用户永远知道它开没开。

⚠️ **只注册一个命令**，不把每个方法都铺成 ``gui.xxx``：单一入口才好做白名单校验与
审计。⚠️ 这与「省 gui 通道」无关 —— 20 通道池已于 v1.9.9 删除（每调用新建一个通道、
无并发上限、不再丢弃），所以铺开并不会撞上限，纯粹是不该多开面。

Created by DeepSeek, 2026-10-30: 第一版（MVP：ping / info / commands / tabs /
    show / screenshot）
"""

from zmlx.system import execute_once

#: 唯一的 gui 命令名（与 ``server.COMMAND_NAME`` 必须一致；外部请求全部从这里进来）
COMMAND_NAME = 'bridge_call'


def show_gui_bridge():
    """打开（或切到）「界面桥」标签页；同时也是 GUI 命令 ``gui.show_gui_bridge()``.

    ⚠️ 走 ``gui.command`` 而不是直接开标签页：菜单是 GUI 线程调的，但命令也可能
    被脚本/后台线程调用 —— 走命令表才能保证「开标签页」发生在 GUI 线程里。
    """
    from zmlx.ui import gui

    gui.command('show_gui_bridge')


def _open():
    """真正打开标签页（注册成命令，故只在 GUI 线程里执行）."""
    from zmlx.ui import gui
    from zmlx.scen.gui_bridge.test_panel import BridgeTestPanel

    def _oper(widget):
        widget.gui_restore = 'gui.show_gui_bridge()'

    gui.get_widget(
        the_type=BridgeTestPanel,
        caption='界面桥',
        on_top=True,
        oper=_oper,
        tooltip='界面桥：启动本机 RPC 服务，或连接另一个 IGG-Hydrate 实例做连通性测试',
    )


@execute_once(file=__file__)
def setup_ui():
    """注册命令与菜单项（由 ``plugins.load_all`` 执行本文件时触发）."""
    from zmlx.ui import gui

    from zmlx.scen.gui_bridge import methods

    # ① 外部请求的唯一入口。⚠️ **不要** mark_direct：它要建控件、切标签页，
    #    必须派发到 GUI 线程（见 ReadMe.md §6.2）。
    gui.add_func(COMMAND_NAME, methods.dispatch)

    # ② 打开面板的命令
    gui.add_func('show_gui_bridge', _open)

    # ③ 菜单
    gui.add_action(
        menu='设置',
        name='gui_bridge',
        text='界面桥（实验）',
        slot=show_gui_bridge,
        overwrite=False,
    )


# ⚠️ 插件的标准形式：注册写在这个分支里。
#    插件机制用 ``exec`` 执行本文件时 ``__name__`` 是 ``'__zml_plugin__'``，
#    于是这里成立 —— 只注册，不开窗口。
if __name__ == '__zml_plugin__':
    setup_ui()
