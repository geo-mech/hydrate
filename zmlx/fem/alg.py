import warnings

import numpy as np

from zml import DynSys, Mesh3, ConjugateGradientSolver
from zmlx.fem.create3 import create3
from zmlx.geometry.point_distance import point_distance as get_distance


def set_mas(dyn: DynSys, ids, mas):
    """
    批量设置给定自由度的质量
    -- 2023.12.6
    """
    size = dyn.size
    for i in ids:
        if i < size:
            dyn.set_mas(i, mas)


def find_boundary(dyn: DynSys, n_dim, i_dim, lower, i_dir, eps=None):
    """
    找到边界自由度的序号(作为list返回).
        n_dim: 模型的总维度 (1, 2, 3)
        i_dim: 目标边界的维度 (0, 1, 2)
        lower: 在目标维度下，是查找左侧边界(lower)还是右侧边界
        i_dir: 在目标边界上，取哪个方向的自由度
    -- 2023.12.6
    """
    assert n_dim == 1 or n_dim == 2 or n_dim == 3
    assert i_dim == 0 or i_dim == 1 or i_dim == 2
    assert i_dir == 0 or i_dir == 1 or i_dir == 2
    assert i_dim < n_dim
    assert i_dir < n_dim

    size = dyn.size

    pos = 1.0e100 if lower else -1.0e100
    idx = i_dim
    while idx < size:
        pos = min(pos, dyn.get_pos(idx)) if lower else max(pos, dyn.get_pos(idx))
        idx += n_dim

    if eps is None:
        eps = 1.0e-6

    ids = []
    idx = i_dim
    while idx < size:
        if abs(pos - dyn.get_pos(idx)) <= eps:
            ids.append(idx + (i_dir - i_dim))
        idx += n_dim

    return ids


def _test1():
    """
    测试find_boundary
    """
    mesh = Mesh3.create_cube(x1=-1, y1=-1, z1=-1,
                             x2=+1, y2=+1, z2=+1,
                             dx=2, dy=2, dz=2)
    print(mesh)

    dyn = create3(mesh)

    print(find_boundary(dyn, n_dim=3, i_dim=0, lower=1, i_dir=0))
    print(find_boundary(dyn, n_dim=3, i_dim=0, lower=1, i_dir=1))
    print(find_boundary(dyn, n_dim=3, i_dim=0, lower=1, i_dir=2))

    print(find_boundary(dyn, n_dim=3, i_dim=0, lower=0, i_dir=0))
    print(find_boundary(dyn, n_dim=3, i_dim=0, lower=0, i_dir=1))
    print(find_boundary(dyn, n_dim=3, i_dim=0, lower=0, i_dir=2))


def add_node_force(dyn: DynSys, node_id, force):
    """
    添加一个节点力. 必须确保给定的force的维度和dyn的维度是一致的
    -- 2023.12.6
    """
    n_dim = len(force)
    assert 1 <= n_dim <= 3
    for i in range(n_dim):
        idx = node_id * n_dim + i
        p2f = dyn.get_p2f(idx)
        p2f.c = p2f.c + force[i]


def add_face_force(dyn: DynSys, mesh: Mesh3, face_id, force):
    """
    添加面力. (将力平分到各个node)
    -- 2023.12.6
    """
    assert face_id < mesh.face_number

    face = mesh.get_face(face_id)
    assert isinstance(face, Mesh3.Face)

    force = [f / face.node_number for f in force]

    for node in face.nodes:
        assert isinstance(node, Mesh3.Node)
        add_node_force(dyn, node.index, force)


def add_body_force(dyn: DynSys, mesh: Mesh3, body_id, force):
    """
    添加体力. (将体力平分到各个node)
    -- 2023.12.6
    """
    assert body_id < mesh.body_number
    assert len(force) == 3

    body = mesh.get_body(body_id)
    assert isinstance(body, Mesh3.Body)

    force = [f / body.node_number for f in force]

    for node in body.nodes:
        assert isinstance(node, Mesh3.Node)
        add_node_force(dyn, node.index, force)


def add_body_pressure(dyn: DynSys, mesh: Mesh3, body_id, pressure):
    """
    添加body的压力
        todo:
            直接根据body和face的中心来计算力的方向，对于不规则的网格，其实是不准确的；力的方向，应该用face的外法线
    -- 2023.12.6
    """
    assert body_id < mesh.body_number

    body = mesh.get_body(body_id)
    assert isinstance(body, Mesh3.Body)
    cent = body.pos

    for face in body.faces:
        assert isinstance(face, Mesh3.Face)
        p2 = face.pos
        dire = [p2[i] - cent[i] for i in range(len(p2))]
        norm = np.linalg.norm(dire)
        if norm < 1.0e-20:
            continue
        dire = [item / norm for item in dire]
        temp = pressure * face.area
        force = [item * temp for item in dire]
        add_face_force(dyn, mesh, face.index, force)


