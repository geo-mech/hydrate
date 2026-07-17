# ** desc = '单相的流动。在单相的基础上，添加了盐度组分的扩散效应'
#
# 【物理问题描述】
# 本模型模拟两种不同溶质在孔隙水中的扩散过程。流体包含三个组分：水（组分0）、
# 溶质A（组分1）和溶质B（组分2）。初始时刻，两种溶质分别位于不同位置：
# 溶质A在左下(0.3,0.3)附近（浓度0.1），溶质B在右上(0.7,0.7)附近（浓度0.1）。
# 两种溶质具有不同的扩散系数（d1=1.0e-9, d2=2.0e-9），扩散速率不同。
# 另外还考虑了重力效应（g=[0,-10,0]），模拟垂向密度分层。
#
# 【建模技术要点】
# 1. 每个流体的组分数量为3（水 + 两种溶质）
# 2. 使用diffusion.add_setting分别为每种溶质添加独立的扩散设置
# 3. 两种溶质的扩散系数不同，可以对比扩散速率的差异
# 4. 设置了重力加速度，考虑密度差异引起的重力分异
# 5. 使用fa_s（面积）和fa_l（距离）属性，而非预计算的传导系数g
#    diffusion模块可通过d * area / dist自动计算传导系数
#
# 【关键参数】
# 网格大小: 40x40，单元格边长1m
# 扩散系数: 溶质A=1.0e-9 m^2/s，溶质B=2.0e-9 m^2/s
# 初始浓度: 溶质A位于(0.3,0.3)附近0.1，溶质B位于(0.7,0.7)附近0.1
# CFL数: 0.2
# 重力加速度: [0, -10, 0] m/s^2（y方向向下）

from zmlx import *


def set_cell(c: Seepage.CellData, x, y, v, p, s=None):
    """
    设置一个Cell的属性

    每个单元格包含一种流体，该流体有三个组分：水（组分0）、溶质A（组分1）和溶质B（组分2）。
    溶质浓度由各自的体积分数定义。

    Args:
        c: 要设置属性的Cell对象（Seepage.CellData类型）
        x: 单元的位置，x坐标（单位：m），若为None则不设置位置
        y: 单元的位置，y坐标（单位：m），若为None则不设置位置
        v: 单元的体积，m3
        p: 单元的压力，Pa
        s: 两种溶质的浓度列表[s0, s1]，默认为None（等价于[0.0, 0.0]）
    """
    if x is not None and y is not None:
        c.pos = [x, y, 0]
    c.set_pore(p=1e6, v=v, dp=1e6, dv=v * 0.1)
    c.fluid_number = 1
    f = c.get_fluid(0)
    f.component_number = 3  # 此流体有3个组分：水、溶质A、溶质B
    fv = c.p2v(p)  # 根据当前压力计算流体体积
    if s is None:
        s = [0.0, 0.0]
    f.get_component(0).vol = fv * (1 - s[0] - s[1])  # 水的体积
    f.get_component(1).vol = fv * s[0]  # 溶质A的体积
    f.get_component(2).vol = fv * s[1]  # 溶质B的体积


def add_cell(model: Seepage, x, y, v, p, s=None):
    """
    在一个渗流模型中(Seepage)，添加一个流体的控制单元(Seepage.Cell)

    Args:
        model: 需要添加单元的模型，Seepage类的对象
        x: 单元的位置，x坐标（单位：m）
        y: 单元的位置，y坐标（单位：m）
        v: 单元的体积，m3
        p: 单元的压力，Pa
        s: 两种溶质的浓度列表，默认为None
    """
    c = model.add_cell()
    set_cell(c, x, y, v, p, s)
    return c


