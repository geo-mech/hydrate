def show_widget(widget, caption=None, use_gui=False, **kwargs):
    if use_gui:
        from zmlx.ui import gui

        def f():
            gui.get_widget(the_type=widget, type_kw=kwargs, caption=caption)

        gui.execute(f, keep_cwd=False,
                    close_after_done=False)
    else:
        import sys
        from zmlx.ui.Qt import QtWidgets
        app = QtWidgets.QApplication(sys.argv)
        w = widget(**kwargs)
        w.show()
        sys.exit(app.exec())
