"""
计算各个face的刚度矩阵（使用x和y坐标），并且存储到给定的Vector里面.
"""

from zml import Vector, Mesh3
from zmlx.fem.attr_getter import attr_getter
from zmlx.fem.stiff2 import stiff2


def compute_face_stiff2(mesh: Mesh3, face_node_n=4, fa_E=None, fa_mu=None, fa_h=None,
                        f_E=1.0, f_mu=0.2, f_h=1.0):
    """
    计算face的单元刚度，并且存储.
        其中face_node_n是一个单元包含的节点的数量.
        则单元的自由度为face_node_n*2，单元刚度矩阵为 face_node_n*2*face_node_n*2

    Returns:
        一个Vector，其中的元素为face的单元刚度矩阵.
        其中的元素的数量为 mesh.face_number * face_node_n * 2 * face_node_n * 2
        todo:
            后续，可以使用numpy的ndarray来存储，这样可以提高效率.
    """
    # 生成face属性的接口函数.
    assert 1.0e-6 <= f_E <= 1.0e20
    get_f_E = attr_getter(index=fa_E, left=1.0e-6, right=1.0e20, default=f_E)
    assert 0.01 <= f_mu <= 0.49
    get_f_mu = attr_getter(index=fa_mu, left=0.01, right=0.49, default=f_mu)
    assert 0.0 <= f_h <= 1.0e20
    get_f_h = attr_getter(index=fa_h, left=0.0, right=1.0e20, default=f_h)

    # 每一个单元刚度矩阵的元素的数量
    layer_n = face_node_n * 2 * face_node_n * 2
    result = Vector(size=layer_n * mesh.face_number)
    result.fill(0)

    pointer = result.pointer
    for face_id in range(mesh.face_number):
        # 生成这个face的单元刚度矩阵
        face = mesh.get_face(face_id)
        assert isinstance(face, Mesh3.Face)
        h = get_f_h(face)
        if h <= 1.0e-30:
            continue
        offset = layer_n * face_id
        stiff = stiff2(face, E=get_f_E(face), mu=get_f_mu(face), h=h)
        dof = face.node_number * 2
        assert dof <= face_node_n * 2
        for i0 in range(dof):
            for i1 in range(dof):
                idx = dof * i0 + i1
                pointer[offset + idx] = stiff[i0, i1]

    # 完成
    return result
