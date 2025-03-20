text = 'Python包设置'
is_sys = True
menu = '设置'


def slot():
    from zmlx.ui.MainWindow import get_window
    from zmlx.ui.Widgets.PackageTable import PackageTable
    from zmlx.ui.Qt import is_PyQt6

    packages = [dict(package_name='numpy', import_name='numpy'),
                dict(package_name='scipy', import_name='scipy'),
                dict(package_name='matplotlib', import_name='matplotlib'),
                dict(package_name='PyOpenGL', import_name='OpenGL'),
                dict(package_name='pyqtgraph', import_name='pyqtgraph'),
                dict(package_name='pypiwin32', import_name='win32com'),
                dict(package_name='pywin32', import_name='pywintypes'),
                dict(package_name='chemicals', import_name='chemicals'),
                ]
    if is_PyQt6:
        packages.append(dict(package_name='PyQt6-WebEngine', import_name='PyQt6.QtWebEngineWidgets'))
    else:
        packages.append(dict(package_name='PyQtWebEngine', import_name='PyQt5.QtWebEngineWidgets'))
    get_window().get_widget(
        the_type=PackageTable, caption='Python包管理', on_top=True,
        type_kw=dict(packages=packages))
