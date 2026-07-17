# ** desc = '实验室尺度的co2水合物分解过程模拟 (仅供参考) 基于case_2的微调'
"""
=============================================================
CO2水合物降压分解的实验室尺度数值模拟 (case_6)
=============================================================

物理问题:
    在case_2的基础上，将甲烷水合物替换为CO2水合物。
    样品几何不变 (长0.5米，半径0.1米)。初始状态: 孔隙中含自由水
    (h2o=0.6) 和CO2水合物 (co2_hydrate=0.4)。初始温度276.15K，
    初始压力4MPa，生产压力0.3MPa，模拟时长3天。

建模技术:
    - 柱坐标系网格 + swap_yz变换
    - 虚拟生产单元实现边界控制
    - TFC热-流-化耦合求解框架
    - 通过 has_co2=True 启用CO2流体体系
    - 自适应时间步长 (dt_min=1e-4, dt_max=10)

与case_2的区别:
    - 水合物类型: CH4水合物 -> CO2水合物
    - 通过 hydrate.create_kwargs(has_co2=True) 启用CO2体系
    - CO2水合物的相平衡条件和热力学性质与CH4水合物不同
    - 展示了框架处理不同气体水合物的灵活性

关键参数:
    - 孔隙度: 0.3, 渗透率: 1.0e-14 m^2
    - 温度: 276.15K, 压力: 4MPa (初始) / 0.3MPa (生产)

物理意义:
    CO2水合物的研究在碳捕集与封存 (CCS) 领域具有重要应用。
    通过对比CH4和CO2水合物的分解行为，可评估CO2-CH4置换开采的可行性。

注意事项:
    此case不针对任何特定实验，仅用于说明实验室尺度水合物分解建模方法。
    since 2025-3-20
"""

from zmlx import *


def create():
    """
    创建并配置实验室尺度CO2水合物降压分解的数值模型。

    本函数基于case_2 (CH4水合物分解) 进行改造，将水合物类型从
    CH4水合物替换为CO2水合物。几何参数、温压条件和生产策略不变。
    展示了同一框架处理不同气体水合物类型的灵活性。

    与case_2的关键区别:
        - 通过 hydrate.create_kwargs(has_co2=True) 启用CO2流体体系
        - 初始水合物饱和度: co2_hydrate=0.4 (而非 ch4_hydrate)
        - CO2水合物的相平衡曲线和热力学参数与CH4水合物不同

    参数:
        无 (所有参数在函数内部定义)

    返回:
        model (tfc.Model): 配置完成的TFC耦合模型对象

    注意:
        - CO2水合物在相同温压条件下比CH4水合物更稳定
        - 该模型可用于对比分析CO2和CH4水合物分解行为的差异
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

    # 定义初始饱和度: 虚拟单元全水，其余单元含水0.6 + CO2水合物0.4
    def get_s(x, y, z):
        if is_prod(x, y, z):
            return {'h2o': 1}
        else:
            return {'h2o': 0.6, 'co2_hydrate': 0.4}

    # 定义密度/渗透率乘数: 顶部边界不透，内部正常值5e6
    def denc(*pos):
        return 1e20 if is_upper(*pos) else 5e6

    # 定义热导率: 确保不会有热量通过用于生产的虚拟的cell传递过来.
    def heat_cond(x, y, z):
        return 1.0 if abs(y) < 2 else 0.0

    # 组装水合物模拟的关键字参数
    kw = hydrate.create_kwargs(
        has_co2=True,            # 启用CO2流体体系 (区别于CH4体系)
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
        s=get_s,                  # 初始饱和度函数 (含CO2水合物)
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
              'time_max': 3 * 24 * 3600,           # 最大模拟时间: 3天
              }
    )
    # 返回模型
    return model


if __name__ == '__main__':
    # 创建并求解模型 (GUI窗口保持打开)
    gui.execute(lambda: tfc.solve(create()), close_after_done=False)
