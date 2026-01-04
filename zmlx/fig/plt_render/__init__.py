from zmlx.plt import get_cm
from zmlx.plt.on_axes import (
    add_cbar, add_contourf, add_dfn2, add_field2, add_rc3, add_scatter, add_surf, add_tricontourf, add_trimesh,
    add_trisurf
)

from zmlx.plt.on_axes.data import add_to_axes
from zmlx.plt.on_figure.data import add_to_figure, show

__all__ = [
    'get_cm', 'add_cbar', 'add_contourf', 'add_dfn2', 'add_field2',
    'add_rc3', 'add_scatter',
    'add_surf', 'add_tricontourf', 'add_trimesh', 'add_trisurf',
    'add_to_axes', 'add_to_figure', 'show'
]
