import zmlx.alg.sys as warnings
from zmlx.plt.on_axes import add_surf

warnings.warn(f'The module {__name__} will be removed after 2027-5-23',
              DeprecationWarning, stacklevel=2)
_keep = [add_surf]
