# ** desc = '单相流。和上一个case相比：1. 不再设置压力差；2、增加了重力效应'
#
# 【物理问题描述】
# 本模型与diffusion4（压力差+扩散）相比，不再设置外部压力差，而是增加了重力效应。
# 在30x20的二维矩形区域中，中心附近有一个初始高盐区（盐度0.5），盐的密度设为
# 2000 kg/m^3（高于水的密度1000 kg/m^3）。在重力作用下，高密度盐水会向下运移，
# 同时盐度通过分子扩散向四周传播。
#
# 【建模技术要点】
# 1. 增加了重力效应（g = [0, -10, 0]），考虑密度差驱动下的自然对流
# 2. 设置盐组分密度为2000 kg/m^3，高于水，使高盐区在重力作用下下沉
# 3. 不设外部压力差，流速完全由密度差和重力驱动
# 4. 使用add_face时显式传入dist参数（区别于之前的自动计算）
# 5. 绘制压力场和盐度场的演变
#
# 【关键参数】
# 网格大小: 30x20，单元格边长1m
# 扩散系数: 1.0e-9 m^2/s
# 渗透率: 1.0e-15 m^2
# 初始盐度: 中心区域0.5，其余0
# 盐组分密度: 2000 kg/m^3（水为1000 kg/m^3）
# 重力加速度: [0, -10, 0] m/s^2（y方向向下）
# 总模拟步数: 300步

from zmlx import *
from zmlx.tfc import diffusion


def set_cell(c: Seepage.CellData, x, y, v, p, s=0.0):
    """
    设置一个Cell的属性

    配置单元格的位置、孔隙属性和流体组分信息。每个单元格包含水（组分0）
    和盐（组分1）两个组分，其中盐组分的密度设为2000 kg/m^3。

    Args:
        c: 要设置属性的Cell对象（Seepage.CellData类型）
        x: 单元的位置，x坐标（单位：m）
        y: 单元的位置，y坐标（单位：m）
        v: 单元的体积，m3
        p: 单元的压力，Pa
        s: 盐度的比例（组分1体积占总流体体积的比例），默认为0
    """
    c.pos = [x, y, 0]
    c.set_pore(p=1e6, v=v, dp=1e6, dv=v * 0.1)
    c.fluid_number = 1
    f = c.get_fluid(0)
    f.component_number = 2  # 此流体有两个组分：水和盐
    fv = c.p2v(p)  # 根据当前压力计算流体体积
    f.get_component(0).vol = fv * (1 - s)
    f.get_component(1).den = 2000.0  # 提升盐组分的密度至2000 kg/m^3，产生重力驱动力
    f.get_component(1).vol = fv * s  # 盐的体积


def add_cell(model: Seepage, x, y, v, p, s=0.0):
    """
    在一个渗流模型中(Seepage)，添加一个流体的控制单元(Seepage.Cell)

    Args:
        model: 需要添加单元的模型，Seepage类的对象
        x: 单元的位置，x坐标（单位：m）
        y: 单元的位置，y坐标（单位：m）
        v: 单元的体积，m3
        p: 单元的压力，Pa
        s: 盐度的比例，默认为0
    """
    c = model.add_cell()
    set_cell(c, x, y, v, p, s)
    return c


def add_face(model: Seepage, i0, i1, area, dist, perm):
    """
    在一个渗流模型中(Seepage)，添加一个流体的流动面(Seepage.Face)

    与之前版本不同，此版本显式传入dist参数而非在函数内自动计算。

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
    return face


def show(model: Seepage, jx, jy, time=None):
    """
    显示模型的压力场和盐度场

    分别绘制压力云图（MPa）和盐度云图，观察重力驱动下盐度分布的变化。

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
    p = np.reshape(cells.pre / 1e6, (jx, jy))
    s = np.reshape(as_numpy(model).fluids(0, 1).vol / as_numpy(model).fluids(0).vol, (jx, jy))

    items = [
        fig.axes2(
            fig.contourf(x, y, p, cbar={'label': 'Pressure/MPa', 'shrink': 0.7}),
            xlabel="x/m", ylabel="y/m", aspect='equal', title='流体压力'
        ),
        fig.axes2(
            fig.contourf(x, y, s, cbar={'label': 'Salt Ratio', 'shrink': 0.7}, cmap='coolwarm'),
            xlabel="x/m", ylabel="y/m", aspect='equal', title='盐度'
        ),
        fig.tight_layout(),
    ]
    if time is not None:
        items.append(fig.suptitle(f'时间：{time2str(time)}'))

    fig.show(
        fig.auto_layout(
            *items
        )
    )


def main():
    """
    主函数：创建重力驱动下的盐度扩散模型并求解。

    在30x20的二维区域中，高密度盐水在重力作用下下沉，
    同时盐度向周围扩散，模拟盐水入侵等自然现象。
    """
    model = Seepage()

    # 定义模型的尺寸
    jx, jy = 30, 20

    # 创建网格（z方向厚度1m）
    mesh = create_cube(x=linspace(0, jx, jx + 1), y=linspace(0, jy, jy + 1), z=[-0.5, 0.5])

    # 注册Face属性键，用于存储扩散过程的传导系数
    fa_g = model.reg_face_key('g')  # 盐度的传导系数

    # 添加Cell：中心附近半径3范围内盐度0.5，其余为0
    for c1 in mesh.cells:
        if get_distance(c1.pos, [jx / 2, jy / 2, 0]) < 3:
            s = 0.5
        else:
            s = 0
        c = add_cell(model, x=c1.pos[0], y=c1.pos[1], v=c1.vol, p=1.5e6, s=s)

    # 添加重力（y方向向下），驱动高密度盐水向下运移
    model.gravity = [0, -10, 0]

    # 设置扩散常数
    # 关于沉积物中扩散系数的取值，DeepSeek的回答，供参考：
    #   https://yb.tencent.com/s/uAOnIZCnSrLa
    d = 1.0e-9  # 扩散系数，单位：m^2/s

    # 在这些Cell之间，添加Face，用于描述流体在这些Cell之间的流动
    for f1 in mesh.faces:
        f2 = add_face(
            model, f1.cell_i0, f1.cell_i1, area=f1.area, dist=f1.dist,
            perm=1.0e-15
        )
        # 设置扩散传导系数：g = area * d / dist
        f2.set_attr(fa_g, f1.area * d / f1.dist)

    # 添加扩散计算设置：组分1（盐）在组分0（水）中扩散
    diffusion.add_setting(model, flu0=[0, 1], flu1=[0], fa_g=fa_g, cfl=0.2)

    # 迭代并且绘图显示
    step_max = 300  # 总迭代步数
    dt = 1.0  # 初始时间步长，单位：s
    time = 0.0

    for step in range(step_max):
        gui.progress(label='计算进度', val_range=[0, step_max], value=step)
        print(f'step = {step}/{step_max}, dt = {time2str(dt)}')
        time += dt

        # 渗流迭代
        model.iterate(dt=dt)
        dt1 = model.get_recommended_dt(previous_dt=dt, cfl=0.2)

        # 扩散迭代
        diffusion.iterate(model, dt=dt, recommend_dt=True)
        dt2 = tfc.get_dt_next(model)

        # 取渗流和扩散推荐步长的较小值
        dt = min(dt1, dt2, 1.0e9)
        if step % 10 == 0:
            show(model, jx, jy, time=time)
    show(model, jx, jy, time=time)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
