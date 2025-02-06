from zmlx.alg.import_module import import_module


def install_dep(show=None):
    """
    尝试安装zml运行所需要的所有的模块
    """
    for name, pip in [
        ('numpy', 'numpy'),
        ('scipy', 'scipy'),
        ('matplotlib', 'matplotlib'),
    ]:
        import_module(name=name, pip=pip, show=show)

    from zmlx.ui.alg.get_preferred_qt_version import get_preferred_qt_version
    version = get_preferred_qt_version()
    print(f'The preferred Qt Version is: {version}')

    if version == 'PyQt5':
        for name, pip in [
            ('PyQt5', 'PyQt5'),
            ('PyQt5.QtWebEngineWidgets', 'PyQtWebEngine'),
        ]:
            import_module(name=name, pip=pip, show=show)

    if version == 'PyQt6':
        for name, pip in [
            ('PyQt6', 'PyQt6'),
            ('PyQt6.QtWebEngineWidgets', 'PyQt6-WebEngine'),
        ]:
            import_module(name=name, pip=pip, show=show)

    for name, pip in [
        ('OpenGL', 'PyOpenGL'),
        ('pyqtgraph', 'pyqtgraph'),
    ]:
        import_module(name=name, pip=pip, show=show)


if __name__ == '__main__':
    install_dep(print)
