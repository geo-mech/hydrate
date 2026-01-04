"""
处理对matplotlib的操作。
"""

from zmlx.exts import SelfPath
from zmlx.plt.cmap import get_cm, get_color
from zmlx.plt.fig2 import (
    plot_xy, plotxy, show_dfn2, show_field2, show_fn2,
    tricontourf, trimesh, contourf, plot2
)
from zmlx.plt.fig3 import plot_trisurf, scatter, show_rc3
from zmlx.plt.fn2 import show_fn2
from zmlx.plt.on_axes import (
    add_curve, add_curve2, curve, add_cbar, add_contourf, add_tricontourf, add_trisurf, add_fn2, plot_on_axes,
    add_surf, add_legend
)
from zmlx.plt.on_axes import add_items, item, plot2d, plot3d
from zmlx.plt.on_axes import data as ax_items
from zmlx.plt.on_figure import add_subplot, add_axes2, add_axes3, plot_on_figure
from zmlx.plt.on_figure import data as fig_items
from zmlx.plt.subplot_layout import calculate_subplot_layout

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
