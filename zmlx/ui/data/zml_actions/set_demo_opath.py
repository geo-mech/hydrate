text = '设置demo项目输出数据的默认目录'


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
    window = get_window()
    if window is not None:
        return not window.is_running()