def compute_disp(mesh: Mesh3, na_dx=None, na_dy=None, na_dz=None, ba_dd=None, ba_dp=None,
                 ba_E0=None, ba_E1=None, ba_mu=None, gravity=-10.0, dt=1.0e3,
                 top_stress=None, top_pressure=None,
                 tolerance=1.0e-20, show=print, bound_mas=1.0e20, bound_sym=True):
    """
    计算各个Node的位移，并且存储在Node属性里面. 其中：
        na_dx, na_dy和na_dz为Node的属性，用来存储计算的结果（各个Node的位移）;
        ba_dd: body的属性，表示密度的变化(density1 - density0);
        ba_dp: body的属性，表示流体压力的变化 (pressure1 - pressure0);
        ba_E0: body的属性，弹性模量
        ba_E1: body的属性，弹性模量(强度降低了之后)
        ba_mu: body的属性，泊松比;
        gravity: 重力加速度
        dt: 计算的时间步长.
        top_stress/top_pressure：模型计算区域顶部的应力(将作用在mesh顶部的一层face上面)
        tolerance: 求解器的残差.
        show: 用以显示计算的过程.
    计算的边界条件为:
        如果bound_sym：
            x的左右侧，均仅仅限制x位移；y的左右侧，都限制y位移；z的底部，限制z的位移.
        否则：
            四周固定；z的底部，限制z的位移.
    """

    def set_bound(_dyn):
        """
        设置边界条件
        """
        # x
        set_mas(_dyn, find_boundary(_dyn, n_dim=3, i_dim=0, lower=1, i_dir=0, eps=1.0e-3), bound_mas)
        set_mas(_dyn, find_boundary(_dyn, n_dim=3, i_dim=0, lower=0, i_dir=0, eps=1.0e-3), bound_mas)
        if not bound_sym:
            set_mas(_dyn, find_boundary(_dyn, n_dim=3, i_dim=0, lower=1, i_dir=1, eps=1.0e-3), bound_mas)
            set_mas(_dyn, find_boundary(_dyn, n_dim=3, i_dim=0, lower=0, i_dir=1, eps=1.0e-3), bound_mas)
            set_mas(_dyn, find_boundary(_dyn, n_dim=3, i_dim=0, lower=1, i_dir=2, eps=1.0e-3), bound_mas)
            set_mas(_dyn, find_boundary(_dyn, n_dim=3, i_dim=0, lower=0, i_dir=2, eps=1.0e-3), bound_mas)
        # y
        set_mas(_dyn, find_boundary(_dyn, n_dim=3, i_dim=1, lower=1, i_dir=1, eps=1.0e-3), bound_mas)
        set_mas(_dyn, find_boundary(_dyn, n_dim=3, i_dim=1, lower=0, i_dir=1, eps=1.0e-3), bound_mas)
        if not bound_sym:
            set_mas(_dyn, find_boundary(_dyn, n_dim=3, i_dim=1, lower=1, i_dir=0, eps=1.0e-3), bound_mas)
            set_mas(_dyn, find_boundary(_dyn, n_dim=3, i_dim=1, lower=0, i_dir=0, eps=1.0e-3), bound_mas)
            set_mas(_dyn, find_boundary(_dyn, n_dim=3, i_dim=1, lower=1, i_dir=2, eps=1.0e-3), bound_mas)
            set_mas(_dyn, find_boundary(_dyn, n_dim=3, i_dim=1, lower=0, i_dir=2, eps=1.0e-3), bound_mas)
        # z
        set_mas(_dyn, find_boundary(_dyn, n_dim=3, i_dim=2, lower=1, i_dir=2, eps=1.0e-3), bound_mas)

    assert na_dx is not None and na_dy is not None and na_dz is not None
    for node in mesh.nodes:
        node.set_attr(na_dx, 0.0)
        node.set_attr(na_dy, 0.0)
        node.set_attr(na_dz, 0.0)
    show('disp inited')

    solver = ConjugateGradientSolver(tolerance=tolerance)
    show('solver created')

    if top_stress is None and top_pressure is not None:
        top_stress = top_pressure
        warnings.warn('The keyword <top_pressure> will not be used, use <top_stress> instead',
                      DeprecationWarning)

    if top_stress is not None and ba_E0 is not None and ba_E1 is not None:
        show('E0, E1 and top_pressure set, will computed disp by the changed of E')
        assert top_stress >= 0
        # 计算z的最大值 (用以寻找顶面)
        z_max = -1.0e100
        for node in mesh.nodes:
            assert isinstance(node, Mesh3.Node)
            z_max = max(z_max, node.pos[2])
        show(f'z_max = {z_max}')

        top_faces = []
        for face in mesh.faces:
            assert isinstance(face, Mesh3.Face)
            is_top = True
            for node in face.nodes:
                assert isinstance(node, Mesh3.Node)
                if abs(node.pos[2] - z_max) > 1.0e-3:
                    is_top = False
                    break
            if is_top:
                top_faces.append(face)
        show(f'count of top face: {len(top_faces)}')
        assert len(top_faces) > 0

        def add_top_pressure(_dyn):
            for face in top_faces:
                add_face_force(_dyn, mesh, face.index, [0, 0, -top_stress * face.area])

        # 计算在原始状态下的位移
        dyn = create3(mesh=mesh, ba_E=ba_E0, ba_mu=ba_mu, ba_den=None, b_E=200e6, b_mu=0.2, b_den=2000.0)
        set_bound(dyn)
        add_top_pressure(dyn)

        dyn.iterate(dt, solver)
        pos0 = [dyn.get_pos(i) for i in range(dyn.size)]
        show('pos0 computed (under E0)')

        # 计算刚度折减之后的位移
        dyn = create3(mesh=mesh, ba_E=ba_E1, ba_mu=ba_mu, ba_den=None, b_E=200e6, b_mu=0.2, b_den=2000.0)
        set_bound(dyn)
        add_top_pressure(dyn)

        dyn.iterate(dt, solver)
        pos1 = [dyn.get_pos(i) for i in range(dyn.size)]
        show('pos1 computed (under E1)')

        # 记录位移
        attr_ids = [na_dx, na_dy, na_dz]
        for node in mesh.nodes:
            assert isinstance(node, Mesh3.Node)
            for i in range(3):
                idx = node.index * 3 + i
                node.set_attr(attr_ids[i], node.get_attr(attr_ids[i]) + pos1[idx] - pos0[idx])
        show('Disp by dE obtained')

    if ba_E1 is not None and (ba_dp is not None or ba_dd is not None):
        show('Will compute the disp by dp and dd')

        dyn = create3(mesh=mesh, ba_E=ba_E1, ba_mu=ba_mu, ba_den=None, b_E=200e6, b_mu=0.2, b_den=2000.0)
        show(f'dyn created: {dyn}')

        set_bound(dyn)
        show('boundary set')

        # 添加压力
        if ba_dp is not None:
            for body in mesh.bodies:
                assert isinstance(body, Mesh3.Body)
                dp = body.get_attr(ba_dp)
                if dp is not None:
                    add_body_pressure(dyn, mesh, body.index, dp)
            show('dp added')

        # 添加重力的改变
        if ba_dd is not None:
            for body in mesh.bodies:
                assert isinstance(body, Mesh3.Body)
                dd = body.get_attr(ba_dd)
                if dd is not None:
                    add_body_force(dyn, mesh, body.index, [0, 0, gravity * dd])
            show('dd added')

        # 计算
        dyn.iterate(dt, solver)
        show('solved')

        # 存储位移 (这里，计算得到了由于压力改变和由于自重改变所带来的位移)
        attr_ids = [na_dx, na_dy, na_dz]
        for node in mesh.nodes:
            assert isinstance(node, Mesh3.Node)
            for i in range(3):
                idx = node.index * 3 + i
                node.set_attr(attr_ids[i], node.get_attr(attr_ids[i]) + dyn.get_pos(idx) - node.pos[i])
        show('disp by dp and dd added')

    show('Add done')


