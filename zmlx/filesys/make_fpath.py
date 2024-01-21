from zmlx.filesys.make_dirs import make_dirs
import os

__all__ = ['make_fpath']


def make_fpath(folder, step=None, ext='.txt', name=None):
    """
    Returns a filename to output data, and ensures that the folder exists
    """
    assert isinstance(folder, str)
    if not os.path.exists(folder):
        make_dirs(folder)
    else:
        assert os.path.isdir(folder)
    assert step is not None or name is not None
    if step is not None:
        return os.path.join(folder, f'{step:010d}{ext}')
    if name is not None:
        return os.path.join(folder, name)

