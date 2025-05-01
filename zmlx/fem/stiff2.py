from zml import Mesh3
from zmlx.fem.stiffness_qua4 import stiffness as qua4_stiff
from zmlx.fem.elements.planar_strain_cst import stiffness as triangle_stiff


def stiff2(face: Mesh3.Face, E, mu, h=1.0):
    """
    计算单元刚度矩阵(仅仅利用x和y坐标)
    """
    assert face.node_number == 3 or face.node_number == 4
    x0, y0, z0 = face.get_node(0).pos
    x1, y1, z1 = face.get_node(1).pos
    x2, y2, z2 = face.get_node(2).pos
    if face.node_number == 3:
        stiff = triangle_stiff(nodes=[(x0, y0), (x1, y1), (x2, y2)],
                               E=E, mu=mu) * h
    else:
        x3, y3, z3 = face.get_node(3).pos
        stiff = qua4_stiff(x0, x1, x2, x3, y0, y1, y2, y3, E=E, mu=mu) * h
    assert stiff[0, 0] >= 0
    return stiff
