"""
定义三维有限元模型.

假设：
    对于Mesh3中的每一个Node，取三个自由度，分别是x、y和z方向的位移。
    基于Mesh3中的Body来定义单元（给定的Mesh3应该包含Body）。
    使用Body的体积和密度来定义Node的质量（集中质量矩阵）。
    get_pos() 返回初始网格坐标，需与 get_disp() 相加得到变形后坐标。
"""

from typing import Optional

from zmlx.exts import Mesh3, DynSys
from zmlx.fem import dyn
from zmlx.fem.stiff3 import stiff3

try:
    import numpy as np
except ImportError:
    np = None


def create_masses(mesh: Mesh3, body_density):
    """
    创建各个自由度对应的质量列表。
    其中body_density为Body中物质的密度。
    """
    assert len(body_density) == mesh.body_number

    vm = [0.0] * mesh.node_number
    for body in mesh.bodies:
        assert isinstance(body, Mesh3.Body)
        m = body.volume * body_density[body.index] / body.node_number
        assert m > 0, f"Body {body.index}的质量为{m}，必须大于0"
        for node in body.nodes:
            assert isinstance(node, Mesh3.Node)
            vm[node.index] += m

    # 自由度按照x-y-z的顺序排列
    return [vm[i // 3] for i in range(len(vm) * 3)]


def create_velocities(mesh: Mesh3, *, x=None, y=None, z=None):
    """
    创建自由度速度向量（默认为0）
    """
    res = [0.0] * (mesh.node_number * 3)
    if x is not None:
        assert len(x) == mesh.node_number
        for i in range(mesh.node_number):
            res[i * 3] = x[i]
    if y is not None:
        assert len(y) == mesh.node_number
        for i in range(mesh.node_number):
            res[i * 3 + 1] = y[i]
    if z is not None:
        assert len(z) == mesh.node_number
        for i in range(mesh.node_number):
            res[i * 3 + 2] = z[i]
    return res


def create_displacements(mesh: Mesh3, *, x=None, y=None, z=None):
    """
    创建自由度位移向量（默认为0）
    """
    res = [0.0] * (mesh.node_number * 3)
    if x is not None:
        assert len(x) == mesh.node_number
        for i in range(mesh.node_number):
            res[i * 3] = x[i]
    if y is not None:
        assert len(y) == mesh.node_number
        for i in range(mesh.node_number):
            res[i * 3 + 1] = y[i]
    if z is not None:
        assert len(z) == mesh.node_number
        for i in range(mesh.node_number):
            res[i * 3 + 2] = z[i]
    return res


def create_forces(mesh: Mesh3, *, x=None, y=None, z=None):
    """
    创建自由度受力向量（默认为0）
    """
    res = [0.0] * (mesh.node_number * 3)
    if x is not None:
        assert len(x) == mesh.node_number
        for i in range(mesh.node_number):
            res[i * 3] = x[i]
    if y is not None:
        assert len(y) == mesh.node_number
        for i in range(mesh.node_number):
            res[i * 3 + 1] = y[i]
    if z is not None:
        assert len(z) == mesh.node_number
        for i in range(mesh.node_number):
            res[i * 3 + 2] = z[i]
    return res


def _body_element(body: Mesh3.Body):
    """
    计算Body单元对应的自由度
    """
    assert body.node_number in (4, 6, 8), \
        f"Body {body.index}的节点数为{body.node_number}，必须为4、6或8"
    res = []
    for node in body.nodes:
        assert isinstance(node, Mesh3.Node)
        idx = node.index
        res.append(idx * 3)
        res.append(idx * 3 + 1)
        res.append(idx * 3 + 2)
    return res


def create_body_elements(mesh: Mesh3):
    """
    计算各个Body单元对应的自由度。
    """
    return [_body_element(body) for body in mesh.bodies]


def create_body_matrices(mesh: Mesh3, body_ym, body_mu):
    """
    创建各个Body单元的刚度矩阵的列表。
    """
    assert len(body_ym) == len(body_mu) == mesh.body_number
    matrices = []
    for body in mesh.bodies:
        assert isinstance(body, Mesh3.Body)
        m = stiff3(body, E=body_ym[body.index], mu=body_mu[body.index])
        matrices.append(m)
    return matrices


class FemModel:
    """
    三维有限元模型
    """

    def __init__(self):
        self._mesh: Optional[Mesh3] = None
        self._dyn: Optional[DynSys] = None
        self._body_density = None
        self._body_matrices = None
        self._body_elements = None
        self._node_x = None
        self._node_y = None
        self._node_z = None

    def set_mesh(self, mesh: Mesh3, *, body_density=None, body_ym=None, body_mu=None):
        """
        设置模型的网格，并创建模型
        """
        assert self._mesh is None and self._dyn is None, "set_mesh can only be called once"
        assert np is not None, "numpy is required"

        self._mesh = mesh
        self._node_x = np.array([node.get_pos(0) for node in mesh.nodes])
        self._node_y = np.array([node.get_pos(1) for node in mesh.nodes])
        self._node_z = np.array([node.get_pos(2) for node in mesh.nodes])

        # 各个自由度的质量（集中质量矩阵，每个 body 的质量均分到其所有节点）
        if body_density is None:
            self._body_density = [1.0] * mesh.body_number
        else:
            self._body_density = body_density

        assert len(self._body_density) == mesh.body_number
        masses = create_masses(mesh, body_density=self._body_density)

        # 各个体的刚度矩阵（单元类型由 stiff3 根据 body.node_number 自动判定）
        if body_ym is not None and body_mu is not None:
            self._body_elements = create_body_elements(mesh)
            self._body_matrices = create_body_matrices(
                mesh, body_ym=body_ym, body_mu=body_mu
            )
        else:
            self._body_elements = []
            self._body_matrices = []

        # 创建初始的dyn模型
        self._dyn = dyn.create_dyn(
            masses=masses,
            elements=self._body_elements,
            matrices=self._body_matrices
        )

    def get_mass(self, *, node_id=None, dim=None):
        assert self._dyn is not None
        if node_id is None:
            assert np is not None
            buffer = np.zeros(self._dyn.size, dtype=np.float64)
            self._dyn.write_mass(buffer)
            vx = buffer[0::3]
            vy = buffer[1::3]
            vz = buffer[2::3]
            if dim is None:
                return vx, vy, vz
            elif dim == 0:
                return vx
            elif dim == 1:
                return vy
            else:
                assert dim == 2
                return vz
        else:
            return self._dyn.get_mass(node_id * 3 + dim)

    def set_mass(self, *, node_id=None, dim=None, value=None):
        assert self._dyn is not None
        assert node_id is not None and dim is not None and value is not None
        assert 0 <= dim <= 2, f"dim must be 0, 1, or 2, but got {dim}"
        self._dyn.set_mass(node_id * 3 + dim, value)

    def get_pos(self, *, node_id=None, dim=None):
        if node_id is None:
            assert self._node_x is not None
            if dim is None:
                return np.copy(self._node_x), np.copy(self._node_y), np.copy(self._node_z)
            elif dim == 0:
                return np.copy(self._node_x)
            elif dim == 1:
                return np.copy(self._node_y)
            else:
                assert dim == 2
                return np.copy(self._node_z)
        else:
            assert self._mesh is not None
            assert dim is not None
            return self._mesh.get_node(node_id).get_pos(dim)

    def get_disp(self, *, node_id=None, dim=None):
        assert self._dyn is not None
        if node_id is None:
            assert np is not None
            buffer = np.zeros(self._dyn.size, dtype=np.float64)
            self._dyn.write_pos(buffer)
            vx = buffer[0::3]
            vy = buffer[1::3]
            vz = buffer[2::3]
            if dim is None:
                return vx, vy, vz
            elif dim == 0:
                return vx
            elif dim == 1:
                return vy
            else:
                assert dim == 2
                return vz
        else:
            return self._dyn.get_pos(node_id * 3 + dim)

    def set_disp(self, *, node_id=None, dim=None, value=None):
        assert self._dyn is not None
        assert 0 <= dim <= 2, f"dim must be 0, 1, or 2, but got {dim}"
        self._dyn.set_pos(node_id * 3 + dim, value)

    def get_force(self, *, node_id=None, dim=None):
        assert self._dyn is not None
        if node_id is None:
            assert np is not None
            buffer = np.zeros(self._dyn.size, dtype=np.float64)
            self._dyn.write_p2f_c(buffer)
            vx = buffer[0::3]
            vy = buffer[1::3]
            vz = buffer[2::3]
            if dim is None:
                return vx, vy, vz
            elif dim == 0:
                return vx
            elif dim == 1:
                return vy
            else:
                assert dim == 2
                return vz
        else:
            return self._dyn.get_p2f(node_id * 3 + dim).c

    def set_force(self, *, node_id=None, dim=None, value=None):
        assert self._dyn is not None
        assert 0 <= dim <= 2, f"dim must be 0, 1, or 2, but got {dim}"
        lexpr = self._dyn.get_p2f(node_id * 3 + dim)
        lexpr.c = value

    def get_dyn(self):
        return self._dyn

    def get_mesh(self):
        return self._mesh

    def get_node_number(self):
        assert self._mesh is not None
        return self._mesh.node_number

    def iterate(self, dt: float, solver=None):
        assert self._dyn is not None
        return self._dyn.iterate(dt, solver=solver)
