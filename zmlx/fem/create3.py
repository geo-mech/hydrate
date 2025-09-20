"""
创建3维的有限元模型
"""

from zmlx.exts.base import Mesh3, DynSys, LinearExpr
from zmlx.fem.attr_getter import attr_getter
from zmlx.fem.stiff3 import stiff3


def create3(mesh, ba_E=None, ba_mu=None, ba_den=None, b_E=1.0, b_mu=0.2,
            b_den=1.0):
    """
    创建3维的动力学模型。 其中mesh为网格.

    对于body：
        ba_E为杨氏模量属性，ba_mu为泊松比属性，ba_den为密度属性(kg/m^3).
        b_E为默认的杨氏模量, b_mu为默认的泊松比，b_den为默认的密度.

    返回：
        DynSys对象，其中的自由度的数量是mesh中node数量的二倍.
    """
    assert isinstance(mesh, Mesh3)

    # 生成body属性的接口函数.
    assert 1.0e-6 <= b_E <= 1.0e20
    get_b_E = attr_getter(index=ba_E, left=1.0e-6, right=1.0e20, default=b_E)
    assert 0.01 <= b_mu <= 0.49
    get_b_mu = attr_getter(index=ba_mu, left=0.01, right=0.49, default=b_mu)
    assert 1.0e-8 <= b_den <= 1.0e8
    get_b_den = attr_getter(index=ba_den, left=1.0e-8, right=1.0e8,
                            default=b_den)

    # 维度
    ndim = 3

    # 设置动力学模型
    model = DynSys()
    model.size = mesh.node_number * ndim
    for node_id in range(mesh.node_number):
        node = mesh.get_node(node_id)
        assert isinstance(node, Mesh3.Node)
        i0 = node_id * ndim
        i1 = i0 + 1
        i2 = i1 + 1
        # 节点位置
        x, y, z = node.pos
        model.set_pos(i0, x)
        model.set_pos(i1, y)
        model.set_pos(i2, z)
        # 节点速度
        model.set_vel(i0, 0)
        model.set_vel(i1, 0)
        model.set_vel(i2, 0)

    # 节点质量
    vm = [0, ] * mesh.node_number
    for body in mesh.bodies:  # body的质量
        assert isinstance(body, Mesh3.Body)
        m = body.volume * get_b_den(body) / body.node_number
        if 0 < m:
            for node in body.nodes:
                assert isinstance(node, Mesh3.Node)
                vm[node.index] += m
    for node_id in range(mesh.node_number):
        assert 0 < vm[node_id]
        i0 = node_id * ndim
        i1 = i0 + 1
        i2 = i1 + 1
        model.set_mass(i0, vm[node_id])
        model.set_mass(i1, vm[node_id])
        model.set_mass(i2, vm[node_id])

    # 修改系数(相当于组刚度矩阵)
    for index in range(model.size):  # 首先初始化
        p2f = model.get_p2f(index)
        p2f.clear()
        p2f.c = 0.0
    # 添加系数(from body)
    for body_id in range(mesh.body_number):
        # 生成这个body的单元刚度矩阵
        body = mesh.get_body(body_id)
        assert isinstance(body, Mesh3.Body)
        stiff = stiff3(body, E=get_b_E(body), mu=get_b_mu(body))
        # 修改总刚
        for i0 in range(body.node_number):
            node_i0 = body.get_node(i0).index  # 需要操作的行
            for i1 in range(body.node_number):
                node_i1 = body.get_node(i1).index  # 影响变量
                for ia in range(ndim):
                    for ib in range(ndim):
                        expr = model.get_p2f(node_i0 * ndim + ia)
                        assert isinstance(expr, LinearExpr)
                        k = -stiff[i0 * ndim + ia, i1 * ndim + ib]
                        expr.c = expr.c - k * model.get_pos(node_i1 * ndim + ib)
                        expr.add(index=node_i1 * ndim + ib, weight=k)

    # 完成，返回model
    return model
