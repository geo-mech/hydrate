if __name__ == "__main__":
    from zmlx.alg.install_dep import install_dep

    install_dep(show_exists=False)  # 首先安装依赖项
    from zmlx import open_gui

    open_gui()
