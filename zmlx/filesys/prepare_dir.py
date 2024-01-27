import os

from zml import question
from zmlx.filesys.make_dirs import make_dirs


def prepare_dir(folder, direct_del=False):
    """
    Prepare an empty folder for output calculation data
    """
    if folder is None:
        return
    if os.path.exists(folder):
        if direct_del:
            y = True
        else:
            y = question(f'Do you want to delete the existed folder <{folder}>?')
        if y:
            import shutil
            shutil.rmtree(folder)
    if not os.path.exists(folder):
        make_dirs(folder)
