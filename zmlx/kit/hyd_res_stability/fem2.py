# ** desc = '二维有限元模型(两个三角形有两个顶点固定，另外两个顶点振动过程)'

from zmlx import *
from zmlx.fem.boundary import find_boundary
from zmlx.fem.compute_face_stiff2 import compute_face_stiff2
from zmlx.mesh.triangle import layered_triangles

face_keys = AttrKeys()


def create_mesh():
    """
    创建mesh
    """
    mesh = layered_triangles(
        x_min=0, x_max=1, nx=10, y_min=0, y_max=1, ny=10, as_mesh=True)
    # 设置属性
    for face in mesh.faces:
        face.set_attr(face_keys.E, 1.0)
        face.set_attr(face_keys.mu, 0.2)
        face.set_attr(face_keys.den, 1.0)
        face.set_attr(face_keys.h, 1.0)
    return mesh


def test_1():
    print(create_mesh())


def create(mesh):
    """
    根据mesh创建模型
    """
    face_stiffs = compute_face_stiff2(
        mesh, fa_E=face_keys.E, fa_mu=face_keys.mu,
        fa_h=face_keys.h)

    model = FemAlg.create2(
        mesh=mesh, fa_den=face_keys.den, fa_h=face_keys.h,
        face_stiffs=face_stiffs)

    # 增大质量，以确保位置不变
    indexes = find_boundary(model, n_dim=2, i_dim=1, lower=1, i_dir=0,
                            eps=1.0e-4)
    for idx in indexes:
        model.set_mass(idx, 1.0e20)
    indexes = find_boundary(model, n_dim=2, i_dim=1, lower=1, i_dir=1,
                            eps=1.0e-4)
    for idx in indexes:
        model.set_mass(idx, 1.0e20)

    # 添加边界的力
    indexes = find_boundary(model, n_dim=2, i_dim=1, lower=1, i_dir=1,
                            eps=1.0e-4)
    for idx in indexes:
        model.get_p2f(idx).c += 1
        print(model.get_p2f(idx).c)

    return model


def show(model, mesh):
    """
    绘图
    """
    if gui.exists():
        vx = [model.get_pos(i * 2) for i in range(mesh.node_number)]
        vy = [model.get_pos(i * 2 + 1) for i in range(mesh.node_number)]
        dx = [vx[i] - mesh.get_node(i).pos[0] for i in range(mesh.node_number)]
        dy = [vy[i] - mesh.get_node(i).pos[1] for i in range(mesh.node_number)]
        tricontourf(x=vx, y=vy, z=dx, caption='x位移', clabel='displacement x')
        tricontourf(x=vx, y=vy, z=dy, caption='y位移', clabel='displacement y')


def solve(model, mesh):
    """
    求解给定的模型
    """
    solver = ConjugateGradientSolver(tolerance=1.0e-20)
    for step in range(5):
        break_point()
        print(f'step = {step}')
        model.iterate(dt=100, solver=solver)
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
