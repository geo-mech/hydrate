import zmlx.alg.sys as warnings

from zmlx.plt.trisurf import plot_trisurf

_keep = [plot_trisurf]

warnings.warn(
    f'The modulus {__name__} is deprecated and '
    f'will be removed after 2026-4-16, import functions directly from <zmlx> instead',
    DeprecationWarning, stacklevel=2
)
