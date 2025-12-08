"""
处理三维的矩形裂缝以及相应的Seepage模型
"""
from typing import Optional

from zmlx.alg.base import linspace
from zmlx.base.zml import Seepage, SeepageMesh, Coord3, Array3, get_norm
from zmlx.config.seepage import create as create_seepage, as_numpy, get_time_str
from zmlx.plt.on_axes import item, plot3d
from zmlx.seepage_mesh.cube import create_cube


def create_mesh(rc3, d0: float, d1: float, *, thick: Optional[float] = None):
    """
    在三维矩形区域内，创建一个SeepageMesh网格.

    Args:
        rc3: 三维矩形。格式为[cent_x, cent_y, cent_z, p0_x, p0_y, p0_z, p1_x, p1_y, p1_z].
            其中cent为矩形的中心，p0为矩形一条边的中心，p1为矩形另一条相邻边的中心.
        d0: 方向0的节点距离
        d1: 方向1的节点距离
        thick: 三维矩形的厚度. 如果为None，则默认值为1.0

    Returns:
        tuple: SeepageMesh网格, 以及每个单元的小矩形的偏移量dir0, dir1
    """
    assert len(rc3) == 9
    # 计算矩形所在的局部坐标系
    dir0 = [rc3[3 + i] - rc3[0 + i] for i in range(3)]
    dir1 = [rc3[6 + i] - rc3[0 + i] for i in range(3)]
    local_coord = Coord3(origin=rc3[0:3], xdir=dir0, ydir=dir1)

    # 计算矩形的大小
    l0 = get_norm(dir0) * 2
    l1 = get_norm(dir1) * 2

    # 在局部坐标系，生成网格
    assert d0 > 0 and d1 > 0

    # 计算两个方向的节点的数量
    n0 = max(2, min(100, int(l0 / d0)))
    n1 = max(2, min(100, int(l1 / d1)))

    if thick is None:
        thick = 1.0

    mesh = create_cube(x=linspace(-l0 / 2, l0 / 2, n0), y=linspace(-l1 / 2, l1 / 2, n1), z=[-thick / 2, thick / 2])
    assert isinstance(mesh, SeepageMesh)

    global_coord = Coord3()

    # 修改坐标
    for cell in mesh.cells:
        assert isinstance(cell, SeepageMesh.Cell)
        pos = global_coord.view(local_coord, Array3.from_list(cell.pos))
        cell.pos = pos.to_list()

    # 计算每隔单元的小矩形的偏移量
    offset0 = local_coord.xdir.to_list()
    offset1 = local_coord.ydir.to_list()
    for i in range(3):
        offset0[i] *= (l0 * 0.5 / (n0 - 1))
        offset1[i] *= (l1 * 0.5 / (n1 - 1))

    # 返回Mesh
    return mesh, offset0 + offset1


def create_flow(rc3, d0, d1, *,
                thick=None,
                fludefs=None,
                s=None,
                **opts) -> Seepage:
    """
    根据固体的裂缝网络，创建对应的流体系统模型（三维的网络，在z方向有多层）.
    这里，将主要依赖seepage模块来完成.
    这样做的好处，从而确保生成的模型
    满足直接在seepage中iterate的要求。
    """
    mesh, rc3_offsets = create_mesh(rc3=rc3, d0=d0, d1=d1, thick=thick)
    # 一些默认的参数
    default_opts = dict(
        p=1.0e6,
        temperature=285.0,
        denc=1.0e5,
        pore_modulus=100e6,
        porosity=1.0,
        dt_min=1.0e-3,
        dt_max=24.0 * 3600.0,
        dv_relative=0.2,
        perm=1.0e-14,
        tags=['disable_ther', 'disable_heat_exchange']
    )
    opts = {**default_opts, **opts}

    model = create_seepage(
        mesh=mesh,
        fludefs=fludefs,
        s=s,
        **opts
    )
    assert isinstance(model, Seepage)
    model.set_text('rc3_offsets', f'{rc3_offsets}')
    model.set_text('rc3', f'{rc3}')

    return model


def show_pressure3(model: Seepage, **opts):
    """
    二维绘图。其中颜色代表流体压力的值.
    这里，opts是传递给绘图内核show_fn2函数的参数
    """
    rc3_offsets = eval(model.get_text('rc3_offsets'))
    dx = rc3_offsets[0: 3]
    dy = rc3_offsets[3: 6]

    rc3 = []
    for cell in model.cells:
        cent = cell.pos
        p0 = [cent[i] + dx[i] for i in range(3)]
        p1 = [cent[i] + dy[i] for i in range(3)]
        rc3.append([*cent, *p0, *p1])

    default_opts = dict(
        cbar=dict(label='Pressure [MPa]', shrink=0.5),
        caption='Pressure',
        title=f'Time = {get_time_str(model)}',
        edge_width=0,
        face_alpha=0.7
    )
    opts = {**default_opts, **opts}
    p = as_numpy(model).cells.pre / 1e6

    items = [item('rc3', rc3, face_color=p, **opts)]
    text = model.get_text('rc3')
    if len(text) > 0:
        items.append(item('rc3', [eval(text)], edge_only=True, edge_width=0.5, edge_color='red'))

    plot3d(*items, aspect='equal', tight_layout=True,
           xlabel='x/m', ylabel='y/m', zlabel='z/m',
           )


def test_2():
    from zmlx.fluid.ch4 import create as create_ch4
    from zmlx.config.seepage import solve

    rc3 = [0, 0, 0, 20, 20, 0, -5, 5, 5]
    model = create_flow(
        rc3=rc3, d0=2, d1=1.2, thick=1,
        fludefs=[create_ch4(name='ch4')],
        s=dict(ch4=1.0),
        p=10e6,
        perm=1.0e-12,
        dt_max=10.0,
        injectors=[dict(
            pos=[0, 0, 0],
            fluid_id=0,
            flu='insitu',
            value=10.0 / 60)
        ],
    )

    solve(model, close_after_done=False,
          extra_plot=lambda: show_pressure3(model),
          time_forward=6000)


if __name__ == '__main__':
    test_2()
