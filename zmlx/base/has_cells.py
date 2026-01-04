from zmlx.geometry.base import point_distance
from zmlx.ui import gui
from zmlx import fig


def get_nearest_cell(model, pos, mask=None):
    """
    找到model中，距离给定的pos最为接近的cell
    """
    if model.cell_number == 0:
        return None

    result = None
    dist = 1.0e100

    # 遍历，找到最接近的cell.
    for cell in model.cells:
        if mask is not None:
            if not mask(cell):  # 只有满足条件的cell才会被检查.
                continue

        # 计算距离
        d = point_distance(cell.pos, pos)
        if result is None or d < dist:
            dist = d
            result = cell  # 更新结果

    # 返回结果
    return result


def get_pos_range(model, dim):
    """
    返回cells在某一个坐标维度上的范围

    参数:
    - model: 网格模型对象
    - dim: 维度索引（0表示x维度，1表示y维度，2表示z维度）

    返回:
    - l_range: 该维度上的最小位置值
    - r_range: 该维度上的最大位置值

    异常:
    - 断言错误: 如果模型中的单元格数量小于等于0，或者维度索引不在[0, 2]范围内
    """
    assert model.cell_number > 0
    assert 0 <= dim <= 2
    l_range, r_range = 1e100, -1e100
    for c in model.cells:
        p = c.pos[dim]
        l_range = min(l_range, p)
        r_range = max(r_range, p)
    return l_range, r_range


def get_cells_in_range(model, xr=None, yr=None, zr=None,
                       center=None, radi=None):
    """
    返回在给定的坐标范围内的所有的cell. 其中xr为x坐标的范围，yr为y坐标的范围，zr为
    z坐标的范围。当某个范围为None的时候，则不检测.

    参数:
    - model: 网格模型对象
    - xr: x坐标范围（可选）
    - yr: y坐标范围（可选）
    - zr: z坐标范围（可选）
    - center: 中心点坐标（可选）
    - radi: 半径（可选）

    返回:
    - cells: 在给定范围内的单元格列表

    异常:
    - 无异常抛出
    """
    if xr is None and yr is None and zr is None and center is not None and radi is not None:
        cells = []
        for c in model.cells:
            if point_distance(center, c.pos) <= radi:
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

    参数:
    - model: 网格模型对象
    - xr: x坐标范围（可选）
    - yr: y坐标范围（可选）
    - zr: z坐标范围（可选）

    返回:
    - mask: 在给定范围内的单元格索引列表

    异常:
    - 无异常抛出
    """

    def get_(v, r):
        """
        根据给定的值和范围生成一个布尔掩码。

        参数:
        - v: 值的列表
        - r: 范围（可选）

        返回:
        - mask: 布尔掩码列表
        """
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
    """
    从网格模型中获取指定索引的单元格位置信息

    参数:
    - model: 网格模型对象
    - index: 索引元组，默认为 (0, 1, 2)，表示获取 x、y、z 坐标

    返回:
    - results: 包含指定索引位置信息的元组

    异常:
    - 无异常抛出
    """
    vpos = [cell.pos for cell in model.cells]
    results = []
    for i in index:
        results.append([pos[i] for pos in vpos])
    return tuple(results)


def get_cell_property(model, get):
    """
    从网格模型中获取每个单元格的指定属性值

    参数:
    - model: 网格模型对象
    - get: 用于获取单元格属性的函数

    返回:
    - results: 包含每个单元格属性值的列表

    异常:
    - 无异常抛出
    """
    return [get(cell) for cell in model.cells]


def plot_tricontourf(model, get, caption=None, gui_only=False, title=None,
                     triangulation=None,
                     fname=None, dpi=300):
    """
    绘制网格模型中每个单元格的指定属性值的三角剖分等值线图。

    参数:
    - model: 网格模型对象
    - get: 用于获取单元格属性的函数
    - caption: 图形标题（可选）
    - gui_only: 是否仅在图形用户界面中显示（可选）
    - title: 图形标题（可选）
    - triangulation: 三角剖分对象（可选）
    - fname: 保存文件名（可选）
    - dpi: 图像分辨率（可选）

    返回:
    - 无返回值

    异常:
    - 无异常抛出
    """
    if gui_only and not gui.exists():
        return
    z = [get(cell) for cell in model.cells]
    if triangulation is None:
        pos = [cell.pos for cell in model.cells]
        x = [p[0] for p in pos]
        y = [p[1] for p in pos]
        o = fig.tricontourf(x=x, y=y, z=z, triangulation=None, levels=20, cmap='coolwarm')
    else:
        o = fig.tricontourf(z=z, triangulation=triangulation, levels=20, cmap='coolwarm')
    fig.show(
        fig.axes2(
            o, xlabel='x/m', ylabel='y/m', aspect='equal', title=title
        ),
        caption=caption, gui_only=gui_only, fname=fname, dpi=dpi
    )
