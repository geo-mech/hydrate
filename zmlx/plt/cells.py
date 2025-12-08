from zmlx.alg.fsys import join_paths, make_fname
from zmlx.base.seepage import get_cell_pos, get_time, get_cell_pre, get_cell_temp, list_comp, get_cell_fm, get_cell_fv, \
    Seepage
from zmlx.plt.fig2 import tricontourf
from zmlx.ui import gui


def show_cells(
        model: Seepage, dim0, dim1, mask=None, show_p=True, show_t=True,
        show_s=True, folder=None, use_mass=False, **opts):
    """
    二维绘图显示

    Args:
        model: Seepage 模型对象
        dim0: 第一个维度索引（0, 1, 2 分别对应 x, y, z 维度）
        dim1: 第二个维度索引（0, 1, 2 分别对应 x, y, z 维度）
        mask: 可选的掩码，用于筛选特定的单元格
        show_p: 是否显示压力（默认为 True）
        show_t: 是否显示温度（默认为 True）
        show_s: 是否显示饱和度（默认为 True）
        folder: 图像保存的文件夹路径（可选）
        use_mass: 是否使用质量饱和度（默认为 False）

    Returns:
        None

    该函数通过获取模型中单元格的位置和属性值，使用 tricontourf 函数绘制二维等值线图，
    显示模型中单元格的压力、温度和饱和度分布。如果提供了文件夹路径，则将图像保存到指定文件夹中。
    """
    if not gui:
        return

    x = get_cell_pos(model=model, dim=dim0, mask=mask)
    y = get_cell_pos(model=model, dim=dim1, mask=mask)

    kw = dict(title=f'time = {get_time(model, as_str=True)}')
    kw.update(opts)

    year = get_time(model) / (365 * 24 * 3600)

    if show_p:  # 显示压力
        v = get_cell_pre(model, mask=mask) / 1e6
        tricontourf(
            x, y, v, caption='pressure', cbar=dict(label='pressure (MPa)'),
            fname=make_fname(
                year, join_paths(folder, 'pressure'),
                '.jpg', 'y'),
            **kw)

    if show_t:  # 显示温度
        v = get_cell_temp(model, mask=mask)
        tricontourf(
            x, y, v, caption='temperature', cbar=dict(label='temperature (K)'),
            fname=make_fname(
                year, join_paths(folder, 'temperature'),
                '.jpg', 'y'),
            **kw)

    if not isinstance(show_s, list):
        if show_s:  # 此时，显示所有组分的饱和度
            show_s = list_comp(model, keep_structure=False)  # 所有的组分名称

    if isinstance(show_s, list):
        if use_mass:  # 此时，显示质量饱和度
            get = get_cell_fm
        else:
            get = get_cell_fv

        fv_all = get(model=model, mask=mask)
        for name in show_s:
            assert isinstance(name, str)
            idx = model.find_fludef(name=name)
            assert idx is not None
            fv = get(model=model, fid=idx, mask=mask)  # 流体体积
            v = fv / fv_all
            # 绘图
            tricontourf(
                x, y, v, caption=name, cbar=dict(label='saturation'),
                fname=make_fname(
                    year, join_paths(folder, name),
                    '.jpg', 'y'),
                **kw)
