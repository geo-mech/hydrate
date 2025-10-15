# ** desc = '在上一个case的基础上，使用SeepageMesh简化循环'

from zmlx import *
from zmlx.plt.on_axes import add_axes2, item, add_items


def set_cell(c: Seepage.CellData, x, y, v, p):
    """
    设置一个Cell的属性
    Args:
        c: 要设置属性的Cell对象
        x: 单元的位置，x坐标
        y: 单元的位置，y坐标
        v: 单元的体积，m3
        p: 单元的压力，Pa
    """
    c.pos = [x, y, 0]
    c.set_pore(p=1e6, v=v, dp=1e6, dv=v * 0.1)
    c.fluid_number = 1
    c.get_fluid(0).vol = c.p2v(p)
    c.get_fluid(0).vis = 1.0e-3  # 水的粘性系数，Pa.s


def add_cell(model: Seepage, x, y, v, p):
    """
    在一个渗流模型中(Seepage)，添加一个流体的控制单元(Seepage.Cell)
    Args:
        model: 需要添加单元的模型，Seepage类的对象
        x: 单元的位置，x坐标
        y: 单元的位置，y坐标
        v: 单元的体积，m3
        p: 单元的压力，Pa
    """
    c = model.add_cell()
    set_cell(c, x, y, v, p)


def add_face(model: Seepage, i0, i1, area, dist, perm):
    """
    在一个渗流模型中(Seepage)，添加一个流体的流动面(Seepage.Face)
    Args:
        model: 需要添加单元的模型，Seepage类的对象
        i0: 第一个单元的索引
        i1: 第二个单元的索引
        area: 流动的横截面积，m2
        dist: 单元之间的距离，m
        perm: 渗透率，单位：m2
    """
    face = model.add_face(i0, i1)
    face.cond = area * perm / dist


def pressure_item(model: Seepage, jx, jy):
    """
    显示模型中所有Cell的压力分布
    Args:
        model: 渗流模型，Seepage类的对象
        jx: 单元的数量，x方向
        jy: 单元的数量，y方向
    Returns:
        压裂分布曲线
    """
    x = np.reshape(as_numpy(model).cells.x, (jx, jy))
    y = np.reshape(as_numpy(model).cells.y, (jx, jy))
    p = np.reshape(as_numpy(model).cells.pre / 1e6, (jx, jy))
    return item('contourf', x, y, p, cbar={'label': 'Pressure/MPa', 'shrink': 0.7})


def test():
    """
    运行测试：创建模型、运行、绘制结果
    """
    model = Seepage()

    # 定义模型的尺寸
    jx, jy = 30, 20

    # 创建SeepageMesh(并将第一个和最后一个Cell的体积设置为无穷大)
    mesh = create_cube(x=linspace(0, jx, jx + 1), y=linspace(0, jy, jy + 1), z=[-0.5, 0.5])
    # 添加Cell。
    for c1 in mesh.cells:
        add_cell(model, x=c1.pos[0], y=c1.pos[1], v=c1.vol, p=1.5e6)
    # 在对角位置设置压力固定（将Cell的体积设置为无穷大）
    c = model.get_cell(0)
    set_cell(c, x=c.pos[0], y=c.pos[1], v=1e6, p=2e6)
    c = model.get_cell(-1)
    set_cell(c, x=c.pos[0], y=c.pos[1], v=1e6, p=1e6)

    # 在这些Cell之间，添加Face，用于描述流体在这些Cell之间的流动
    for f1 in mesh.faces:
        add_face(
            model, f1.cell_i0, f1.cell_i1, area=f1.area, dist=f1.dist,
            perm=1.0e-15
        )

    # 迭代并且绘图显示
    step_max = 100
    dt = 1.0
    for step in range(step_max):
        print(f'step = {step}/{step_max}, dt = {time2str(dt)}')
        model.iterate(dt=dt)
        dt = model.get_recommended_dt(previous_dt=dt, dv_relative=0.1)
        items = [pressure_item(model, jx, jy)]
        plot(add_axes2, add_items, *items,
             xlabel="x/m", ylabel="y/m", title=f'Pressure Distribution, step = {step}',
             aspect='equal', tight_layout=True,
             caption='压力场'
             )


if __name__ == '__main__':
    gui.execute(test, close_after_done=False)
