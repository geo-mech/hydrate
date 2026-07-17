# ** desc = '单相的流动。在单相的基础上，添加了盐度组分的扩散效应'
#
# 【物理问题描述】
# 本模型在单相流体渗流的基础上，添加了盐度（溶质）组分的扩散过程。在40x40的二维
# 正方形区域中，初始时刻在中心附近（半径3范围内）存在一个盐度0.1的高盐区，其余
# 区域盐度为0。随着时间推移，盐度通过分子扩散作用逐渐向四周传播。
#
# 【建模技术要点】
# 1. 基于Seepage底层API手动构建模型，每个Cell包含一个流体（水）和两个组分（水和盐）
# 2. 组分0代表纯水，组分1代表盐，盐度定义为组分1体积与总体积之比
# 3. 使用Face上的自定义属性（'g'）存储扩散传导系数，计算公式：g = area * d / dist
# 4. 调用diffusion.add_setting和diffusion.iterate进行扩散过程的计算
# 5. 扩散计算与达西流动计算交替进行（先渗流后扩散），时间步取两者最小值
# 6. Cell体积不变（不设大体积边界），因此所有单元压力会缓慢均衡
#
# 【关键参数】
# 网格大小: 40x40，单元格边长1m
# 渗透率: 1.0e-15 m^2
# 扩散系数: 1.0e-9 m^2/s（沉积物中典型溶质扩散系数）
# 初始压力: 1.5MPa
# 初始盐度: 中心区域0.1，其余0
# 总模拟步数: 100步，每步步长1s

from zmlx import *


def set_cell(c: Seepage.CellData, x, y, v, p, s=0.0):
    """
    设置一个Cell的属性

    该函数配置单个单元格的位置、孔隙属性、流体及组分信息。
    每个单元格包含一种流体（水），该流体包含两个组分：
    组分0（纯水）和组分1（盐），盐度由组分1的体积分数定义。

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
    # 设置孔隙属性：参考压力1MPa，参考体积v，体积模量由dp/dv定义
    c.set_pore(p=1e6, v=v, dp=1e6, dv=v * 0.1)
    c.fluid_number = 1  # 每个单元格包含一种流体
    f = c.get_fluid(0)
    f.component_number = 2  # 此流体有两个组分：水（组分0）和盐（组分1）
    fv = c.p2v(p)  # 根据当前压力计算流体所占的孔隙体积
    f.get_component(0).vol = fv * (1 - s)  # 纯水的体积
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

    根据两个单元之间的距离和渗透率计算流动传导系数。

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
    显示模型的盐度分布

    根据网格形状将一维数据重塑为二维数组，绘制盐度（组分1体积分数）的云图。

    Args:
        model: 渗流模型，Seepage类的对象
        jx: 单元的数量，x方向
        jy: 单元的数量，y方向
        time: 模拟的时间，单位：s（用于标题显示）
    """
    if not gui:
        return
    cells = as_numpy(model).cells
    x = np.reshape(cells.x, (jx, jy))
    y = np.reshape(cells.y, (jx, jy))
    # 计算盐度：组分1体积 / 总流体体积
    s = np.reshape(as_numpy(model).fluids(0, 1).vol / as_numpy(model).fluids(0).vol, (jx, jy))

    fig.show(
        fig.axes2(
            fig.contourf(x, y, s, cbar={'label': 'Salt Ratio', 'shrink': 0.7}, cmap='coolwarm'),
            title=f'盐度. 时间={time2str(time)}',
            xlabel="x/m", ylabel="y/m", aspect='equal'
        ),
        fig.tight_layout(),
        caption='盐度分布'
    )


def main():
    """
    主函数：创建带溶质扩散的单相渗流模型并求解。

    构建40x40的二维模型，中心区域初始有高盐度（0.1），
    模拟渗流和盐度扩散的耦合过程，每10步显示一次盐度分布。
    """
    model = Seepage()

    # 定义模型的尺寸
    jx, jy = 40, 40

    # 创建SeepageMesh网格（z方向厚度1m）
    mesh = create_cube(
        x=linspace(0, jx, jx + 1),
        y=linspace(0, jy, jy + 1),
        z=[-0.5, 0.5])

    # 注册Face属性键，用于存储扩散过程中的传导系数
    fa_g = model.reg_face_key('g')

    # 添加Cell：中心半径3范围内盐度0.1，其余区域盐度为0
    for c1 in mesh.cells:
        if get_distance(c1.pos, [jx / 2, jy / 2, 0]) < 3:
            s = 0.1
        else:
            s = 0
        add_cell(model, x=c1.pos[0], y=c1.pos[1], v=c1.vol, p=1.5e6, s=s)

    # 设置扩散常数
    # 关于沉积物中扩散系数的取值，DeepSeek的回答，供参考：
    #   https://yb.tencent.com/s/uAOnIZCnSrLa
    d = 1.0e-9  # 扩散系数，单位：m^2/s

    # 在这些Cell之间，添加Face，用于描述流体在这些Cell之间的流动
    for f1 in mesh.faces:
        f2 = add_face(
            model, f1.cell_i0, f1.cell_i1, area=f1.area,
            perm=1.0e-15
        )
        # 设置扩散传导系数：g = area * d / dist（类比达西传导系数）
        f2.set_attr(fa_g, f1.area * d / f1.dist)

    # 添加扩散计算设置：组分1（盐）在组分0（水）中扩散
    diffusion.add_setting(model, flu0=[0, 1], flu1=[0], fa_g=fa_g, cfl=0.2)

    # 迭代并且绘图显示
    step_max = 100  # 总迭代步数
    dt = 1.0  # 初始时间步长，单位：s
    time = 0.0

    for step in range(step_max):
        gui.progress(label='计算进度', val_range=[0, step_max], value=step)
        print(f'step = {step}/{step_max}, dt = {time2str(dt)}')
        time += dt

        # 渗流迭代（达西流动）
        model.iterate(dt=dt)
        dt1 = model.get_recommended_dt(previous_dt=dt, cfl=0.1)

        # 扩散迭代（溶质扩散）
        diffusion.iterate(model, dt=dt, recommend_dt=True)
        dt2 = tfc.get_dt_next(model)

        # 取渗流和扩散推荐步长中的较小值作为下一步长
        dt = min(dt1, dt2, 1.0e9)
        if step % 10 == 0:
            show(model, jx, jy, time=time)
    show(model, jx, jy, time=time)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