def _test2():
    mesh = Mesh3.create_cube(x1=-10, y1=-10, z1=-10,
                             x2=+10, y2=+10, z2=+10,
                             dx=2, dy=2, dz=2)
    print(mesh)

    ba_dd = 0
    ba_dp = 1
    ba_E0 = 2
    ba_E1 = 3
    ba_mu = 4

    # 设置属性
    for body in mesh.bodies:
        assert isinstance(body, Mesh3.Body)
        body.set_attr(ba_dd, 100 if get_distance(body.pos, [0, 0, 0]) < 5 else 0)
        body.set_attr(ba_dp, 0)
        body.set_attr(ba_E0, 200e6)
        body.set_attr(ba_E1, 200e6)
        body.set_attr(ba_mu, 0.2)
    print('Attrs set')

    na_dx = 0
    na_dy = 1
    na_dz = 2
    compute_disp(mesh, na_dx=na_dx, na_dy=na_dy, na_dz=na_dz, ba_dd=ba_dd, ba_dp=ba_dp,
                 ba_E0=ba_E0, ba_E1=ba_E1, ba_mu=ba_mu, top_stress=1e6)

    # 读取中间一个切面，并且绘图
    x = []
    z = []
    v = []
    for node in mesh.nodes:
        assert isinstance(node, Mesh3.Node)
        if abs(node.pos[1] - 0) < 2:
            x.append(node.pos[0])
            z.append(node.pos[2])
            v.append(node.get_attr(2))
    print(x)
    from zmlx.plt.tricontourf import tricontourf
    tricontourf(x, z, v)


if __name__ == '__main__':
    _test2()
