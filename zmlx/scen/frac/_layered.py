"""
管理分层模型
"""
from typing import List, Optional, Union, Set, Tuple, Dict, Any

from zmlx.exts import Seepage, np, FractureNetwork, SeepageMesh
from zmlx.scen.frac._base import create_network
from zmlx.scen.frac._topo import get_topo
from zmlx.scen.frac._traj import get_cells_along
from zmlx.tfc import seepage
from zmlx.tfc.groups import create_virtual_groups, iterate as iterate_groups


def _create_layer(
        *, vx, vy, layer_z, thick, s, dt_max=3600.0, perm=1.0e-14, bound_open=True,
        flu_defs: Optional[List[Seepage.FluDef]] = None
) -> Seepage:
    """
    创建模型的水平一层.
    Args:
        perm: 渗透率. 默认值为1e-15
        layer_z: 层的z坐标
        dt_max: 最大时间步长. 默认值为3600秒
        vx: 模型的x方向的单元格数量
        vy: 模型的y方向的单元格数量
        s: 初始饱和度. 默认值为(1, 0)
        thick: 层的厚度
        bound_open: 是否将四周设置为流体的开放边界. 默认值为True
        flu_defs: 流体定义. 默认值为[Seepage.FluDef].water, Seepage.FluDef].oil

    Returns:
        model: 模型对象
    """
    from zmlx.seepage_mesh import create_cube

    assert np is not None, "numpy is not installed"
    mesh = create_cube(
        vx,
        vy, (layer_z - thick / 2, layer_z + thick / 2)
    )

    x0, x1 = mesh.get_pos_range(0)
    y0, y1 = mesh.get_pos_range(1)

    if bound_open:
        for cell in mesh.cells:  # 将四周设置为流体的开放边界
            x, y, z = cell.pos
            if abs(y - y1) < 0.1 or abs(x - x1) < 0.1 or abs(x - x0) < 0.1 or abs(y - y0) < 0.1:
                cell.vol *= 1.0e8

    # 定义流体
    if flu_defs is None:
        flu_defs = [
            Seepage.FluDef(den=1000, vis=1.0e-3, name='water'),
            Seepage.FluDef(den=50, vis=1.0e-2, name='oil'),
        ]

    assert flu_defs is not None, "flu_defs is None"

    if s is None:
        s = dict(water=1, oil=0)

    # 创建模型
    model = seepage.create(
        mesh,
        porosity=0.02,  # 在压裂的过程中，能够影响到的孔隙率
        pore_modulus=100e6,
        p=1e6, temperature=280,
        s=s,
        perm=perm,
        disable_update_den=True,
        disable_update_vis=True,
        disable_ther=True,
        disable_heat_exchange=True,
        fludefs=flu_defs
    )
    # 最大时间步长
    seepage.set_dt_max(model, dt_max)
    # 检查时间步长
    model.add_tag('check_dt')
    return model


