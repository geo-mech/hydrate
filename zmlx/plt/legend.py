from zmlx.plt.on_axes import add_legend

_keep = [add_legend]

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2027-5-23',
              DeprecationWarning, stacklevel=2)
