# ** desc = '实验室尺度的水合物分解过程模拟 (仅供参考)'
"""
=============================================================
CH4水合物降压分解的实验室尺度数值模拟 (case_3 - 气相饱和条件)
=============================================================

物理问题:
    在case_2的基础上，将初始孔隙流体由水饱和改为甲烷气饱和。
    样品几何不变 (长0.5米，半径0.1米)。初始状态: 孔隙中充满甲烷气
    (ch4=0.6) 和甲烷水合物 (ch4_hydrate=0.4)，无自由水相。
    初始温度276.15K，初始压力4MPa，生产压力0.3MPa，模拟时长3天。

建模技术:
    - 柱坐标系网格 + swap_yz变换
    - 虚拟生产单元实现边界控制
    - TFC热-流-化耦合求解框架
    - 自适应时间步长 (dt_min=1e-4, dt_max=10)

与case_2的区别:
    - 初始饱和度: {h2o: 0.6, ch4_hydrate: 0.4} -> {ch4: 0.6, ch4_hydrate: 0.4}
    - 孔隙中无水相存在，仅为气相和水合物相
    - 该条件模拟气藏中水合物分解的初期行为

关键参数:
    - 孔隙度: 0.3, 渗透率: 1.0e-14 m^2
    - 温度: 276.15K (3°C), 压力: 4MPa

物理意义:
    模拟不含自由水的含气水合物储层在降压过程中的分解行为，
    考察气相饱和度对分解速率和传热传质的影响。

注意事项:
    此case不针对任何特定实验，仅用于说明实验室尺度水合物分解建模方法。
    since 2025-2-6
"""

from zmlx import *


def create():
    """
    创建并配置实验室尺度CH4水合物降压分解的数值模型 (气相饱和条件)。

    本函数与 case_2 结构相同，但初始饱和度改为甲烷气饱和而非水饱和:
        - 初始: ch4=0.6, ch4_hydrate=0.4 (孔隙中无自由水相)
        - 展示框架处理不同初始流体分布的能力
        - 模拟气藏中不含自由水情况下的水合物分解行为

    参数:
        无 (所有参数在函数内部定义)

    返回:
        model (tfc.Model): 配置完成的TFC耦合模型对象

    注意:
        - 气相饱和条件下，水合物分解后释放的气体可自由流动
        - 由于无水相存在，相对渗透率行为和毛细管压力与水饱和情况不同
        - 该场景对应于低含水饱和度的天然气水合物藏
    """
    # 创建柱坐标系网格: 轴向50等分 (0~0.5m), 径向10等分 (0~0.1m)
    mesh = create_cylinder(x=np.linspace(0, 0.5, 50),
                           r=np.linspace(0, 0.1, 10))
    # 交换Y和Z轴坐标，使柱体轴向与Z方向对齐
    swap_yz(mesh)

    # 添加虚拟的cell和face用于生产 (大体积/面积以减小局部流动阻力)
    add_cell_face(mesh, pos=[0, 0, 0], offset=[0, 10, 0], vol=1000,
                  area=5, length=1)

    # 找到上下范围，从而去找到顶底的边界
    z_min, z_max = mesh.get_pos_range(2)

    # 判断是否为顶部边界 (Z方向最大处)
    def is_upper(x, y, z):
        return abs(z - z_max) < 0.0001

    # 判断是否为生产虚拟单元 (Y方向偏移10m处)
    def is_prod(x, y, z):
        return abs(y - 10) < 0.1

    # 定义初始饱和度: 虚拟单元全水，其余单元为甲烷气0.6 + 水合物0.4 (无水相)
    def get_s(x, y, z):
        if is_prod(x, y, z):
            return {'h2o': 1}
        else:
            return {'ch4': 0.6, 'ch4_hydrate': 0.4}

    # 定义密度/渗透率乘数: 顶部边界不透，内部正常值5e6
    def denc(*pos):
        return 1e20 if is_upper(*pos) else 5e6

    # 定义热导率: 确保不会有热量通过用于生产的虚拟的cell传递过来.
    def heat_cond(x, y, z):
        return 1.0 if abs(y) < 2 else 0.0

    # 组装水合物模拟的关键字参数
    kw = hydrate.create_kwargs(
        gravity=[0, 0, 0],       # 忽略重力影响
        dt_min=1.0e-4,           # 最小时间步长 (秒)
        dt_max=10,               # 最大时间步长 (秒)
        cfl=0.1,         # 体积变化相对容差
        mesh=mesh,                # 网格对象
        porosity=0.3,             # 孔隙度
        pore_modulus=100e6,       # 孔隙模量 (Pa)
        denc=denc,                # 密度/渗透率乘数函数
        temperature=273.15 + 3.0, # 初始温度 (K) = 3°C
        p=4e6,                    # 初始压力 (Pa) = 4 MPa
        s=get_s,                  # 初始饱和度函数 (气相饱和)
        perm=1.0e-14,             # 绝对渗透率 (m^2) ≈ 10 mD
        dist=0.001,               # 裂隙/网格特征尺度 (m)
        heat_cond=heat_cond,      # 热导率函数
        prods=[{'index': -1,      # 生产井: 连接最后一个单元
                't': [0, 1e20],   # 从0时刻到无穷大持续生产
                'p': [0.3e6, 0.3e6]}]  # 恒定生产压力 0.3 MPa
    )
    # 创建TFC耦合模型 (忽略重力相关警告)
    model = tfc.create(**kw,
                       warnings_ignored={'gravity'})

    # 配置求解器选项
    model.set_text(
        key='solve',
        text={'monitor': {'cell_ids': [model.cell_number - 1]},  # 监控虚拟生产单元的状态
              'show_cells': {'dim0': 0,           # 沿轴向显示剖面
                             'dim1': 2,            # 沿Z方向显示剖面
                             'mask': tfc.get_cell_mask(
                                 model=model, yr=[-1, 1])},  # Y∈[-1,1]范围内的单元格
              'time_max': 24 * 3600 * 3,           # 最大模拟时间: 3天
              }
    )

    # 返回模型
    return model


if __name__ == '__main__':
    # 创建并求解模型 (GUI窗口保持打开)
    gui.execute(lambda: tfc.solve(create()), close_after_done=False)
