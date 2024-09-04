import sys

from zmlx.ui.GuiBuffer import gui


def show_readme():
    try:
        gui.trigger('readme.txtpy')
    except Exception as e:
        print(f'Error: {e}')


def open_gui(argv=None):
    """
    打开gui; 将首先尝试安装依赖项.
    """
    # 尝试安装依赖项
    try:
        from zmlx.alg.install_dep import install_dep
        install_dep(show=print)
    except:
        pass

    gui.execute(show_readme, keep_cwd=False, close_after_done=False)


if __name__ == "__main__":
    open_gui(sys.argv)
