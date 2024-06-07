from zmlx.alg.import_module import import_module


def install_dep(show=None):
    """
    尝试安装zml运行所需要的所有的模块
    """
    for name, pip in [
        ('PyQt5', 'PyQt5'),
        ('PyQt5.QtWebEngineWidgets', 'PyQtWebEngine'),
        ('numpy', 'numpy'),
        ('scipy', 'scipy'),
        ('matplotlib', 'matplotlib'),
        ('OpenGL', 'PyOpenGL'),
        ('pyqtgraph', 'pyqtgraph'),
    ]:
        import_module(name=name, pip=pip, show=show)


if __name__ == '__main__':
    install_dep(print)
