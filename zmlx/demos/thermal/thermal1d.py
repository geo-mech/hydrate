# 1D benchmark field of heat conduction
"""
一维热传导基准算例（半无限长杆），采用 Seepage 求解器直接求解。

物理问题：
    一个半无限长的一维杆，长度100m（x方向），截面为1m x 1m。
    初始温度分布：
        - x=0 处（左边界）：恒温 T0 = 273.15K (0摄氏度)，通过设置极大mc实现
        - 其余区域：初始温度 T1 = 373.15K (100摄氏度)
    岩体热物性参数（花岗岩）：
        - 导热系数 k = 1.69 W/(m.K)
        - 密度 rho = 2640 kg/m^3
        - 比热容 c = 754.4 J/(kg.K)
        - 热扩散率 alpha = k / (rho * c)

解析解：
    对于半无限长杆，左边界恒温 T0，初始温度 T1 的经典问题，
    温度分布满足误差函数解：
        T(x,t) = T1 + (T0 - T1) * erf(x / (2 * sqrt(alpha * t)))
    本代码使用 scipy.special.erf 计算解析解用于对比验证。

建模方式：
    采用 Seepage 底层API直接建立网格和热传导模型，
    不使用 tfc.create 等高层封装，展示最底层的热传导求解流程。
    使用 model.iterate_thermal() 直接驱动热传导迭代。

by 徐涛、张召彬
"""

from scipy.special import erf

from zmlx import *


class CellAttrs:
    """
    单元格属性索引定义。
    """
    temperature = 0  # 温度属性索引
    mc = 1           # 热容属性索引


class FaceAttrs:
    """
    面属性索引定义。
    """
    g_heat = 0  # 热传导系数属性索引


def create():
    """
    创建一维热传导模型。

    使用Seepage底层API创建网格（501个节点，x方向0~100m），
    手动设置每个单元格的温度、热容，以及每个面的导热系数。

    边界条件：
        - x=0处：恒温 T0=273.15K（通过将mc设为极大值 1e20 实现）

    返回：
        Seepage对象：初始化好的一维热传导模型
    """
    model = Seepage()
    # 创建一维网格：x方向0~100m，共501个网格
    mesh = create_cube(
        x=np.linspace(0, 100, 501),  # x方向网格节点
        y=(-0.5, 0.5),               # y方向单个网格
        z=(-0.5, 0.5)                # z方向单个网格
    )
    x0, x1 = mesh.get_pos_range(0)  # 获取x方向范围

    # 遍历所有网格，设置单元格属性
    for c in mesh.cells:
        cell = model.add_cell()
        cell.pos = c.pos
        x = c.pos[0]
        # T0 = 273.15K, T1 = 373.15K
        cell.set_attr(CellAttrs.temperature,
                      373.15 if abs(x - x0) < 1e-3 else 273.15)
        # 设置热容（mc = rho * c * vol）
        # 边界处设置极大热容以保持恒温
        cell.set_attr(CellAttrs.mc, 1.0e20 * c.vol if abs(
            x - x0) < 1e-3 else 2640 * 754.4 * c.vol)

    # 遍历所有面，设置导热系数
    for f in mesh.faces:
        # 高温高压测试结果 热导率为1.69 W/(K.m)
        face = model.add_face(model.get_cell(f.link[0]),
                              model.get_cell(f.link[1]))
        # 面导热系数 = 面积 * k / 长度
        face.set_attr(FaceAttrs.g_heat, f.area * 1.69 / f.length)

    return model


def get_theory(time):
    """
    计算指定时刻的温度分布理论解析解。

    基于一维热传导的误差函数解：
        T(x,t) = T1 + (T0 - T1) * erf(x / (2 * sqrt(alpha * t)))

    参数：
        time: 时间 [s]

    返回：
        (x, T) 元组：
            x: 位置数组 [m]
            T: 对应位置的温度数组 [K]
    """
    x = np.linspace(0, 100, 101)  # 从0到100m均匀取101个点
    T0 = 273.15        # 左边界温度 [K] (0摄氏度)
    T1 = 273.15 + 100  # 初始温度 [K] (100摄氏度)
    k = 1.69           # 导热系数 [W/(m.K)]
    rho = 2640         # 密度 [kg/m^3]
    c = 754.4          # 比热容 [J/(kg.K)]
    alpha = k / (rho * c)  # 热扩散率 [m^2/s]
    # 误差函数解析解
    T = T1 + (T0 - T1) * erf(x / (2 * np.sqrt(alpha * time)))
    return x, T


def show(model, time):
    """
    绘制数值解与解析解的对比图。

    将数值解（取每20个点显示为圆圈标记）与解析解（连续曲线）
    绘制在同一张图上，不同时间步用不同颜色区分。

    参数：
        model: Seepage对象（数值解）
        time:  当前时间 [s]
    """
    import matplotlib.pyplot as plt
    def on_figure(fig):
        # 如果是第一次绘图，初始化坐标轴
        if hasattr(fig, 'my_ax'):
            ax = fig.my_ax
            fig.my_idx += 1
        else:
            ax = add_axes2(fig)
            fig.my_ax = ax
            fig.my_idx = 0
            ax.set_xlabel('x (m)')
            ax.set_ylabel('temperature (K)')

        # 使用tab20调色板的不同颜色区分不同时间步
        c = plt.cm.tab20.colors[fig.my_idx]
        x1 = tfc.get_x(model)                     # 数值解坐标
        t1 = tfc.get_ca(model, CellAttrs.temperature)  # 数值解温度
        ax.plot(x1[::20], t1[::20], 'o', c=c)     # 每20个点画一个圆圈
        x2, t2 = get_theory(time)                 # 解析解
        ax.plot(x2, t2, c=c, label=f'{time / 3600 / 24:.0f} d')  # 解析解曲线
        ax.legend(frameon=False)                  # 显示图例

    plot(on_figure, caption='temperature', clear=False)


def solve(model):
    """
    求解一维热传导模型，并逐步绘制对比图。

    使用 model.iterate_thermal() 直接驱动热传导迭代，
    每500步（除第0步外）绘制一次数值解与解析解的对比图。

    参数：
        model: Seepage对象
    """
    dt = 200000  # 时间步长 [s] (约2.3天)
    for step in range(5000):  # 总计约31.7年
        gui.break_point()
        # 直接调用底层热传导迭代
        model.iterate_thermal(
            dt=dt,                     # 时间步长
            ca_t=CellAttrs.temperature, # 温度属性索引
            ca_mc=CellAttrs.mc,        # 热容属性索引
            fa_g=FaceAttrs.g_heat)     # 导热系数属性索引
        # 每500步绘制一次对比图
        if step % 500 == 0 and step != 0:
            show(model, time=dt * step)
            print(f'step = {step}')


def execute():
    """
    执行一维热传导基准算例的建模与求解全过程。

    先创建模型，再启动GUI求解流程，支持 --no-gui 参数以命令行模式运行。
    """
    model = create()
    gui.execute(solve, close_after_done=False, args=[model, ])


if __name__ == '__main__':
    execute()