def _get_virtual_network(
        network: FractureNetwork,
        layer: Union[Seepage, SeepageMesh]
):
    """
    返回裂缝网络(network)经过的所有Cell的索引，以及由这些Cells构成的网络.
    Args:
        network:裂缝网络
        layer:模型对象(平行于x-y平面的模型)

    Returns:
        cells: 虚拟网络所有涉及的Cell的索引
        links: 基于这些cells所构建网络的link(返回的cells中的元素的索引)
    """
    v_tips, v_fids = get_topo(network)
    if v_tips is None or v_fids is None:
        return None, None

    # 虚拟网络所有涉及的Cell的索引
    tip_cells: Set[int] = set()

    vertex_n = network.vertex_number
    for tips in v_tips:
        assert len(tips) == 2
        for i in tips:
            assert 0 <= i < vertex_n
            v = network.get_vertex(i)
            assert v is not None
            x, y = v.pos
            c = layer.get_nearest_cell(pos=[x, y, None])
            assert c is not None
            tip_cells.add(c.index)

    all_links: Set[Tuple[int, int]] = set()

    assert len(v_fids) == len(v_tips)
    for index in range(len(v_fids)):
        fids = v_fids[index]
        assert len(fids) > 0  # 这里是所有相关的裂缝，但是，是无序的，下面，需要构建出按照顺序的裂缝轨迹
        i0, i1 = v_tips[index]
        assert i0 != i1
        all_vertexes: Set[int] = set()
        for fid in fids:
            f = network.get_fracture(fid)
            assert f is not None
            for v in f.vertexes:
                assert v is not None
                all_vertexes.add(v.index)
        assert i0 in all_vertexes
        assert i1 in all_vertexes
        # 下面，需要对这些Vertex排序
        vertex_list: List[int] = [i0]
        idx = 0
        while idx < len(vertex_list):
            v = network.get_vertex(vertex_list[idx])
            idx += 1
            assert v is not None
            found = False
            for v2 in v.vertexes:
                if v2.index in all_vertexes and v2.index not in vertex_list:
                    vertex_list.append(v2.index)
                    found = True
                    break
            if not found:
                break
        assert i0 == vertex_list[0] and i1 == vertex_list[-1]
        # 现在，可以得到一串有序的坐标
        points = []
        for i in vertex_list:
            v = network.get_vertex(i)
            assert v is not None
            x, y = v.pos
            points.append([x, y, None])

        # 获得沿着这个轨迹的所有的Cell的Index
        cell_ids = get_cells_along(points=points, model=layer)
        assert cell_ids[0] in tip_cells
        assert cell_ids[-1] in tip_cells
        if len(cell_ids) >= 2:
            for i in range(len(cell_ids) - 1):
                i0 = cell_ids[i]
                i1 = cell_ids[i + 1]
                assert i0 != i1
                if i0 < i1:
                    all_links.add((i0, i1))
                else:
                    all_links.add((i1, i0))

    all_cells_set: Set[int] = set()
    for link in all_links:
        for i in link:
            all_cells_set.add(i)

    cells = list(all_cells_set)
    local_cell_ids: Dict[int, int] = dict()
    for i in range(len(cells)):
        local_cell_ids[cells[i]] = i

    links: List[Tuple[int, int]] = []
    for link in all_links:
        links.append((local_cell_ids[link[0]], local_cell_ids[link[1]]))

    return cells, links


def _test_2():
    assert np is not None
    layer = SeepageMesh()
    for x in np.linspace(-10, 10, 30):
        for y in np.linspace(-10, 10, 30):
            c = layer.add_cell()
            c.pos = [x, y, 0]

    network = FractureNetwork()
    network.add_fracture(first=[0, -1], second=[0, 1], lave=0.2)
    network.add_fracture(first=[-1, 0], second=[1, 0], lave=0.2)

    cells, links = _get_virtual_network(network, layer=layer)
    print(cells)
    print(links)
    for i in cells:
        c = layer.get_cell(i)
        assert c is not None
        print(c.pos)


# if __name__ == '__main__':
#     test_2()


