# ** name = 'Quick Look 快速评估'
# ** desc = '2D 单相流压力的快速评估工具：注册「帮助 → 加载 → Quick Look 快速评估」入口'
# ** enabled = False
"""Quick Look 快速评估 — GUI 集成入口.

仿照 scen/frac/zml_plugin.py 的模式：
  帮助 > 加载 > Quick Look 快速评估 → 注册 Quick_Look 菜单
  Quick_Look > 打开评估控件 → 打开参数输入与结果显示控件
"""

from zmlx.system import execute_once
from zmlx.ui import gui


def open_the_widget():
    from zmlx.scen.quick_look._widget import QuickLookWidget
    gui.get_widget(
        the_type=QuickLookWidget,
        caption='Quick Look 快速评估',
        icon='matplotlib',
        tooltip='2D 单相流压力快速评估工具',
    )


@execute_once(file=__file__)
def main():
    gui.add_action(
        menu=['帮助', '加载'],
        text='Quick Look 快速评估',
        slot=open_the_widget,
    )


if __name__ == '__zml_plugin__':
    # 插件机制执行时 ``__name__`` 是 ``'__zml_plugin__'``：只注册
    # 「帮助 → 加载 → Quick Look 快速评估」这一项，不要开窗口。
    main()

if __name__ == '__main__':
    # ⚠️ 用独立的 ``if`` 而不是 ``elif``：两种运行方式的判断互不相干。
    if gui.exists():
        main()
    else:
        def main_x():
            main()
            open_the_widget()


        gui.execute(main_x, close_after_done=False)
