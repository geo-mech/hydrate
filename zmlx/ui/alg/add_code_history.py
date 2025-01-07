import os
import shutil

from zml import app_data
from zmlx.filesys.tag import time_string


def add_code_history(fname):
    try:
        if fname is None:
            return
        if os.path.isfile(fname):
            shutil.copy(fname,
                        app_data.root('console_history', f'{time_string()}.py'))
    except:
        pass
