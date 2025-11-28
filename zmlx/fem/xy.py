"""
在x-y平面内的二维的模型.

假设：
    对于Mesh3中的每一个Node，都只有两个自由度，分别是x和y方向的位置。Node的z坐标是固定的（应该为0），不参与计算。
    使用Mesh3中的Face来定义单元。
    使用Node周围的Face来定义Node的质量。
    Node只有质量，不考虑转动惯量。
"""

from zml import Mesh3
from zmlx.fem import dyn


def get_masses(mesh: Mesh3, face_density, face_thickness):
    """
    计算各个自由度对应的质量。其中face_density为Face中物质的密度，face_thickness为Face的厚度（用以计算Face的物质体积）。
    """
    assert len(face_density) == len(face_thickness) == mesh.face_number

    vm = [0, ] * mesh.node_number
    for face in mesh.faces:  # face的质量
        assert isinstance(face, Mesh3.Face)
        m = face.area * face_thickness[face.index] * face_density[face.index] / face.node_number
        if 0 < m:
            for node in face.nodes:
                assert isinstance(node, Mesh3.Node)
                vm[node.index] += m

    # 自由度按照x-y的顺序排列
    return [vm[i // 2] for i in range(len(vm) * 2)]


def get_element(face: Mesh3.Face):
    res = []
    for node in face.nodes:
        assert isinstance(node, Mesh3.Node)
        idx = node.index
        res.append(idx * 2)
        res.append(idx * 2 + 1)
    return res


def get_elements(mesh: Mesh3):
    """
    计算各个单位对应的自由度. 每个单位是一个Face.
    """
    return [get_element(face) for face in mesh.faces]


def get_matrices(mesh: Mesh3, face_ym, face_mu, face_thickness, get_matrix=None):
    """
    计算单元刚度矩阵(各个face的)。其中face_ym为Face的杨氏模量，face_mu为Face的泊松比，face_thickness为Face的厚度。
    get_matrix为一个函数，用于计算一个Face的刚度矩阵。
        m = get_matrix的参数为(nodes, ym, mu)，其中每一个node都是[x, y]格式的节点坐标， ym是杨氏模量，mu是泊松比。
        注意：
            get_matrix可能需要根据nodes的数量来确定单元的类型，比如，是三角形单元，还是四边形单元。
    其中单元刚度m的含义为：
        m[i][j] 表示第i个自由度对第j个自由度的刚度系数。
            当仅在第 j个自由度上产生单位位移（dj=1），而其他所有自由度位移为零时，
            在第 i个自由度上需要施加的节点力（或力矩）的大小。
    """
    if get_matrix is None:  # 默认使用常应变三角形单元（平面应变状态）
        from zmlx.fem.elements.planar_strain_cst import stiffness as get_matrix

    assert len(face_ym) == len(face_mu) == len(face_thickness) == mesh.face_number
    matrices = []
    for face in mesh.faces:
        assert isinstance(face, Mesh3.Face)
        nodes = [node.pos[:2] for node in face.nodes]
        m = get_matrix(nodes, face_ym[face.index], face_mu[face.index])
        matrices.append(m * face_thickness[face.index])
    return matrices


def create_dyn(mesh: Mesh3, face_ym, face_mu, face_density, face_thickness, get_matrix=None,
               velocities=None, displacements=None):
    """
    创建一个动态模型。其中
        face_ym为Face的杨氏模量，face_mu为Face的泊松比，face_thickness为Face的厚度, face_density为Face的密度。
        get_matrix为一个函数，用于计算一个Face的刚度矩阵。
    """
    masses = get_masses(mesh, face_density=face_density, face_thickness=face_thickness)
    elements = get_elements(mesh)
    matrices = get_matrices(mesh, face_ym=face_ym, face_mu=face_mu, face_thickness=face_thickness,
                            get_matrix=get_matrix)
    return dyn.create_dyn(
        masses=masses, elements=elements, matrices=matrices, velocities=velocities,
        displacements=displacements
    )
