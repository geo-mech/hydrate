# ** desc = '两相流，水驱替油模拟(添加DFN)'
#
# 物理问题描述：
#   本模型在 wat_disp_oil.py（水驱油）的基础上添加离散裂缝网络（DFN），
#   模拟裂缝性储层中的水驱油过程。
#   模型采用二维平面网格（60x60），区域范围0~30m x 0~30m。
#   初始时模型内部充满油（Oil饱和度=1），
#   在左下角以恒定流量1e-5 m3/s注入水，水驱替油向右上角运移。
#   离散裂缝网络由两组方向（近水平和近垂直）的裂缝组成，
#   裂缝通过面的面积放大100倍来模拟高渗透通道效应。
#
# 建模技术要点：
#   1. 使用 dfn2 生成二维离散裂缝网络（两组裂缝角度）
#   2. 沿裂缝路径查找经过的网格面，将面积放大100倍等效模拟高渗透率
#   3. 使用 add_dfn2 在压力/饱和度云图上叠加裂缝网络显示
#   4. 保证每个面只放大一次（避免重复放大）
#   5. 网格精度60x60（比 wat_disp_oil.py 的30x30更精细，以捕捉裂缝细节）

import math

from zmlx import *


def create(jx: int, jy: int, s=None, fid_inj=None):
    """
    创建含离散裂缝网络（DFN）的水驱油模型。

    Args:
        jx: x方向的网格单元数量
        jy: y方向的网格单元数量
        s: 初始饱和度。默认值为 (1, 0)，即油饱和度为1，水饱和度为0
        fid_inj: 注入流体的ID。默认值为1（水）

    Returns:
        tuple: (model, fractures) 包含渗流模型对象和裂缝线段列表
    """
    from zmlx.geometry.dfn2 import dfn2
    from zmlx.plt import show_dfn2

    # 生成离散裂缝网络：
    #   区域范围：x:0~30m, y:0~30m
    #   裂缝长度：3~8m
    #   两组裂缝方向：近水平（-0.2~0.2弧度）和近垂直（pi/2-0.2 ~ pi/2+0.2弧度）
    #   P21（裂缝密度）：0.5 m/m2
    #   最小裂缝长度：0.5m
    fractures = dfn2(
        xr=[0, 30], yr=[0, 30],
        lr=[3, 8],
        angles=np.linspace(-0.2, 0.2, 10).tolist() + np.linspace(math.pi / 2 - 0.2, math.pi / 2 + 0.2, 10).tolist(),
        # 两组角度：近水平一组，近垂直一组
        p21=0.5,
        l_min=0.5)

    # 若GUI存在，则先显示DFN结构
    if gui.exists():
        show_dfn2(fractures, caption='Discrete Fracture Network')

    # 生成二维平面网格：0~30m x 0~30m，厚度1m
    mesh: SeepageMesh = create_cube(
        linspace(0, 30, jx + 1),
        linspace(0, 30, jy + 1), (-0.5, 0.5)
    )

    # 对于DFN经过的单元面，将面积提升到100倍（等效提高渗透率）
    face_number_backup = mesh.face_number  # 备份原始面数量
    faces_has_been_set = set()  # 记录已处理的面，避免重复放大
    for x0, y0, x1, y1 in fractures:
        p0 = [x0, y0, None]
        p1 = [x1, y1, None]
        # 查找裂缝线段经过的所有单元
        cells = tfc.get_cells_along_seg(p0, p1, model=mesh)
        if len(cells) >= 2:
            for i in range(1, len(cells)):
                i0 = cells[i - 1]
                i1 = cells[i]
                face = mesh.get_face(cell_0=mesh.get_cell(i0), cell_1=mesh.get_cell(i1))
                if face is not None:
                    if face.index not in faces_has_been_set:  # 确保area只增加一次
                        face.area *= 100  # 面积放大100倍，等效于渗透率提高100倍
                        faces_has_been_set.add(face.index)
    print(f'DFN added ({len(faces_has_been_set)} faces set). face number: {face_number_backup} -> {mesh.face_number}')

    x0, x1 = mesh.get_pos_range(0)
    y0, y1 = mesh.get_pos_range(1)

    # 右上角设为大体积单元作为定压出口边界
    for cell in mesh.cells:
        x, y, z = cell.pos
        if abs(y - y1) < 0.1 and abs(x - x1) < 0.1:
            cell.vol = 1.0e8

    # 定义流体
    fluid_defs = [
        FluDef(den=50, vis=1.0e-2, name='oil'),
        FluDef(den=1000, vis=1.0e-3, name='water')
    ]

    if s is None:
        s = (1, 0)

    # 创建渗流模型
    model: Seepage = tfc.create(
        mesh, porosity=0.2, pore_modulus=100e6,
        p=1e6, temperature=280,
        s=s,
        perm=1e-14,
        disable_update_den=True,
        disable_update_vis=True,
        disable_ther=True,
        disable_heat_exchange=True,
        fludefs=fluid_defs
    )

    if fid_inj is None:
        fid_inj = 1

    # 在左下角设置注入井
    cell = model.get_nearest_cell((x0, y0, 0))
    assert cell is not None
    model.add_injector(
        fluid_id=fid_inj,
        flu=cell.get_fluid(1),
        pos=cell.pos,
        radi=0.1,
        opers=[(0, 1.0e-5)]  # 恒定注入流量 1e-5 m3/s
    )
    # 设置最大时间步长为1周
    tfc.set_dt_max(model, 3600 * 24 * 7)
    return model, fractures


def show(model: Seepage, jx: int, jy: int, fractures=None):
    """
    在界面上显示模型的状态（压力和饱和度云图），
    并叠加离散裂缝网络显示。

    Args:
        model: 渗流模型对象
        jx: x方向的网格单元数量
        jy: y方向的网格单元数量
        fractures: 离散裂缝网络线段列表。若不为None，则在图上叠加绘制裂缝
    """
    x = tfc.get_x(model, shape=(jx, jy))
    y = tfc.get_y(model, shape=(jx, jy))
    p = tfc.get_p(model, shape=(jx, jy))
    s = tfc.get_v(model, 1, shape=(jx, jy)) / tfc.get_v(model, None, shape=(jx, jy))

    def f(figure):
        # 两列并排显示：压力云图和饱和度云图，均叠加DFN
        layout = AutoLayout(figure, num_plots=2, subplot_aspect_ratio=1, aspect='equal', xlabel='x/m', ylabel='y/m')
        ax = layout.add_axes2(title='Pressure')
        add_contourf(ax, x, y, p, cbar=dict(label='Pressure', shrink=0.7))
        if fractures is not None:
            add_dfn2(ax, fractures, linewidth=1)  # 绘制DFN裂缝线
        ax = layout.add_axes2(title='Saturation')
        add_contourf(ax, x, y, s, cbar=dict(label='Saturation', shrink=0.7), cmap='coolwarm')
        if fractures is not None:
            add_dfn2(ax, fractures, linewidth=1)
        figure.tight_layout()

    plot(f, caption='模型状态')


def wat_disp_oil():
    """
    主函数：创建60x60网格的含DFN水驱油模型（初始纯油），
    模拟100天的驱替过程。网格精度比无DFN版本更高以捕捉裂缝细节。
    """
    jx, jy = 60, 60
    model, fractures = create(jx, jy, s=(1, 0), fid_inj=1)
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy, fractures), time_forward=100 * 24 * 3600)


if __name__ == '__main__':
    gui.execute(wat_disp_oil, close_after_done=False)
