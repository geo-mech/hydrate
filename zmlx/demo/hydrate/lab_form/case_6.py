# ** desc = '实验室尺度的co2水合物合成过程模拟 (仅供参考) '
"""
=============================================================
CO2水合物合成的实验室尺度数值模拟 (case_6)
=============================================================

物理问题:
    在case_2 (CH4水合物合成) 的基础上，将注入气体从甲烷替换为CO2。
    样品几何不变 (长0.5米，半径0.1米)。初始状态: 孔隙中含自由水
    (h2o=0.6) 和CO2气体 (co2=0.4)。温度276.15K，初始压力1MPa。
    以1.0e-6 m^3/s的速率持续注入CO2气体，驱动CO2水合物生成反应。
    总模拟时长10小时。

建模技术:
    - 柱坐标系网格 (create_cylinder) + swap_yz坐标变换
    - TFC热-流-化耦合求解框架
    - 通过 has_co2=True 启用CO2流体体系和对应的水合物相平衡
    - 注入CO2气体，流体类型为 'insitu' (就地流体)
    - 自适应时间步长: dt_min=1e-4, dt_max=10

与case_2 (CH4合成) 的区别:
    - 注入气体: CH4 -> CO2
    - 初始气相: ch4=0.4 -> co2=0.4
    - 通过 has_co2=True 启用CO2体系
    - CO2水合物的生成条件与CH4水合物不同

关键参数:
    - 孔隙度: 0.3, 渗透率: 1.0e-14 m^2
    - 温度: 276.15K (3°C), 压力: 1MPa
    - 注入速率: 1.0e-6 m^3/s (CO2气体)

物理意义:
    CO2水合物合成在碳捕集与封存 (CCS)、海水淡化和蓄冷技术等领域
    具有广阔的应用前景。通过CO2水合物生成，可将CO2以固体形式固定在
    沉积物孔隙中，实现永久封存。

注意事项:
    此case不针对任何特定实验，仅用于说明实验室尺度水合物合成建模方法。
"""

from zmlx import *


def create():
    """
    创建并配置实验室尺度CO2水合物合成的数值模型。

    本函数基于 lab_form/case_2.py (CH4水合物合成) 改造而来，
    将注入气体从甲烷替换为CO2。通过 has_co2=True 启用CO2流体体系。
    展示了同一框架处理不同气体水合物合成的灵活性。

    与case_2 (CH4合成) 的关键区别:
        - 注入流体: CH4 -> CO2
        - 初始气相: ch4=0.4 -> co2=0.4
        - 通过 has_co2=True 启用CO2体系和相平衡

    参数:
        无 (所有参数在函数内部定义)

    返回:
        model (tfc.Model): 配置完成的TFC耦合模型对象

    注意:
        - CO2水合物的生成条件 (相平衡温度-压力) 与CH4水合物不同
        - 在相同温压条件下，CO2水合物更易生成 (相平衡温度更高)
        - 该模型可用于研究CO2地质封存中的水合物生成行为
    """
    # 创建柱坐标系网格: 轴向50等分 (0~0.5m), 径向10等分 (0~0.1m)
    mesh = create_cylinder(x=np.linspace(0, 0.5, 50),
                           r=np.linspace(0, 0.1, 10))
    # 交换Y和Z轴坐标，使柱体轴向与Z方向对齐
    swap_yz(mesh)

    # 找到上下范围，从而去找到顶底的边界
    z_min, z_max = mesh.get_pos_range(2)

    # 判断是否为顶部边界 (Z方向最大处)
    def is_upper(x, y, z):
        return abs(z - z_max) < 0.0001

    # 定义初始饱和度: 孔隙中含水0.6 + CO2气体0.4 (CO2水合物生成的前驱状态)
    def get_s(x, y, z):
        return {'h2o': 0.6, 'co2': 0.4}

    # 定义密度/渗透率乘数: 顶部边界不透，内部正常值5e6
    def denc(*pos):
        return 1e20 if is_upper(*pos) else 5e6

    # 定义热导率函数 (保留与分解模拟一致的接口)
    def heat_cond(x, y, z):
        return 1.0 if abs(y) < 2 else 0.0

    # 组装水合物模拟的关键字参数
    kw = hydrate.create_kwargs(
        has_co2=True,            # 启用CO2流体体系 (区别于CH4体系)
        gravity=[0, 0, 0],       # 忽略重力影响
        dt_min=1.0e-4,           # 最小时间步长 (秒)
        dt_max=10,               # 最大时间步长 (秒)
        cfl=1,           # 体积变化相对容差 (适应注入导致的体积膨胀)
        mesh=mesh,                # 网格对象
        porosity=0.3,             # 孔隙度
        pore_modulus=100e6,       # 孔隙模量 (Pa)
        denc=denc,                # 密度/渗透率乘数函数
        temperature=273.15 + 3.0, # 初始温度 (K) = 3°C
        p=1e6,                    # 初始压力 (Pa) = 1 MPa
        s=get_s,                  # 初始饱和度函数 (含CO2气体)
        perm=1.0e-14,             # 绝对渗透率 (m^2) ≈ 10 mD
        dist=0.001,               # 裂隙/网格特征尺度 (m)
        heat_cond=heat_cond,      # 热导率函数
    )
    # 创建TFC耦合模型 (忽略重力相关警告)
    model = tfc.create(**kw,
                       warnings_ignored={'gravity'})

    # 添加注气井: 持续注入CO2气体驱动CO2水合物生成
    tfc.add_injector(
        model, data=dict(
            flu='insitu',          # 流体类型: 采用地层温度的原位流体
            fluid_id='co2',        # 注入流体组分: CO2
            value=1.0e-6,          # 注入速率 (m^3/s)
            pos=[0, 0, 0],         # 注入位置: 坐标原点
        ))

    # 配置求解器选项
    model.set_text(
        key='solve',
        text={'show_cells': {'dim0': 0,     # 沿轴向 (第0维) 显示云图剖面
                             'dim1': 2       # 沿Z方向 (第2维) 显示剖面
                             },
              'time_max': 10 * 3600,         # 最大模拟时间: 10小时 (秒)
              }
    )
    # 返回模型
    return model


if __name__ == '__main__':
    # 创建并求解模型 (GUI窗口保持打开)
    gui.execute(lambda: tfc.solve(create()), close_after_done=False)
