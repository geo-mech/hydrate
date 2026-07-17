from zmlx.system import warn, deprecated

warn('setup_files.py is deprecated.', DeprecationWarning, stacklevel=2)
from zmlx.ui import exts


@deprecated(alternative='zmlx.ui.exts.get_rank', remove_after='2027-7-6')
def get_rank(*args, **kwargs):
    return exts.get_rank(*args, **kwargs)


@deprecated(alternative='zmlx.ui.exts.set_rank', remove_after='2027-7-6')
def set_rank(*args, **kwargs):
    exts.set_rank(*args, **kwargs)


@deprecated(alternative='zmlx.ui.exts.get_files', remove_after='2027-7-6')
def get_files(*args, **kwargs):
    return exts.get_files(*args, **kwargs)


@deprecated(alternative='zmlx.ui.exts.set_files', remove_after='2027-7-6')
def set_files(*args, **kwargs):
    exts.set_files(*args, **kwargs)
