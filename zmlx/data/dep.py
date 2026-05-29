# zmlx 计算模块运行所需要的第三方的包

import sys

package_names = [
    'numpy', 'scipy', 'matplotlib', 'pyqtgraph',
    'PyQt6', 'PyQt6-WebEngine', 'pyqt6-qscintilla',
    'PyOpenGL', 'dulwich',
    'pillow', 'pyvista', 'pyvistaqt', 'vtk', 'pandas', 'openpyxl'
]

if sys.platform.startswith('win'):
    package_names.extend(['pypiwin32', 'pywin32'])

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
