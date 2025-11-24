# ** desc = '单相的流动。在单相的基础上，添加了盐度组分的扩散效应'

from zmlx import *


def set_cell(c: Seepage.CellData, x, y, v, p, s=None):
    """
    设置一个Cell的属性
    Args:
        c: 要设置属性的Cell对象
        x: 单元的位置，x坐标
        y: 单元的位置，y坐标
        v: 单元的体积，m3
        p: 单元的压力，Pa
        s: 盐度的比例，默认为0
    """
    if x is not None and y is not None:
        c.pos = [x, y, 0]
    c.set_pore(p=1e6, v=v, dp=1e6, dv=v * 0.1)
    c.fluid_number = 1
    f = c.get_fluid(0)
    f.component_number = 3  # 此流体有3个组分
    fv = c.p2v(p)  # 总的体积
    if s is None:
        s = [0.0, 0.0]
    f.get_component(0).vol = fv * (1 - s[0] - s[1])
    f.get_component(1).vol = fv * s[0]  # 盐的体积
    f.get_component(2).vol = fv * s[1]  # 盐的体积


def add_cell(model: Seepage, x, y, v, p, s=None):
    """
    在一个渗流模型中(Seepage)，添加一个流体的控制单元(Seepage.Cell)
    Args:
        model: 需要添加单元的模型，Seepage类的对象
        x: 单元的位置，x坐标
        y: 单元的位置，y坐标
        v: 单元的体积，m3
        p: 单元的压力，Pa
        s: 盐度的比例，默认为None
    """
    c = model.add_cell()
    set_cell(c, x, y, v, p, s)
    return c


def add_face(model: Seepage, i0, i1, area, perm):
    """
    在一个渗流模型中(Seepage)，添加一个流体的流动面(Seepage.Face)
    Args:
        model: 需要添加单元的模型，Seepage类的对象
        i0: 第一个单元的索引
        i1: 第二个单元的索引
        area: 流动的横截面积，m2
        perm: 渗透率，单位：m2
    """
    dist = get_distance(model.get_cell(i0).pos, model.get_cell(i1).pos)
    face = model.add_face(i0, i1)
    face.cond = area * perm / dist
    return face


def show(model: Seepage, jx, jy, time=None):
    """
    显示模型的压力和盐度
    Args:
        model: 渗流模型，Seepage类的对象
        jx: 单元的数量，x方向
        jy: 单元的数量，y方向
        time: 模拟的时间，单位：s
    """
    if not gui:
        return
    cells = as_numpy(model).cells
    x = np.reshape(cells.x, (jx, jy))
    y = np.reshape(cells.y, (jx, jy))
    s1 = np.reshape(as_numpy(model).fluids(0, 1).vol / as_numpy(model).fluids(0).vol, (jx, jy))
    s2 = np.reshape(as_numpy(model).fluids(0, 2).vol / as_numpy(model).fluids(0).vol, (jx, jy))

    def on_figure(fig):
        """
        用于在matplotlib中绘图的回调函数
        Args:
            fig: matplotlib.figure.Figure类的对象，用于绘图
        """
        args = [fig, add_contourf, x, y]
        opts = dict(nrows=1, ncols=2, xlabel="x/m", ylabel="y/m", aspect='equal')
        add_axes2(*args, s1, index=1, title='溶质1',
                  cbar={'label': '浓度', 'shrink': 0.7}, **opts)
        add_axes2(*args, s2, index=2, title='溶质2',
                  cbar={'label': '浓度', 'shrink': 0.7}, **opts)
        if time is not None:
            fig.suptitle(f'时间：{time2str(time)}')
        fig.tight_layout()

    # 实施绘图
    plot(on_figure, caption='溶质浓度分布')


def main():
    """
    运行测试：创建模型、运行、绘制结果
    """
    model = Seepage()

    # 定义模型的尺寸
    jx, jy = 40, 40

    # 创建SeepageMesh(并将第一个和最后一个Cell的体积设置为无穷大)
    mesh = create_cube(
        x=linspace(0, jx, jx + 1),
        y=linspace(0, jy, jy + 1),
        z=[-0.5, 0.5])

    # 辅助盐度扩散过程计算的属性
    fa_g1 = model.reg_face_key('g1')  # 盐度的传导系数
    fa_g2 = model.reg_face_key('g2')  # 盐度的传导系数

    # 添加Cell
    for c1 in mesh.cells:
        if get_distance(c1.pos, [jx * 0.3, jy * 0.3, 0]) < 3:
            s0, s1 = 0.1, 0.0
        elif get_distance(c1.pos, [jx * 0.7, jy * 0.7, 0]) < 3:
            s0, s1 = 0.0, 0.1
        else:
            s0, s1 = 0.0, 0.0
        add_cell(model, x=c1.pos[0], y=c1.pos[1], v=c1.vol, p=1.5e6, s=[s0, s1])

    # 设置扩散常数. 这里，可以尝试在一定的范围内修改此扩散系数，来观察扩散的影响效果
    # 关于沉积物中扩散系数的取值，DeepSeek的回答，供参考：
    #   https://yb.tencent.com/s/uAOnIZCnSrLa
    d1 = 1.0e-9
    d2 = d1 * 3

    # 在这些Cell之间，添加Face，用于描述流体在这些Cell之间的流动
    for f1 in mesh.faces:
        f2 = add_face(
            model, f1.cell_i0, f1.cell_i1, area=f1.area,
            perm=1.0e-15
        )
        f2.set_attr(fa_g1, f1.area * d1 / f1.dist)
        f2.set_attr(fa_g2, f1.area * d2 / f1.dist)

    diffusion.add_setting(model, flu0=[0, 1], flu1=[0], fa_g=fa_g1, cfl=0.2)
    diffusion.add_setting(model, flu0=[0, 2], flu1=[0], fa_g=fa_g2, cfl=0.2)
    model.gravity = [0, -10, 0]

    # 迭代并且绘图显示
    step_max = 100
    dt = 1.0
    time = 0.0

    for step in range(step_max):
        gui.progress(label='计算进度', val_range=[0, step_max], value=step)
        print(f'step = {step}/{step_max}, dt = {time2str(dt)}')
        time += dt

        model.iterate(dt=dt)
        dt1 = model.get_recommended_dt(previous_dt=dt, cfl=0.2)

        r = diffusion.iterate(model, dt=dt)

        dt = min(dt1, r[0].get('dt', dt), r[1].get('dt', dt), 1.0e9)
        if step % 10 == 0:
            show(model, jx, jy, time=time)

    show(model, jx, jy, time=time)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
