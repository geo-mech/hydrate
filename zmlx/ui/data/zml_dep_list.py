import os.path


def main():
    from zmlx.io.json_ex import write
    packages = [
        dict(package_name='numpy', import_name='numpy'),
        dict(package_name='scipy', import_name='scipy'),
        dict(package_name='matplotlib',
             import_name='matplotlib'),
        dict(package_name='PyOpenGL', import_name='OpenGL'),
        dict(package_name='pyqtgraph', import_name='pyqtgraph'),
        dict(package_name='pypiwin32', import_name='win32com'),
        dict(package_name='pywin32', import_name='pywintypes'),
        dict(package_name='chemicals', import_name='chemicals'),
    ]
    fname = os.path.join(os.path.dirname(__file__), 'zml_dep_list.json')
    write(fname, packages, encoding='utf-8')


if __name__ == '__main__':
    main()
