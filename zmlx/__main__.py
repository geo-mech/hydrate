import sys


def _env():
    from zmlx.alg import install_dep
    install_dep()


def _demo():
    from zmlx.ui import gui
    def f():
        gui.show_demo()

    gui.execute(f, close_after_done=False)


def _show_ui(argv):
    from zmlx.ui.gui_buffer import open_gui
    open_gui(argv)


def main():
    if len(sys.argv) < 2:
        from zmlx.exts import about
        print(about())
        return

    key = sys.argv[1]
    argv = sys.argv[1:]

    if key == 'env' or key == 'install_dep':
        _env()
        return

    if key == 'demo':
        _demo()
        return

    if key == 'ui':
        _show_ui(argv)
        return


if __name__ == "__main__":
    main()
