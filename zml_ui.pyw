import os
import subprocess
import sys


def pip_install(package_name, name=None, show_exists=True):
    """使用pip安装指定的Python包。

    如果提供了name参数，会先检查该模块是否已存在，只有在模块不存在时才会安装package_name。

    Args:
        show_exists: 在包已经存在的时候，是否显示提示信息。
        package_name (str): 要安装的Python包名称。
        name (str, optional): 要检查的模块名称。如果为None，则直接安装package_name。

    Returns:
        None
    """
    try:
        if name is not None:
            from importlib.util import find_spec
            if find_spec(name):
                if show_exists:
                    print(f"安装包 {package_name} 已经存在!")
                return
        subprocess.check_call([f'{os.path.abspath(sys.executable)}',
                               '-m', 'pip', 'install',
                               package_name])
    except subprocess.CalledProcessError as e:
        print(f"安装包 {package_name} 失败: {e}")


def install_dep(show_exists=True):
    """
    安装计算模块运行所需要的第三方的包
    """
    found_qt = False
    if not found_qt:
        try:
            import PyQt6
            found_qt = True
            pip_install('PyQt6-WebEngine', 'PyQt6.QtWebEngineWidgets',
                        show_exists=show_exists)
            pip_install('pyqt6-qscintilla', 'PyQt6.Qsci',
                        show_exists=show_exists)
        except:
            pass

    if not found_qt:
        try:
            import PyQt5
            found_qt = True
            pip_install('PyQtWebEngine', 'PyQt5.QtWebEngineWidgets',
                        show_exists=show_exists)
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


if __name__ == "__main__":
    install_dep(show_exists=False)  # 首先安装依赖项
    from zmlx import open_gui

    open_gui()
