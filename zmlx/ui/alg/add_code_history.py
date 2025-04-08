import os
import shutil

from zml import app_data
from zmlx.filesys.tag import time_string


def add_code_history(fname):
    try:
        if os.path.isfile(fname):
            t_str = time_string()
            shutil.copy(
                fname, app_data.root('console_history', f'{t_str}.py'))
            with open(app_data.root('console_history', f'{t_str}.txt'),
                      'w', encoding='utf-8') as file:  # 记录原文件的位置.
                file.write(fname)
    except:
        pass
