"""
处理FractureNetwork以及相应的Seepage模型。包括创建，显示等基本的操作。
"""
from zmlx.alg.base import clamp
from zmlx.base.frac import get_fn2
from zmlx.base.zml import Seepage, FractureNetwork, SeepageMesh, Coord3, Array3
from zmlx.config.seepage import create as create_seepage, as_numpy, get_time, get_time_str
from zmlx.geometry.dfn2 import get_avg_length as get_dfn2_avg_length
from zmlx.plt.fig2 import show_fn2
from zmlx.plt.rc3 import show_rc3


def create_network(
        fractures, *, l_ave=None, height=50.0, data=None):
    """
    根据给定的离散网络数据，创建裂缝网络模型。
        fractures的每一个元素代表一个裂缝，且裂缝fracture是一个长度为4的list，
        格式为 x0  y0  x1  y1.
    """

    assert len(fractures) > 0, 'There is no fracture.'

    if l_ave is None:
        l_ave = get_dfn2_avg_length(fractures) / 5.0
        print(f'Warning, l_ave not given, use l_ave: {l_ave}')

    if data is None:
        data = FractureNetwork.FractureData.create(
            h=height, dn=0, ds=0, f=0.9, p0=1e6, k=0.0)
    else:
        assert isinstance(data, FractureNetwork.FractureData)

    network = FractureNetwork()

    for fracture in fractures:
        assert len(fracture) == 4
        network.add_fracture(pos=fracture, lave=l_ave, data=data)

    return network  # 返回生成的裂缝网络


def create_mesh(
        network: FractureNetwork, *, coord=None, height=None, thick=None,
        l_min=None, l_max=None) -> SeepageMesh:
    """根据裂缝网络创建渗流网格(单层的渗流网络)。

    Args:
        network (FractureNetwork): 裂缝网络对象
        coord: network所在的坐标体系
        height: 裂缝区域的高度(默认值为None，此时高度为1)
        thick: 裂缝区域的厚度(默认值为None，此时厚度为1)
        l_min: 允许的最小的长度(默认值为None，此时长度为lave/2)
        l_max: 允许的最大的长度(默认值为None，此时长度为lave*2)

    Returns:
        SeepageMesh: 生成的渗流网格对象
    """
    mesh = SeepageMesh()
    if network.fracture_number == 0:  # 没有裂缝，直接返回空网格
        return mesh

    # 计算单元长度的平均值
    if l_min is None or l_max is None:
        lave = 0.0
        for fracture in network.fractures:  # 添加单元
            assert isinstance(fracture, FractureNetwork.Fracture)
            length = fracture.length
            assert length > 0, (f'Fracture length must > 0 '
                                f'but got {length}')
            lave += length
        lave /= network.fracture_number
        # 计算允许的最大的长度和最小的长度(限制在一定的范围内，从而保证计算的稳定性)
        l_max = lave * 2.0
        l_min = lave / 2.0
    else:
        assert 0 < l_min <= l_max, (f'l_min must in (0, l_max] but '
                                    f'got l_min={l_min}, l_max={l_max}')

    if height is None:
        height = 1.0
    else:
        assert height > 0, f'Fracture height must > 0 but got {height}'

    if thick is None:
        thick = 1.0
    else:
        assert thick > 0, f'Fracture thickness must > 0 but got {thick}'

    # 全局坐标系(在全局坐标系下创建Mesh)
    global_coord = Coord3()

    for fracture in network.fractures:  # 添加Cell
        assert isinstance(fracture, FractureNetwork.Fracture)
        cell = mesh.add_cell()
        x, y = fracture.center
        z = 0.0
        if coord is not None:
            assert isinstance(coord, Coord3)
            pos = global_coord.view(coord, Array3.from_list([x, y, z]))
            assert isinstance(pos, Array3)
            pos = pos.to_list()
        else:
            pos = [x, y, z]
        cell.pos = pos  # 三维坐标
        length = clamp(fracture.length, l_min, l_max)
        cell.vol = length * height * thick

    for vertex in network.vertexes:  # 添加Face
        assert isinstance(vertex, FractureNetwork.Vertex)
        for i0 in range(vertex.fracture_number):
            f0 = vertex.get_fracture(i0)
            assert isinstance(f0, FractureNetwork.Fracture)
            for i1 in range(i0 + 1, vertex.fracture_number):
                f1 = vertex.get_fracture(i1)
                assert isinstance(f1, FractureNetwork.Fracture)
                face = mesh.add_face(
                    f0.index,
                    f1.index
                )
                dist = clamp((f0.length + f1.length) / 2.0, l_min, l_max)
                face.dist = dist
                face.area = height * thick

    # 返回创建的网格
    return mesh


