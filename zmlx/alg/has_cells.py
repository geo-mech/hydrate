from zmlx.geometry.point_distance import point_distance as get_distance
from zmlx.plt.tricontourf import tricontourf
from zmlx.ui import gui


def get_pos_range(model, dim):
    """
    返回cells在某一个坐标维度上的范围
    """
    assert model.cell_number > 0
    assert 0 <= dim <= 2
    lrange, rrange = 1e100, -1e100
    for c in model.cells:
        p = c.pos[dim]
        lrange = min(lrange, p)
        rrange = max(rrange, p)
    return lrange, rrange


def get_cells_in_range(model, xr=None, yr=None, zr=None,
                       center=None, radi=None):
    """
    返回在给定的坐标范围内的所有的cell. 其中xr为x坐标的范围，yr为y坐标的范围，zr为
    z坐标的范围。当某个范围为None的时候，则不检测.
    """
    if xr is None and yr is None and zr is None and center is not None and radi is not None:
        cells = []
        for c in model.cells:
            if get_distance(center, c.pos) <= radi:
                cells.append(c)
        return cells
    ranges = (xr, yr, zr)
    cells = []
    for c in model.cells:
        out_of_range = False
        for i in range(len(ranges)):
            r = ranges[i]
            if r is not None:
                p = c.pos[i]
                if p < r[0] or p > r[1]:
                    out_of_range = True
                    break
        if not out_of_range:
            cells.append(c)
    return cells


def get_cell_mask(model, xr=None, yr=None, zr=None):
    """
    返回给定坐标范围内的cell的index。主要用来辅助绘图。since 2024-6-12
    """

    def get_(v, r):
        if r is None:
            return [True] * len(v)  # 此时为所有
        else:
            return [r[0] <= v[i] <= r[1] for i in range(len(v))]

    v_pos = [c.pos for c in model.cells]
    # 三个方向分别的mask
    x_mask = get_([pos[0] for pos in v_pos], xr)
    y_mask = get_([pos[1] for pos in v_pos], yr)
    z_mask = get_([pos[2] for pos in v_pos], zr)

    # 返回结果
    return [x_mask[i] and y_mask[i] and z_mask[i] for i in range(len(x_mask))]


def get_cell_pos(model, index=(0, 1, 2)):
    vpos = [cell.pos for cell in model.cells]
    results = []
    for i in index:
        results.append([pos[i] for pos in vpos])
    return tuple(results)


def get_cell_property(model, get):
    return [get(cell) for cell in model.cells]


def plot_tricontourf(model, get, caption=None, gui_only=False, title=None, triangulation=None,
                     fname=None, dpi=300):
    if gui_only and not gui.exists():
        return
    if triangulation is None:
        pos = [cell.pos for cell in model.cells]
        x = [p[0] for p in pos]
        y = [p[1] for p in pos]
        z = [get(cell) for cell in model.cells]
        tricontourf(x=x, y=y, z=z, caption=caption, gui_only=gui_only,
                    title=title, triangulation=None, fname=fname, dpi=dpi, levels=20, cmap='coolwarm',
                    xlabel='x/m', ylabel='y/m', aspect='equal')
    else:
        z = [get(cell) for cell in model.cells]
        tricontourf(z=z, caption=caption, gui_only=gui_only,
                    title=title, triangulation=triangulation, fname=fname, dpi=dpi, levels=20, cmap='coolwarm',
                    xlabel='x/m', ylabel='y/m', aspect='equal')