def create_fracture_virtual_groups(layers: List[Seepage], fractures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    给定所有的层，以及裂缝，创建虚拟的裂缝分组
    """
    assert isinstance(fractures, list), f'fractures {fractures} is not a list'

    data_list: List[Dict[str, Any]] = []
    for fracture in fractures:
        assert isinstance(fracture, dict), f'fracture {fracture} is not a dict'

        network = fracture.get('network')
        if network is None:
            trajectory = fracture.get('trajectory')
            if isinstance(trajectory, list):
                network = create_network(trajectory)

        if not isinstance(network, FractureNetwork):
            continue

        if network.fracture_number == 0:
            continue

        cell_ids, links = _get_virtual_network(network, layer=layers[0])
        if cell_ids is None or links is None:
            continue

        if len(links) == 0:
            continue

        perm_h = fracture.get('perm_h', 1.0e-9)
        assert isinstance(perm_h, (float, int)), f'perm_h {perm_h} is not a float or int'
        assert perm_h >= 0, f'perm_h {perm_h} is negative'

        perm_v = fracture.get('perm_v', 1.0e-11)
        assert isinstance(perm_v, (float, int)), f'perm_v {perm_v} is not a float or int'
        assert perm_v >= 0, f'perm_v {perm_v} is negative'

        cells = []
        faces = []

        for i0 in range(len(cell_ids)):
            for i1 in range(len(layers)):
                new_i = len(cells)
                cells.append(dict(
                    model_index=i1, cell_index=cell_ids[i0]
                ))
                if i1 > 0:  # 纵向的（跨越了不同的model）
                    faces.append(dict(
                        i0=new_i, i1=new_i - 1, area=1.0, dist=1.0, perm=perm_v, heat_cond=1.0
                    ))

        for i0 in range(len(links)):
            ia, ib = links[i0]
            for i1 in range(len(layers)):
                first = ia * len(layers) + i1
                second = ib * len(layers) + i1
                faces.append(dict(
                    i0=first, i1=second, area=1.0, dist=1.0, perm=perm_h, heat_cond=1.0
                ))

        data_list.append(dict(
            cells=cells, faces=faces, injectors=fracture.get('injectors'),
        ))

    groups: List[Dict[str, Any]] = create_virtual_groups(layers, data_list)
    return groups


def create(
        x0=-75.0, x1=75.0, y0=-200.0, y1=200.0, z0=-15.0, z1=15.0,
        jx=40, jy=60, jz=6,
        dt=10.0,
        fractures: Optional[List[Dict[str, Any]]] = None,
        perm=1.0e-14,
        dfn2_data=None,
        bound_open=True,
) -> Dict[str, Any]:
    """
    创建一个分层模型(包含多个group). 后续，使用tfc.groups的配置向前迭代
    """
    assert np is not None, "numpy is not installed"

    # 创建分层
    layers: List[Seepage] = []
    vx = np.linspace(x0, x1, jx + 1)
    vy = np.linspace(y0, y1, jy + 1)
    vz = np.linspace(z0, z1, jz + 1)

    for i in range(1, len(vz)):  # 创建分层模型
        model = _create_layer(
            vx=vx,
            vy=vy,
            s=dict(water=0.1, oil=0.9),
            layer_z=(vz[i - 1] + vz[i]) / 2, thick=vz[i] - vz[i - 1],
            dt_max=dt,
            perm=perm,
            bound_open=bound_open,
        )
        layers.append(model)

    groups = [{
        'models': layers,
    }]

    if fractures is not None:
        assert isinstance(fractures, list), f'fractures {fractures} is not a list'
        virtual_groups: List[Dict[str, Any]] = create_fracture_virtual_groups(layers, fractures)
        groups.extend(virtual_groups)

    from zmlx.scen.frac._show import _show_p, _show_s
    def _plot():
        _show_s(layers, jx, jy, dfn2_data=dfn2_data)
        _show_p(layers, jx, jy, dfn2_data=dfn2_data)

    return dict(
        time=0.0, dt=dt, groups=groups, show=_plot, time_max=3600 * 3.0, layers=layers
    )


def iterate(space: Dict[str, Any]):
    """
    将模型向前迭代一步。由于实质上一个一个分组模型，因此，直接调用groups的iterate函数
    """
    iterate_groups(space)


def _get_n_loops(groups: List[Dict[str, Any]]) -> List[int]:
    return [group['n_loop'] for group in groups]


def solve(space: Dict[str, Any]):
    """
    求解计算模型
    """
    from zmlx.utility import GuiIterator
    from zmlx.alg import time2str
    gui_it = GuiIterator(iterate=iterate, plot=space['show'])
    groups: List[Dict] = space['groups']

    for step in range(9999999):
        if space['time'] > space['time_max']:
            break
        gui_it(space)
        if step % 50 == 0:
            print(f"step = {step}, time = {time2str(space['time'])}, n_loop = {_get_n_loops(groups)}")

    space['show']()
