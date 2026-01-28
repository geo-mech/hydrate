from zmlx.plt.cmap import get_cm
from zmlx.plt.on_axes.cbar import add_cbar
from zmlx.plt.on_axes.contourf import add_contourf
from zmlx.plt.on_axes.data import add_to_axes
from zmlx.plt.on_axes.dfn2 import add_dfn2
from zmlx.plt.on_axes.field2 import add_field2
from zmlx.plt.on_axes.rc3 import add_rc3
from zmlx.plt.on_axes.scatter import add_scatter
from zmlx.plt.on_axes.surf import add_surf
from zmlx.plt.on_axes.tricontourf import add_tricontourf
from zmlx.plt.on_axes.trimesh import add_trimesh
from zmlx.plt.on_axes.trisurf import add_trisurf
from zmlx.plt.on_figure.data import add_to_figure, show

_keep = [get_cm, add_cbar, add_contourf, add_dfn2, add_field2, add_rc3, add_scatter,
         add_surf, add_tricontourf, add_trimesh, add_trisurf,
         add_to_axes, add_to_figure, show
         ]
