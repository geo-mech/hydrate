# ** desc = '单相的流动。添加了压力差和扩散，两者同时起作用'
#
# 【物理问题描述】
# 本模型模拟单相渗流与溶质扩散同时存在的情况。在40x40的二维区域中，
# 中心附近有一个初始高盐区（盐度0.1），同时模型对角位置存在压力差
# （左上角(0,0)压力高于右下角(40,40)）驱动流体流动。因此盐度同时受
# 扩散作用（由浓度梯度驱动）和对流传输（由压力梯度驱动）的影响。
#
# 【建模技术要点】
# 1. 扩散与渗流同步作用：通过大体积Cell设置固定压力边界产生对流
# 2. 扩散设置通过fa_g（扩散传导系数）实现
# 3. 使用tfc.iterate_flow（而非model.iterate）处理渗流迭代
# 4. 使用tfc.set_dt_max限制最大时间步长
# 5. 同时显示压力场和盐度场的演变
#
# 【关键参数】
# 网格大小: 40x40，单元格边长1m
# 压力差: 0.3e6 Pa（左上角1.65MPa，右下角1.35MPa）
# 扩散系数: 1.0e-9 m^2/s
# 渗透率: 1.0e-15 m^2
# 总模拟步数: 300步

from zmlx import *


def set_cell(c: Seepage.CellData, x, y, v, p, s=0.0):
    """
    设置一个Cell的属性

    配置单元格的位置、孔隙属性和流体组分信息。每个单元格包含水和盐两个组分。

    Args:
        c: 要设置属性的Cell对象（Seepage.CellData类型）
        x: 单元的位置，x坐标（单位：m），若为None则不设置位置
        y: 单元的位置，y坐标（单位：m），若为None则不设置位置
        v: 单元的体积，m3
        p: 单元的压力，Pa
        s: 盐度的比例（组分1体积占总流体体积的比例），默认为0
    """
    if x is not None and y is not None:
        c.pos = [x, y, 0]
    c.set_pore(p=1e6, v=v, dp=1e6, dv=v * 0.1)
    c.fluid_number = 1
    f = c.get_fluid(0)
    f.component_number = 2  # 此流体有两个组分：水和盐
    fv = c.p2v(p)  # 根据当前压力计算流体体积
    f.get_component(0).vol = fv * (1 - s)
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
    显示模型的压力场和盐度场

    绘制两个子图：（1）压力分布云图（MPa）；（2）盐度分布云图。

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

    fig.show(
        fig.auto_layout(
            fig.axes2(
                fig.contourf(x, y, p, cbar={'label': 'Pressure/MPa', 'shrink': 0.7}),
                xlabel="x/m", ylabel="y/m", aspect='equal', title='流体压力'
            ),
            fig.axes2(
                fig.contourf(x, y, s, cbar={'label': 'Salt Ratio', 'shrink': 0.7}, cmap='coolwarm'),
                xlabel="x/m", ylabel="y/m", aspect='equal', title='盐度'
            ),
        ),
        fig.suptitle(f'时间：{time2str(time)}'),
        fig.tight_layout(),
        caption='压力和盐度分布',
    )


def main():
    """
    主函数：创建对流-扩散耦合模型并求解。

    在40x40二维区域中，同时存在压力梯度驱动的对流传质和浓度梯度
    驱动的分子扩散，模拟盐度在两种输运机制共同作用下的时空演变。
    """
    model = Seepage()

    # 定义模型的尺寸
    jx, jy = 40, 40

    # 创建SeepageMesh网格（z方向厚度1m）
    mesh = create_cube(
        x=linspace(0, jx, jx + 1),
        y=linspace(0, jy, jy + 1),
        z=[-0.5, 0.5])

    # 注册Face属性键，用于存储扩散过程的传导系数
    fa_g = model.reg_face_key('g')

    # 添加Cell：中心附近半径3范围内盐度0.1，其余为0
    for c1 in mesh.cells:
        if get_distance(c1.pos, [jx / 2, jy / 2, 0]) < 3:
            s = 0.1
        else:
            s = 0
        add_cell(model, x=c1.pos[0], y=c1.pos[1], v=c1.vol, p=1.5e6, s=s)

    # 设置对角压力差，产生定向流动
    d_pre = 0.3e6  # 压力差异 (Pa)，确保小于2e6以避免负孔隙体积
    assert d_pre < 2e6
    # 在左上角(0,0)设置固定高压边界（体积极大，维持压力不变）
    c = model.get_nearest_cell(pos=[0, 0, 0])
    set_cell(c, x=None, y=None, v=1e6, p=1.5e6 + d_pre * 0.5, s=0)
    # 在右下角(40,40)设置固定低压边界（体积极大，维持压力不变）
    c = model.get_nearest_cell(pos=[jx, jy, 0])
    set_cell(c, x=None, y=None, v=1e6, p=1.5e6 - d_pre * 0.5, s=0)

    # 设置扩散常数. 这里，可以尝试在一定的范围内修改此扩散系数，来观察扩散的影响效果
    # 关于沉积物中扩散系数的取值，DeepSeek的回答，供参考：
    #   https://yb.tencent.com/s/uAOnIZCnSrLa
    d = 1.0e-9  # 扩散系数，单位：m^2/s

    # 在这些Cell之间，添加Face，用于描述流体在这些Cell之间的流动
    for f1 in mesh.faces:
        f2 = add_face(
            model, f1.cell_i0, f1.cell_i1, area=f1.area,
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
    tfc.set_dt_max(model, 1.0e9)  # 设置最大时间步长限制

    for step in range(step_max):
        gui.progress(label='计算进度', val_range=[0, step_max], value=step)
        print(f'step = {step}/{step_max}, dt = {time2str(dt)}')
        time += dt

        # 渗流迭代（使用tfc引擎，自动推荐步长）
        tfc.iterate_flow(model, dt=dt, recommend_dt=True, cfl=0.2)
        # 扩散迭代
        diffusion.iterate(model, dt=dt, recommend_dt=True)
        # 获取推荐步长
        dt = tfc.get_dt_next(model)
        if step % 10 == 0:
            show(model, jx, jy, time=time)
    show(model, jx, jy, time=time)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