def create_flow(
        network: FractureNetwork, *,
        fludefs,
        s,
        mesh_opts=None,
        **opts) -> Seepage:
    """
    根据固体的裂缝网络，创建对应的流体系统模型（三维的网络，在z方向有多层）.
    这里，将主要依赖seepage模块来完成.
    这样做的好处，从而确保生成的模型
    满足直接在seepage中iterate的要求。
    """
    if mesh_opts is None:
        mesh_opts = {}

    # 创建渗流的网格
    mesh = create_mesh(network, **mesh_opts)

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

    return create_seepage(
        mesh=mesh,
        fludefs=fludefs,
        s=s,
        **opts
    )


def show_ds(network, **opts):
    """
    二维绘图。其中颜色代表ds的值.
    这里，opts是传递给绘图内核show_fn2函数的参数
    """
    pos, w, c = get_fn2(network, key=-1)
    default_opts = dict(
        cbar=dict(label='The shear [m]'),
        caption='The Ds',
        w_min=1,
        w_max=5)
    opts = {**default_opts, **opts}
    show_fn2(pos=pos, w=w, c=c, **opts)


def show_dn(network, **opts):
    """
    二维绘图。其中颜色代表dn的值.
    这里，opts是传递给绘图内核show_fn2函数的参数
    """
    pos, w, c = get_fn2(network, key=-2)
    default_opts = dict(
        cbar=dict(label='The normal [m]'),
        caption='The Dn',
        w_min=1,
        w_max=5)
    opts = {**default_opts, **opts}
    show_fn2(pos=pos, w=w, c=c, **opts)


def show_pressure(
        network: FractureNetwork, flow: Seepage,
        **opts):
    """
    二维绘图。其中颜色代表流体压力的值.
    这里，opts是传递给绘图内核show_fn2函数的参数
    """
    assert network.fracture_number == flow.cell_number, \
        'The number of fractures is not equal to the number of cells.'
    pos, w, c = get_fn2(network)
    c = as_numpy(flow).cells.pre / 1e6
    default_opts = dict(
        cbar=dict(label='The Pressure [MPa]'),
        caption='The Pressure',
        title=f'Time = {get_time(flow, as_str=True)}',
        w_min=1,
        w_max=5)
    opts = {**default_opts, **opts}
    show_fn2(pos=pos, w=w, c=c, **opts)


def show_pressure3(network: FractureNetwork, flow: Seepage, zr=None, **opts):
    """
    二维绘图。其中颜色代表流体压力的值.
    这里，opts是传递给绘图内核show_fn2函数的参数
    """
    assert network.fracture_number == flow.cell_number, \
        'The number of fractures is not equal to the number of cells.'

    if zr is None:
        zr = [-0.5, 0.5]
    else:
        assert len(zr) == 2, 'zr must be a list of two elements.'

    z0, z1 = zr
    rc3 = []
    for fracture in network.fractures:
        assert isinstance(fracture, FractureNetwork.Fracture)
        x0, y0 = fracture.get_vertex(0).pos
        x1, y1 = fracture.get_vertex(1).pos
        cent = [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]
        p0 = [x0, y0, (z0 + z1) / 2]
        p1 = [(x0 + x1) / 2, (y0 + y1) / 2, z1]
        rc3.append([*cent, *p0, *p1])

    default_opts = dict(
        cbar=dict(label='Pressure [MPa]',
                  shrink=0.5),
        caption='Pressure',
        title=f'Time = {get_time_str(flow)}',
        edge_width=0
    )
    opts = {**default_opts, **opts}
    p = as_numpy(flow).cells.pre / 1e6
    show_rc3(rc3, face_color=p, **opts)


def test(show3d=True):
    from zmlx.fluid.ch4 import create as create_ch4
    from zmlx.config.seepage import solve
    from zmlx.geometry.dfn2 import dfn2
    import math

    l_ave = 3.0
    fractures = dfn2(
        xr=[-40, 40], yr=[-40, 40], p21=0.3, l_min=2, lr=[10, 60],
        ar=[0, math.pi * 2]
    )

    network = create_network(fractures=fractures, l_ave=l_ave)
    flow = create_flow(
        network=network,
        fludefs=[create_ch4(name='ch4')],
        s=dict(ch4=1.0),
        p=10e6,
        perm=1.0e-12,
        dt_max=10.0,
        mesh_opts=dict(
            thick=0.01, height=30,
        ),
        injectors=[dict(
            pos=[0, 0, 0],
            fluid_id=0,
            flu='insitu',
            value=10.0 / 60)
        ],
    )

    def show():
        if show3d:
            show_pressure3(
                network, flow, zr=[-3, 3], edge_width=0.5
            )
        else:
            show_pressure(network, flow, w_min=2)

    solve(flow, close_after_done=False,
          extra_plot=show,
          time_forward=6000)


if __name__ == '__main__':
    test(show3d=True)
