# zmlx 计算模块运行所需要的第三方的包
package_names = [
    'numpy', 'scipy', 'matplotlib', 'pyqtgraph',
    'PyQt6', 'PyQt6-WebEngine', 'pyqt6-qscintilla',
    'PyOpenGL', 'pypiwin32', 'pywin32', 'dulwich',
    'pillow', 'pyvista', 'pyvistaqt', 'vtk', 'pandas', 'openpyxl'
]

# zmlx 计算模块运行所需要的第三方的包的导入名(根据包名)
import_names = {
    'numpy': 'numpy', 'scipy': 'scipy', 'matplotlib': 'matplotlib', 'pyqtgraph': 'pyqtgraph',
    'PyOpenGL': 'OpenGL',
    'pypiwin32': 'win32com',
    'pywin32': 'pywintypes',
    'dulwich': 'dulwich',
    'pillow': 'PIL',
    'pyvista': 'pyvista',
    'pyvistaqt': 'pyvistaqt',
    'vtk': 'vtk',
    'PyQt6-WebEngine': 'PyQt6.QtWebEngineWidgets',
    'pyqt6-qscintilla': 'PyQt6.Qsci',
    'PyQt6': 'PyQt6',
    'pandas': 'pandas',
    'openpyxl': 'openpyxl'
}