def add_face(model: Seepage, i0, i1, area, perm):
    """
    在一个渗流模型中(Seepage)，添加一个流体的流动面(Seepage.Face)

    根据单元间距离计算流动传导系数。

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
    显示两种溶质的浓度分布

    分别绘制溶质A（组分1）和溶质B（组分2）的浓度云图，便于对比两种
    扩散速率不同的溶质在相同时间内的扩散范围差异。

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
    # 计算溶质A浓度
    s1 = np.reshape(as_numpy(model).fluids(0, 1).vol / as_numpy(model).fluids(0).vol, (jx, jy))
    # 计算溶质B浓度
    s2 = np.reshape(as_numpy(model).fluids(0, 2).vol / as_numpy(model).fluids(0).vol, (jx, jy))
    fig.show(
        fig.auto_layout(
            fig.axes2(
                fig.contourf(
                    x, y, s1, cbar={'label': '浓度', 'shrink': 0.7}, cmap='coolwarm'
                ),
                xlabel="x/m", ylabel="y/m", aspect='equal'
            ),
            fig.axes2(
                fig.contourf(
                    x, y, s2, cbar={'label': '浓度', 'shrink': 0.7}, cmap='coolwarm'
                ),
                xlabel="x/m", ylabel="y/m", aspect='equal'
            ),
            fig.tight_layout(),
            fig.suptitle(f'时间：{time2str(time)}'),
        ),
        caption='溶质浓度分布'
    )


def main():
    """
    主函数：创建双溶质扩散模型并求解。

    在40x40的二维区域中，两种不同扩散速率的溶质分别位于不同位置，
    模拟它们各自扩散的过程，展示扩散系数差异对传输距离的影响。
    """
    model = Seepage()

    # 定义模型的尺寸
    jx, jy = 40, 40

    # 创建网格（z方向厚度1m）
    mesh = create_cube(
        x=linspace(0, jx, jx + 1),
        y=linspace(0, jy, jy + 1),
        z=[-0.5, 0.5])

    # 注册Face属性键，分别存储面积和距离信息供扩散模块使用
    fa_s = model.reg_face_key('area')   # 流动横截面积
    fa_l = model.reg_face_key('length') # 单元间距离

    # 添加Cell：溶质A在左下(0.3,0.3)附近，溶质B在右上(0.7,0.7)附近
    for c1 in mesh.cells:
        if get_distance(c1.pos, [jx * 0.3, jy * 0.3, 0]) < 3:
            s0, s1 = 0.1, 0.0  # 仅溶质A浓度为0.1
        elif get_distance(c1.pos, [jx * 0.7, jy * 0.7, 0]) < 3:
            s0, s1 = 0.0, 0.1  # 仅溶质B浓度为0.1
        else:
            s0, s1 = 0.0, 0.0
        add_cell(model, x=c1.pos[0], y=c1.pos[1], v=c1.vol, p=1.5e6, s=[s0, s1])

    # 设置扩散常数. 这里，可以尝试在一定的范围内修改此扩散系数，来观察扩散的影响效果
    # 关于沉积物中扩散系数的取值，DeepSeek的回答，供参考：
    #   https://yb.tencent.com/s/uAOnIZCnSrLa
    d1 = 1.0e-9  # 溶质A的扩散系数，单位：m^2/s
    d2 = d1 * 2  # 溶质B的扩散系数是A的两倍，扩散更快

    # 在这些Cell之间，添加Face，用于描述流体在这些Cell之间的流动
    for f1 in mesh.faces:
        f2 = add_face(
            model, f1.cell_i0, f1.cell_i1, area=f1.area,
            perm=1.0e-15
        )
        f2.set_attr(fa_s, f1.area)  # 存储Face的横截面积
        f2.set_attr(fa_l, f1.dist)  # 存储Face对应的单元间距离

    # 分别为两种溶质添加扩散设置（使用不同的扩散系数）
    diffusion.add_setting(model, flu0=[0, 1], flu1=[0], d=d1, cfl=0.2)  # 溶质A
    diffusion.add_setting(model, flu0=[0, 2], flu1=[0], d=d2, cfl=0.2)  # 溶质B
    # 添加重力效应（y方向向下），考虑密度差异引起的分层
    model.gravity = [0, -10, 0]

    # 迭代并且绘图显示
    step_max = 100  # 总迭代步数
    dt = 1.0  # 初始时间步长，单位：s
    time = 0.0

    for step in range(step_max):
        gui.progress(label='计算进度', val_range=[0, step_max], value=step)
        print(f'step = {step}/{step_max}, dt = {time2str(dt)}')
        time += dt

        # 渗流迭代
        model.iterate(dt=dt)
        dt1 = model.get_recommended_dt(previous_dt=dt, cfl=0.2)

        # 扩散迭代（两种溶质同时扩散）
        diffusion.iterate(model, dt=dt, recommend_dt=True)
        dt2 = tfc.get_dt_next(model)

        # 取建议步长最小值
        dt = min(dt1, dt2, 1.0e9)
        if step % 10 == 0:
            show(model, jx, jy, time=time)

    show(model, jx, jy, time=time)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
