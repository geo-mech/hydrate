"""
创建二维的有限元模型
"""

from zml import Mesh3, DynSys, LinearExpr
from zmlx.fem.attr_getter import attr_getter
from zmlx.fem.stiff2 import stiff2


def create2(mesh, fa_E=None, fa_mu=None, fa_den=None, fa_h=None,
            f_E=1.0, f_mu=0.2, f_den=1.0, f_h=1.0):
    """
    创建二维的动力学模型。 其中mesh为网格.

    对于face：
        fa_E为杨氏模量属性，fa_mu为泊松比属性，fa_den为密度属性(kg/m^3), fa_h为厚度属性.
        f_E为默认的杨氏模量, f_mu为默认的泊松比，f_den为默认的密度，f_h为默认的厚度(默认为1).

    注意：
        1、对于mesh中所有的node的位置，将仅使用x和y坐标，因此务必保证mesh是二维的；
        2、仅支持三角形网格和四边形网格（以及两者混合的网格）；

    返回：
        DynSys对象，其中的自由度的数量是mesh中node数量的二倍.
    """
    assert isinstance(mesh, Mesh3)

    # 生成face属性的接口函数.
    assert 1.0e-6 <= f_E <= 1.0e20
    get_f_E = attr_getter(index=fa_E, left=1.0e-6, right=1.0e20, default=f_E)
    assert 0.01 <= f_mu <= 0.49
    get_f_mu = attr_getter(index=fa_mu, left=0.01, right=0.49, default=f_mu)
    assert 1.0e-8 <= f_den <= 1.0e8
    get_f_den = attr_getter(index=fa_den, left=1.0e-8, right=1.0e8, default=f_den)
    assert 0.0 <= f_h <= 1.0e20
    get_f_h = attr_getter(index=fa_h, left=0.0, right=1.0e20, default=f_h)

    # 维度
    ndim = 2

    # 设置动力学模型
    model = DynSys()
    model.size = mesh.node_number * ndim
    for node_id in range(mesh.node_number):
        node = mesh.get_node(node_id)
        assert isinstance(node, Mesh3.Node)
        i0 = node_id * ndim
        i1 = i0 + 1
        # 节点位置
        x, y, z = node.pos
        model.set_pos(i0, x)
        model.set_pos(i1, y)
        # 节点速度
        model.set_vel(i0, 0)
        model.set_vel(i1, 0)

    # 节点质量
    vm = [0, ] * mesh.node_number
    for face in mesh.faces:  # face的质量
        assert isinstance(face, Mesh3.Face)
        m = face.area * get_f_h(face) * get_f_den(face) / face.node_number
        if 0 < m:
            for node in face.nodes:
                assert isinstance(node, Mesh3.Node)
                vm[node.index] += m
    for node_id in range(mesh.node_number):
        assert 0 < vm[node_id]
        i0 = node_id * ndim
        i1 = i0 + 1
        model.set_mass(i0, vm[node_id])
        model.set_mass(i1, vm[node_id])

    # 修改系数(相当于组刚度矩阵)
    for index in range(model.size):  # 首先初始化
        p2f = model.get_p2f(index)
        p2f.clear()
        p2f.c = 0.0
    # 添加系数(from face)
    for face_id in range(mesh.face_number):
        # 生成这个face的单元刚度矩阵
        face = mesh.get_face(face_id)
        assert isinstance(face, Mesh3.Face)
        h = get_f_h(face)
        if h <= 1.0e-30:
            continue
        stiff = stiff2(face, E=get_f_E(face), mu=get_f_mu(face), h=h)
        # 修改总刚
        for i0 in range(face.node_number):
            node_i0 = face.get_node(i0).index  # 需要操作的行
            for i1 in range(face.node_number):
                node_i1 = face.get_node(i1).index  # 影响变量
                for ia in range(ndim):
                    for ib in range(ndim):
                        expr = model.get_p2f(node_i0 * ndim + ia)
                        assert isinstance(expr, LinearExpr)
                        k = -stiff[i0 * ndim + ia, i1 * ndim + ib]
                        expr.c = expr.c - k * model.get_pos(node_i1 * ndim + ib)
                        expr.add(index=node_i1 * ndim + ib, weight=k)

    # 完成，返回model
    return model
