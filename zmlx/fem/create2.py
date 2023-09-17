"""
创建二维的有限元模型
"""

from zml import *
from zmlx.fem.stiffness_triangle import stiffness as triangle_stiff
from zmlx.fem.stiffness_qua4 import stiffness as qua4_stiff


def create2(mesh, fa_E=None, fa_mu=None, fa_den=None, fa_h=None,
            E=1.0, mu=0.2, den=1.0, h=1.0):
    """
    创建二维的动力学模型。 其中mesh为网格，fa_E为face的杨氏模量属性，fa_mu为face的泊松比属性。
    fa_den为face的密度属性(kg/m^3), fa_h为face的厚度属性.

    E为默认的杨氏模量, mu为默认的泊松比，den为默认的密度，h为默认的厚度.

    注意：
        1、对于mesh中所有的node的位置，将仅使用x和y坐标，因此务必保证mesh是二维的；
        2、仅支持三角形网格和四边形网格（以及两者混合的网格）；

    返回：
        DynSys对象，其中的自由度的数量是mesh中node数量的二倍.
    """
    assert isinstance(mesh, Mesh3)

    def make_fn(index, min, max, default):
        """
        用以生成获取face属性的函数
        """
        if index is None:
            def f(face):
                return default
            return f
        else:
            def f(face):
                assert isinstance(face, Mesh3.Face)
                return face.get_attr(index=index, min=min, max=max, default_val=default)
            return f

    # 生成face属性的接口函数.
    assert 1.0e-6 <= E <= 1.0e20
    get_E = make_fn(index=fa_E, min=1.0e-6, max=1.0e20, default=E)
    assert 0.01 <= mu <= 0.49
    get_mu = make_fn(index=fa_mu, min=0.01, max=0.49, default=mu)
    assert 1.0e-8 <= den <= 1.0e8
    get_den = make_fn(index=fa_den, min=1.0e-8, max=1.0e8, default=den)
    assert 1.0e-10 <= h <= 1.0e20
    get_h = make_fn(index=fa_h, min=1.0e-10, max=1.0e20, default=h)

    # 设置动力学模型
    dyn = DynSys()
    dyn.size = mesh.node_number * 2
    for node_id in range(mesh.node_number):
        node = mesh.get_node(node_id)
        assert isinstance(node, Mesh3.Node)
        i0 = node_id * 2
        i1 = i0 + 1
        # 节点位置
        x, y, z = node.pos
        dyn.set_pos(i0, x)
        dyn.set_pos(i1, y)
        # 节点速度
        dyn.set_vel(i0, 0)
        dyn.set_vel(i1, 0)

    # 节点质量
    vm = [0, ] * mesh.node_number
    for face in mesh.faces:
        assert isinstance(face, Mesh3.Face)
        m = face.area * get_h(face) * get_den(face) / face.node_number
        assert 0 < m
        for node in face.nodes:
            assert isinstance(node, Mesh3.Node)
            vm[node.index] += m
    for node_id in range(mesh.node_number):
        assert 0 < vm[node_id]
        i0 = node_id * 2
        i1 = i0 + 1
        dyn.set_mas(i0, vm[node_id])
        dyn.set_mas(i1, vm[node_id])

    # 修改系数(相当于组刚度矩阵)
    for index in range(dyn.size):  # 首先初始化
        p2f = dyn.get_p2f(index)
        p2f.clear()
        p2f.c = 0.0
    # 添加系数
    for face_id in range(mesh.face_number):
        # 生成这个face的单元刚度矩阵
        face = mesh.get_face(face_id)
        assert isinstance(face, Mesh3.Face)
        assert face.node_number == 3 or face.node_number == 4
        if face.node_number == 3:
            x0, y0, z0 = face.get_node(0).pos
            x1, y1, z1 = face.get_node(1).pos
            x2, y2, z2 = face.get_node(2).pos
            stiff = triangle_stiff(x0, x1, x2, y0, y1, y2, E=get_E(face), mu=get_mu(face))
        else:
            x0, y0, z0 = face.get_node(0).pos
            x1, y1, z1 = face.get_node(1).pos
            x2, y2, z2 = face.get_node(2).pos
            x3, y3, z3 = face.get_node(3).pos
            stiff = qua4_stiff(x0, x1, x2, x3, y0, y1, y2, y3, E=get_E(face), mu=get_mu(face))
        stiff = stiff * get_h(face)
        # 修改总刚
        for i0 in range(face.node_number):
            node_i0 = face.get_node(i0).index   # 需要操作的行
            for i1 in range(face.node_number):
                node_i1 = face.get_node(i1).index  # 影响变量
                for ia, ib in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                    expr = dyn.get_p2f(node_i0 * 2 + ia)
                    assert isinstance(expr, LinearExpr)
                    k = -stiff[i0*2+ia, i1*2+ib]  # 加上负号
                    expr.c = expr.c - k * dyn.get_pos(node_i1 * 2 + ib)
                    expr.add(index=node_i1 * 2 + ib, weight=k)

    # 完成，返回dyn
    return dyn
