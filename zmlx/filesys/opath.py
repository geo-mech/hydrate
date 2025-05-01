from zmlx.alg.sys import create_deprecated as create, get_deprecated as get

_deprecated_funcs = dict(
    opath=create('zmlx.io.path', 'get_path', '2026-2-11'),
    get=create('zmlx.io.path', 'get_path', '2026-2-11'),
    get_opath=create('zmlx.io.path', 'get_path', '2026-2-11'),
    set_opath=create('zmlx.io.path', 'set_path', '2026-2-11'),
    set=create('zmlx.io.path', 'set_path', '2026-2-11'),
    TaskFolder=create('zmlx.io.TaskFolder', 'TaskFolder', '2026-2-11'),
)


def __getattr__(name):
    return get(name, data=_deprecated_funcs, current_pack_name='zmlx.filesys.opath')


import warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)


from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)