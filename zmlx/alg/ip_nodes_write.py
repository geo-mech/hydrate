from zmlx.exts import ip

ip_nodes_write = ip.ip_nodes_write

__all__ = [
    'ip_nodes_write'
]

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)
