from zmlx import *
import numpy as np
from zmlx.react import melt


class CellKeys:
    temp = 0
    mc = 1
    power = 2


class FaceKeys:
    g_heat = 0


class FluIds:
    gas = 0
    sol = 1


class FluKeys:
    temp = 0
    c = 1


def create_mesh(width, grid):
    """
    创建一个Mesh
    """
    # 创建一个正方形的mesh，中心点在0，0。在方向上，坐标在0到1之间(厚度为1)
    x = np.linspace(-width * 0.5, width * 0.5, round(width / grid))
    y = x
    z = [0, 1]
    mesh = SeepageMesh.create_cube(x, y, z)

    # 添加一个虚拟的Cell，用以模拟热环境
    virtual_cell = mesh.add_cell()
    virtual_cell.pos = [0, 0, -1]
    virtual_cell.vol = 1.0e5    # 将它的体积设置得很大(为了计算的稳定，也不宜过大，比正常大三五个量级即可)
    for idx in range(mesh.cell_number - 1):
        face = mesh.add_face(mesh.get_cell(idx), virtual_cell)
        face.area = mesh.get_cell(idx).vol
        face.length = 1.0

    # 返回Mesh
    return mesh


def _test1():
    mesh = create_mesh(100, 1)
    print(mesh)


def create_model(mesh, t_ini=100.0):
    assert isinstance(mesh, SeepageMesh)

    model = Seepage()

    for c in mesh.cells:
        assert isinstance(c, SeepageMesh.Cell)
        cell = model.add_cell()
        assert isinstance(cell, Seepage.Cell)

        cell.pos = c.pos
        cell.set_attr(CellKeys.mc, c.vol * 1.0e6)
        cell.set_attr(CellKeys.temp, t_ini)  # 背景温度（如果没有加热，则最终冷却到这个温度）
        cell.set_attr(CellKeys.power, 0.0)

        cell.fluid_number = 2
        cell.get_fluid(FluIds.gas).set(mass=1).set_attr(FluKeys.temp, t_ini).set_attr(FluKeys.c, 1000.0)
        cell.get_fluid(FluIds.sol).set(mass=1).set_attr(FluKeys.temp, t_ini).set_attr(FluKeys.c, 1000.0)

    for f in mesh.faces:
        assert isinstance(f, SeepageMesh.Face)
        face = model.add_face(model.get_cell(f.link[0]), model.get_cell(f.link[1]))
        assert isinstance(face, Seepage.Face)
        face.set_attr(FaceKeys.g_heat, f.area * 1.0 / f.length)

    # 在中心点，设置一个区域，让固体的质量等于0
    for cell in model.cells:
        if get_distance([0, 0, 0], cell.pos) < 2 or get_distance([15, 15, 0], cell.pos) < 2 or get_distance([-15, 15, 0], cell.pos) < 2:
            cell.get_fluid(FluIds.gas).set(mass=2)
            cell.get_fluid(FluIds.sol).set(mass=0)

    # 添加一个反应
    r = melt.create(
        sol=FluIds.sol,
        flu=FluIds.gas,
        vp=[1, 100e6],
        vt=[105, 105],
        temp=105,
        heat=573000,
        fa_t=FluKeys.temp,
        fa_c=FluKeys.c,
        t2q=([-10, 0, 10], [-1, 0, 1]),
        l2r=True,
        r2l=False,  # 和melt相比，方向改变
    )
    model.add_reaction(r)

    return model


def _test2():
    mesh = create_mesh(100, 1)
    print(mesh)
    model = create_model(mesh)
    print(model)


def show(model):
    assert isinstance(model, Seepage)

    x = model.numpy.cells.x
    y = model.numpy.cells.y
    z = model.numpy.cells.z
    mask = z > 0
    T = model.numpy.cells.get(CellKeys.temp)
    tricontourf(x[mask], y[mask], T[mask], caption='温度')

    m0 = model.numpy.fluids(FluIds.gas).mass
    m1 = model.numpy.fluids(FluIds.sol).mass
    s1 = m1 / (m0 + m1)
    tricontourf(x[mask], y[mask], s1[mask], caption='固体')


def _test3():
    mesh = create_mesh(100, 1)
    print(mesh)
    model = create_model(mesh)
    print(model)
    show(model)


def solve(model: Seepage, dt):
    """
    向前迭代一步
    """
    sol = ConjugateGradientSolver(tolerance=1.0e-15)
    for step in range(10000):
        gui.break_point()
        print(f'step = {step}')

        # 根据固体的饱和度，计算加热的功率
        m0 = model.numpy.fluids(FluIds.gas).mass
        m1 = model.numpy.fluids(FluIds.sol).mass
        s1 = m1 / (m0 + m1)  # 固体的比例
        power = np.ones(shape=s1.shape) * 1
        power[s1 < 0.01] = 30
        model.numpy.cells.set(CellKeys.power, power)

        # 加热
        model.heating(ca_mc=CellKeys.mc, ca_t=CellKeys.temp, ca_p=CellKeys.power, dt=dt)

        # 限定虚拟边界的温度
        model.get_cell(model.cell_number-1).set_attr(CellKeys.temp, 100.0)

        # 传热
        model.iterate_thermal(dt=dt, ca_t=CellKeys.temp, ca_mc=CellKeys.mc, fa_g=FaceKeys.g_heat, solver=sol)

        # 直接把Cell的温度给流体
        temp = model.numpy.cells.get(CellKeys.temp)
        model.numpy.fluids(FluIds.gas).set(FluKeys.temp, temp)
        model.numpy.fluids(FluIds.sol).set(FluKeys.temp, temp)

        # 反应
        model.get_reaction(0).react(model, dt=dt)

        # 将流体的温度再返回给固体
        temp = model.numpy.fluids(FluIds.sol).get(FluKeys.temp)
        model.numpy.cells.set(CellKeys.temp, temp)

        # 绘图
        if step % 50 == 0:
            show(model)


def _test4():
    mesh = create_mesh(100, 1)
    model = create_model(mesh)
    gui.execute(lambda: solve(model, 1.0e6), close_after_done=False)


if __name__ == '__main__':
    _test4()
