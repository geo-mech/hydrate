# ** desc = '二维有限元模型(两个三角形有两个顶点固定，另外两个顶点振动过程)'

from zmlx import *
from zmlx.fem.dyn import create_dyn
from zmlx.fem.elements.planar_strain_cst import stiffness
from zmlx.fem import xy

def create_mesh():
    """
    创建mesh
    """
    mesh = Mesh3()

    # 添加node
    nodes = [mesh.add_node(*pos) for pos in
             [(0, 0, 0), (1, 0, 0), (0.5, 1, 0), (1.5, 1, 0)]]

    # 添加link和face
    for triangle in [(0, 1, 2), (1, 2, 3)]:
        n0 = nodes[triangle[0]]
        n1 = nodes[triangle[1]]
        n2 = nodes[triangle[2]]
        mesh.add_face(
            [mesh.add_link([n0, n1]), mesh.add_link([n1, n2]),
             mesh.add_link([n2, n0])]
        )
    return mesh


def create(mesh: Mesh3):
    """
    根据mesh创建模型
    """
    face_n = mesh.face_number
    masses = xy.get_masses(mesh, face_density=[1.0] * face_n, face_thickness=[1.0] * face_n)

    velocities = [0.0] * mesh.node_number * 2
    displacements = [0.0] * mesh.node_number * 2
    elements = xy.get_elements(mesh)
    matrices = xy.get_matrices(mesh, face_ym=[1.0] * face_n,
                               face_mu=[0.2] * face_n,
                               face_thickness=[1.0] * face_n)

    model = create_dyn(
        masses=masses, velocities=velocities,
        displacements=displacements,
        elements=elements,
        matrices=matrices
    )

    # 增大质量，以确保位置不变
    for idx in [0, 1, 3]:
        model.set_mass(idx, model.get_mass(idx) * 1.0e20)

    # 修改初始位置，打破平衡状态
    idx = 3 * 2  # 第3个node的x
    model.set_pos(idx, model.get_pos(idx) + 0.2)

    return model


def show(model, mesh: Mesh3):
    """
    绘图
    """
    if gui.exists():
        dx = [model.get_pos(i * 2) for i in range(mesh.node_number)]
        dy = [model.get_pos(i * 2 + 1) for i in range(mesh.node_number)]
        vx = [node.pos[0] for node in mesh.nodes]
        vy = [node.pos[1] for node in mesh.nodes]
        vx = [vx[i] + dx[i] for i in range(len(vx))]
        vy = [vy[i] + dy[i] for i in range(len(vy))]
        tricontourf(x=vx, y=vy, z=dx, caption='x位移', clabel='displacement x')


def solve(model: DynSys, mesh):
    """
    求解给定的模型
    """
    for step in range(5000):
        gui.break_point()
        print(f'step = {step}')
        model.iterate(dt=0.1)
        if step % 20 == 0:
            show(model, mesh)


def execute(gui_mode=True, close_after_done=False):
    """
    主函数
    """
    mesh = create_mesh()
    model = create(mesh=mesh)
    gui.execute(func=solve, args=[model, mesh],
                close_after_done=close_after_done, disable_gui=not gui_mode)


if __name__ == '__main__':
    execute()
