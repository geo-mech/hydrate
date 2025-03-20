text = '设置示例的数据输出'
on_toolbar = True
tooltip = '设置demo中的项目运行的时候输出数据的文件夹，如果不设置，则一般默认不输出数据'


def slot():
    from zmlx.ui.GuiBuffer import gui
    from zmlx.demo.opath import set_output, opath
    if gui.exists():
        root = opath()
        name = gui.get_existing_directory('Choose Demo Output Folder', root)
        if len(name) > 0:
            set_output(name)
        else:
            print(f'Current folder: {root}')
    else:
        print(opath())


def enabled():
    from zmlx.ui.MainWindow import get_window
    from zmlx.ui.Widgets.Demo import DemoWidget
    window = get_window()
    if window is None:
        return False
    if window.is_running():
        return False
    return isinstance(window.get_current_widget(), DemoWidget)
