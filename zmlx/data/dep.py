"""第三方包依赖信息。

Modified by Claude, 2026-08-12
"""
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

# zmlx 计算模块运行所需要的第三方的包的一句话说明（根据包名）
#
# ⚠️ 这里是**唯一**的说明来源：「设置 → 运行环境」的「备注」列直接读它，
#    所以改这里就等于改界面上显示的说明。找不到说明的包退回默认文案
#    （「zmlx 的核心依赖」），不会报错。
package_notes = {
    'numpy': '数值数组与线性代数，几乎所有计算模块的基础',
    'scipy': '稀疏矩阵与线性求解，渗流求解器的默认后端',
    'matplotlib': '绘图后端，zmlx.plt 与 MatplotWidget 的底层',
    'pyqtgraph': '交互式绘图，zmlx.pg 的高性能曲线 / 三维显示',
    'PyQt6': '图形界面框架，整个 GUI 的基础',
    'PyQt6-WebEngine': '内嵌网页浏览器，用于显示 PDF、网页与在线文档',
    'pyqt6-qscintilla': '代码编辑器控件（语法高亮、自动补全）',
    'PyOpenGL': '三维绘图的 OpenGL 绑定',
    'dulwich': '纯 Python 的 git 实现，用于检查程序更新',
    'pillow': '读写图片（PNG / JPG），图片浏览与图标的基础',
    'pyvista': '三维网格可视化，VtkView 与三维显示',
    'pyvistaqt': '把 pyvista 的三维视图嵌进 Qt 界面',
    'vtk': '三维可视化的底层引擎（pyvista 依赖它）',
    'pandas': '表格数据的读写与处理',
    'openpyxl': '读写 Excel（.xlsx）文件',
    'pywin32': '调用 Windows 系统接口（快捷方式、剪贴板等）',
    'pypiwin32': 'pywin32 的废弃别名（保留仅为兼容，不要单独安装）',
}
