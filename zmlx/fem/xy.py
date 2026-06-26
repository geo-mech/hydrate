"""
定义在x-y平面内的二维的有限元模型.

假设：
    对于Mesh3中的每一个Node，都只取两个自由度，分别是x和y方向的位移。Node的z坐标不参加计算。
    基于Mesh3中的Link和Face来定义单元 （给定的Mesh3不应该包含Body）
    使用Node周围的Face的面积、厚度、密度来定义Node的质量。
    Node只有质量，不考虑转动惯量。
"""

from enum import Enum
from typing import List, Optional

from zmlx.alg import sys as warnings
from zmlx.exts import Mesh3, DynSys
from zmlx.fem import dyn
from zmlx.fem.elements import planar_strain_cst, planar_stress_cst, truss2

try:
    import numpy as np
except ImportError:
    np = None


class FaceType(Enum):
    """
    定义支持的Face单元的类型
    """
    PlanarStrainCST = 1
    PlanarStressCST = 2


class LinkType(Enum):
    Truss2 = 1  # 杆单元


def create_masses(
        mesh: Mesh3, face_density, face_thickness
):
    """
    创建各个自由度对应的质量的列表。其中face_density为Face中物质的密度，face_thickness为Face的厚度（用以计算Face的物质体积）。
    Note:
        创建自由度的质量，是建立模型的第一步.
    """
    assert len(face_density) == len(face_thickness) == mesh.face_number

    vm = [0, ] * mesh.node_number
    for face in mesh.faces:  # face的质量
        assert isinstance(face, Mesh3.Face)
        m = face.area * face_thickness[face.index] * face_density[face.index] / face.node_number
        assert m > 0, f"Face {face.index}的质量为{m}，必须大于0"
        for node in face.nodes:
            assert isinstance(node, Mesh3.Node)
            vm[node.index] += m

    # 自由度按照x-y的顺序排列
    return [vm[i // 2] for i in range(len(vm) * 2)]


def create_velocities(mesh: Mesh3, *, x=None, y=None):
    """
    创建自由度速度向量（默认为0）
    """
    res = [0, ] * (mesh.node_number * 2)
    if x is not None:
        assert len(x) == mesh.node_number
        for i in range(mesh.node_number):
            res[i * 2] = x[i]

    if y is not None:
        assert len(y) == mesh.node_number
        for i in range(mesh.node_number):
            res[i * 2 + 1] = y[i]
    return res


def create_displacements(mesh: Mesh3, *, x=None, y=None):
    """
    创建自由度位移向量（默认为0）
    """
    res = [0, ] * (mesh.node_number * 2)
    if x is not None:
        assert len(x) == mesh.node_number
        for i in range(mesh.node_number):
            res[i * 2] = x[i]

    if y is not None:
        assert len(y) == mesh.node_number
        for i in range(mesh.node_number):
            res[i * 2 + 1] = y[i]
    return res


def create_forces(mesh: Mesh3, *, x=None, y=None):
    """
    创建自由度受力向量（默认为0）
    """
    res = [0, ] * (mesh.node_number * 2)
    if x is not None:
        assert len(x) == mesh.node_number
        for i in range(mesh.node_number):
            res[i * 2] = x[i]

    if y is not None:
        assert len(y) == mesh.node_number
        for i in range(mesh.node_number):
            res[i * 2 + 1] = y[i]
    return res


def _face_element(face: Mesh3.Face):
    """
    计算Face单元对应的自由度
    """
    assert face.node_number == 3 or face.node_number == 4, f"Face {face.index}的节点数为{face.node_number}，必须为3或4"
    res = []
    for node in face.nodes:
        assert isinstance(node, Mesh3.Node)
        idx = node.index
        res.append(idx * 2)
        res.append(idx * 2 + 1)
    return res


def create_face_elements(mesh: Mesh3):
    """
    计算各个单位对应的自由度. 每个单位是一个Face.
    """
    return [_face_element(face) for face in mesh.faces]


def create_face_matrices(
        mesh: Mesh3, face_ym, face_mu, face_thickness,
        *,
        face_types: Optional[List[FaceType]] = None
):
    """
    创建各个Face单元的刚度矩阵的列表。
    """
    if face_types is None:
        face_types = [FaceType.PlanarStrainCST] * mesh.face_number

    assert len(face_types) == len(face_ym) == len(face_mu) == len(face_thickness) == mesh.face_number
    matrices = []
    for face in mesh.faces:
        assert isinstance(face, Mesh3.Face)
        nodes = [node.pos[:2] for node in face.nodes]
        if face_types[face.index] == FaceType.PlanarStrainCST:  # 平面应变单元
            m = planar_strain_cst.calc_stiffness(
                nodes, E=face_ym[face.index], mu=face_mu[face.index], thickness=face_thickness[face.index]
            )
            matrices.append(m)
        elif face_types[face.index] == FaceType.PlanarStressCST:  # 平面应力单元
            m = planar_stress_cst.calc_stiffness(
                nodes, E=face_ym[face.index], mu=face_mu[face.index], thickness=face_thickness[face.index]
            )
            matrices.append(m)
        else:
            assert False, f"不支持的单元类型：{face_types[face.index]}"
    return matrices


def _link_element(link: Mesh3.Link):
    """
    计算Link单元对应的自由度
    """
    assert link.node_number == 2, f"Link {link.index}的节点数为{link.node_number}，必须为2"
    res = []
    for node in link.nodes:
        assert isinstance(node, Mesh3.Node)
        idx = node.index
        res.append(idx * 2)
        res.append(idx * 2 + 1)
    return res


def create_link_elements(mesh: Mesh3):
    """
    计算各个单位对应的自由度. 每个单位是一个Link.
    """
    return [_link_element(link) for link in mesh.links]


def create_link_matrices(
        mesh: Mesh3, link_ym, link_area,
        *,
        link_types: Optional[List[LinkType]] = None
):
    """
    创建各个Link单元的刚度矩阵的列表。
    """
    if link_types is None:
        link_types = [LinkType.Truss2] * mesh.link_number

    assert len(link_types) == len(link_ym) == len(link_area) == mesh.link_number
    matrices = []
    for link in mesh.links:
        nodes = [node.pos[:2] for node in link.nodes]
        if link_types[link.index] == LinkType.Truss2:
            m = truss2.calc_stiffness(
                nodes, E=link_ym[link.index], area=link_area[link.index]
            )
            matrices.append(m)
        else:
            assert False, f"不支持的单元类型：{link_types[link.index]}"
    return matrices


# 与create_masses相同
get_masses = create_masses
# 与create_elements相同
get_elements = create_face_elements


def get_matrices(
        mesh: Mesh3, face_ym, face_mu, face_thickness,
        get_matrix=None
):
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
    warnings.warn("get_matrices is deprecated, please use create_matrices instead",
                  DeprecationWarning,
                  stacklevel=2)
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
    warnings.warn("create_dyn is deprecated, please use create_model instead",
                  DeprecationWarning,
                  stacklevel=2)
    masses = get_masses(mesh, face_density=face_density, face_thickness=face_thickness)
    elements = get_elements(mesh)
    matrices = get_matrices(
        mesh, face_ym=face_ym, face_mu=face_mu, face_thickness=face_thickness,
        get_matrix=get_matrix
    )
    return dyn.create_dyn(
        masses=masses, elements=elements, matrices=matrices, velocities=velocities,
        displacements=displacements
    )


class FemModel:
    """
    有限元模型
    """

    def __init__(self):
        """
        初始化变量
        """
        self._mesh: Optional[Mesh3] = None
        self._dyn: Optional[DynSys] = None
        self._face_density = None
        self._face_thickness = None
        self._face_matrices = None
        self._face_elements = None
        self._face_types = None
        self._node_x = None
        self._node_y = None
        self._link_elements = None
        self._link_types = None
        self._link_matrices = None

    def set_mesh(self, mesh: Mesh3, *, face_density=None, face_thickness=None, face_ym=None, face_mu=None,
                 face_types=None, link_ym=None, link_area=None, link_types=None):
        """
        设置模型的网格，并创建模型
        """
        assert self._mesh is None and self._dyn is None, "set_mesh can only be called once"
        assert np is not None, "numpy is required"

        self._mesh = mesh
        self._node_x = np.array(
            [node.get_pos(0) for node in mesh.nodes]
        )
        self._node_y = np.array(
            [node.get_pos(1) for node in mesh.nodes]
        )

        # 各个自由度的质量
        if face_density is None:
            self._face_density = [1.0] * mesh.face_number
        else:
            self._face_density = face_density

        if face_thickness is None:
            self._face_thickness = [1.0] * mesh.face_number
        else:
            self._face_thickness = face_thickness

        assert len(self._face_density) == len(self._face_thickness) == mesh.face_number
        masses = create_masses(
            mesh, face_density=self._face_density, face_thickness=self._face_thickness
        )

        # 各个面的单元和刚度矩阵
        if face_ym is not None and face_mu is not None:
            self._face_elements = create_face_elements(mesh)
            if face_types is None:
                self._face_types = [FaceType.PlanarStrainCST] * mesh.face_number  # 默认采用常应变三角形单元
            else:
                self._face_types = face_types
            self._face_matrices = create_face_matrices(
                mesh, face_ym=face_ym, face_mu=face_mu, face_thickness=self._face_thickness,
                face_types=self._face_types
            )
        else:
            self._face_elements = []
            self._face_matrices = []

        # 添加基于各个Link的单元
        if link_ym is not None and link_area is not None:
            self._link_elements = create_link_elements(mesh)
            if link_types is None:
                self._link_types = [LinkType.Truss2] * mesh.link_number
            else:
                self._link_types = link_types
            self._link_matrices = create_link_matrices(
                mesh, link_ym=link_ym, link_area=link_area, link_types=self._link_types
            )
        else:
            self._link_elements = []
            self._link_matrices = []

        # 创建初始的dyn模型
        self._dyn = dyn.create_dyn(
            masses=masses,
            elements=self._face_elements + self._link_elements,
            matrices=self._face_matrices + self._link_matrices
        )

    def get_mass(self, *, node_id=None, dim=None):
        """
        返回节点的质量
        """
        assert self._dyn is not None
        if node_id is None:
            assert np is not None
            buffer = np.zeros(self._dyn.size, dtype=np.float64)
            self._dyn.write_mass(buffer)
            vx = buffer[0::2]
            vy = buffer[1::2]
            if dim is None:
                return vx, vy
            elif dim == 0:
                return vx
            else:
                assert dim == 1
                return vy
        else:
            return self._dyn.get_mass(node_id * 2 + dim)

    def set_mass(self, *, node_id=None, dim=None, value=None):
        """
        设置节点的质量
        """
        assert self._dyn is not None
        assert node_id is not None and dim is not None and value is not None
        assert dim == 0 or dim == 1, f"dim must be 0 or 1, but got {dim}"
        self._dyn.set_mass(node_id * 2 + dim, value)

    def get_pos(self, *, node_id=None, dim=None):
        """
        返回节点的位置
        """
        if node_id is None:
            assert self._node_x is not None and self._node_y is not None
            if dim is None:
                return np.copy(self._node_x), np.copy(self._node_y)
            elif dim == 0:
                return np.copy(self._node_x)
            else:
                assert dim == 1
                return np.copy(self._node_y)
        else:
            assert self._mesh is not None
            assert dim is not None
            return self._mesh.get_node(node_id).get_pos(dim)

    def get_disp(self, *, node_id=None, dim=None):
        """
        返回节点的位移
        """
        assert self._dyn is not None
        if node_id is None:
            assert np is not None
            buffer = np.zeros(self._dyn.size, dtype=np.float64)
            self._dyn.write_pos(buffer)
            vx = buffer[0::2]
            vy = buffer[1::2]
            if dim is None:
                return vx, vy
            elif dim == 0:
                return vx
            else:
                assert dim == 1
                return vy
        else:
            return self._dyn.get_pos(node_id * 2 + dim)

    def set_disp(self, *, node_id=None, dim=None, value=None):
        """
        设置节点的位移
        """
        assert self._dyn is not None
        assert dim == 0 or dim == 1, f"dim must be 0 or 1, but got {dim}"
        self._dyn.set_pos(node_id * 2 + dim, value)
    def get_force(self, *, node_id=None, dim=None):
        """
        返回节点的力
        """
        assert self._dyn is not None
        if node_id is None:
            assert np is not None
            buffer = np.zeros(self._dyn.size, dtype=np.float64)
            self._dyn.write_p2f_c(buffer)
            vx = buffer[0::2]
            vy = buffer[1::2]
            if dim is None:
                return vx, vy
            elif dim == 0:
                return vx
            else:
                assert dim == 1
                return vy
        else:
            return self._dyn.get_p2f(node_id * 2 + dim).c

    def set_force(self, *, node_id=None, dim=None, value=None):
        """
        设置节点的位移
        """
        assert self._dyn is not None
        assert dim == 0 or dim == 1, f"dim must be 0 or 1, but got {dim}"
        lexpr = self._dyn.get_p2f(node_id * 2 + dim)
        lexpr.c = value  # 设置节点力

    def get_dyn(self):
        """
        返回动力学模型
        """
        return self._dyn

    def get_mesh(self):
        """
        返回网格对象
        """
        return self._mesh

    def get_node_number(self):
        """
        返回节点的数量
        """
        assert self._mesh is not None
        return self._mesh.node_number

    def iterate(self, dt: float, solver=None):
        """
        向前迭代一步
        """
        assert self._dyn is not None
        return self._dyn.iterate(dt, solver=solver)
