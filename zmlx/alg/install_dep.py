from zmlx.alg.pip_install import pip_install


def install_dep():
    """
    尝试安装zml运行所需要的所有的模块
    """
    for name, pip in [
        ('numpy', 'numpy'),
        ('scipy', 'scipy'),
        ('matplotlib', 'matplotlib'),
    ]:
        pip_install(pip, name=name)

    from zmlx.ui.alg.get_preferred_qt_version import get_preferred_qt_version
    version = get_preferred_qt_version()
    print(f'The preferred Qt Version is: {version}')

    if version == 'PyQt5':
        for name, pip in [
            ('PyQt5', 'PyQt5'),
            ('PyQt5.QtWebEngineWidgets', 'PyQtWebEngine'),
        ]:
            pip_install(pip, name=name)

    if version == 'PyQt6':
        for name, pip in [
            ('PyQt6', 'PyQt6'),
            ('PyQt6.QtWebEngineWidgets', 'PyQt6-WebEngine'),
        ]:
            pip_install(pip, name=name)

    for name, pip in [
        ('OpenGL', 'PyOpenGL'),
        ('pyqtgraph', 'pyqtgraph'),
    ]:
        pip_install(pip, name=name)


if __name__ == '__main__':
    install_dep()
