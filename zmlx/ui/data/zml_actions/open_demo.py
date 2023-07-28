# ** on_toolbar = True
# ** icon = 'python.png'
# ** dependency = """from zmlx import get_path \nimport os\nassert os.path.isdir(get_path('demo'))"""

import os

from zmlx import get_path, gui
from zmlx.ui.FileAlg import open_file_by_dlg


def run():
    folder = get_path('demo')
    if os.path.isdir(folder):
        open_file_by_dlg(folder)
    else:
        gui.information('失败', '未找到demos文件夹')


gui.execute(run, close_after_done=False)
