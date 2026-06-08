from zmlx.plt.on_axes import add_cbar

_keep = [add_cbar]

import zmlx.alg.sys as warnings

warnings.warn(f'The module {__name__} will be removed after 2027-5-23',
              DeprecationWarning, stacklevel=2)
