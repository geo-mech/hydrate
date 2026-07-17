# ** desc = '单相的流动。在单相的基础上，添加了盐度组分的扩散效应'
#
# 【物理问题描述】
# 本模型与diffusion1类似，但初始盐度分布不同：在40x40的二维正方形区域中，
# 存在两个高盐区（盐度0.1），分别位于左下角（0.3, 0.3）和右上角（0.7, 0.7）
# 附近（半径3范围内），其余区域盐度为0。模拟显示两个高盐斑块同时向外扩散的过程。
#
# 【建模技术要点】
# 1. 与diffusion1相同的技术框架：Seepage底层API + 两个组分（水和盐）
# 2. 初始盐度的空间分布不同，展示两个独立源项的扩散及可能的重叠
# 3. 使用diffusion.add_setting和diffusion.iterate处理扩散过程
# 4. 渗流和扩散交替迭代，时间步取两者推荐步长的最小值
#
# 【关键参数】
# 网格大小: 40x40，单元格边长1m
# 扩散系数: 1.0e-9 m^2/s
# 初始盐度: 两个位置（0.3,0.3）和（0.7,0.7）附近为0.1，其余为0
# CFL数: 0.2（扩散计算）

from zmlx import *


def set_cell(c: Seepage.CellData, x, y, v, p, s=0.0):
    """
    设置一个Cell的属性

    配置单元格的位置、孔隙属性和流体组分信息。
    每个流体单元包含两个组分：组分0（纯水）和组分1（盐）。

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
    # 设置孔隙属性：参考压力1MPa，参考体积v，压力变化范围1MPa对应体积变化0.1*v
    c.set_pore(p=1e6, v=v, dp=1e6, dv=v * 0.1)
    c.fluid_number = 1
    f = c.get_fluid(0)
    f.component_number = 2  # 此流体有两个组分：水（组分0）和盐（组分1）
    fv = c.p2v(p)  # 根据当前压力和孔隙压缩性计算流体体积
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
    显示模型的盐度分布

    将模型数据重塑为二维数组，绘制盐度云图。

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
    # 计算盐度：组分1体积 / 总流体体积
    s = np.reshape(as_numpy(model).fluids(0, 1).vol / as_numpy(model).fluids(0).vol, (jx, jy))

    # 实施绘图
    fig.show(
        fig.axes2(
            fig.contourf(
                x, y, s, cmap='coolwarm',
                cbar={'label': 'Salt Ratio', 'shrink': 0.7},
            ),
            title=f'盐度. 时间={time2str(time)}', xlabel="x/m", ylabel="y/m",
            aspect='equal'
        ),
        fig.tight_layout(),
        caption='盐度分布'
    )


def main():
    """
    主函数：创建两个扩散源的盐度扩散模型并求解。

    模型在40x40区域内设置两个初始高盐度斑块，模拟盐度在孔隙水中的
    扩散过程，观察两个扩散源各自的演变及相互影响。
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
    fa_g = model.reg_face_key('g')  # 盐度的传导系数

    # 添加Cell：左下(0.3,0.3)和右上(0.7,0.7)附近半径3范围内盐度0.1，其余为0
    for c1 in mesh.cells:
        # 判断是否在任意一个高盐区附近
        if get_distance(c1.pos, [jx * 0.3, jy * 0.3, 0]) < 3 or get_distance(c1.pos, [jx * 0.7, jy * 0.7, 0]) < 3:
            s = 0.1
        else:
            s = 0
        add_cell(model, x=c1.pos[0], y=c1.pos[1], v=c1.vol, p=1.5e6, s=s)

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
