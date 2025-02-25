import sys

from zmlx.alg.pip_install import pip_install


def install_dep(show_exists=True):
    """
    安装计算模块运行所需要的第三方的包
    """
    found_qt = False
    if not found_qt:
        try:
            import PyQt6
            found_qt = True
            pip_install('PyQt6-WebEngine', 'PyQt6.QtWebEngineWidgets', show_exists=show_exists)
            pip_install('pyqt6-qscintilla', 'PyQt6.Qsci', show_exists=show_exists)
        except:
            pass

    if not found_qt:
        try:
            import PyQt5
            found_qt = True
            pip_install('PyQtWebEngine', 'PyQt5.QtWebEngineWidgets', show_exists=show_exists)
        except:
            pass

    if not found_qt:
        if sys.version_info >= (3, 8):
            items = [('PyQt6', 'PyQt6'),
                     ('PyQt6-WebEngine', 'PyQt6.QtWebEngineWidgets'),
                     ('pyqt6-qscintilla', 'PyQt6.Qsci')
                     ]
        else:
            items = [('PyQt5', 'PyQt5'),
                     ('PyQtWebEngine', 'PyQt5.QtWebEngineWidgets')
                     ]
        for package_name, name in items:
            pip_install(package_name, name=name, show_exists=show_exists)

    for package_name, name in [
        ('numpy', 'numpy'),
        ('scipy', 'scipy'),
        ('matplotlib', 'matplotlib'),
        ('PyOpenGL', 'OpenGL'),
        ('pyqtgraph', 'pyqtgraph'),
        ('pypiwin32', 'win32com'),
        ('pywin32', 'pywintypes'),
        ('dulwich', 'dulwich'),
    ]:
        pip_install(package_name, name=name, show_exists=show_exists)


if __name__ == '__main__':
    install_dep()
