# ** desc = '实验室尺度的水合物分解过程模拟 (仅供参考)'
"""
=============================================================
CH4水合物降压分解的实验室尺度数值模拟 (case_2 - 低温和低压条件)
=============================================================

物理问题:
    在case_1的基础上，修改了初始温度和压力条件，使其更接近实际水合物藏的
    温压环境。样品几何不变 (长0.5米，半径0.1米)，初始水合物饱和度40%。
    初始温度降至276.15K (3°C)，初始压力降至4MPa，生产压力降至0.3MPa。
    模拟时长3天，采用更低的背压驱动力更强。

建模技术:
    - 柱坐标系网格 + swap_yz变换
    - 虚拟生产单元实现边界控制
    - TFC热-流-化耦合求解框架
    - 自适应时间步长 (dt_min=1e-4, dt_max=10)

与case_1的区别:
    - 初始温度: 285K -> 276.15K (降低约9°C)
    - 初始压力: 10MPa -> 4MPa (更低的初始压力)
    - 生产压力: 3MPa -> 0.3MPa (更大的压降幅度)
    - 通过 warnings_ignored={'gravity'} 忽略重力警告

关键参数:
    - 孔隙度: 0.3, 渗透率: 1.0e-14 m^2
    - 初始: h2o=0.6, ch4_hydrate=0.4

注意事项:
    此case不针对任何特定实验，仅用于说明实验室尺度水合物分解建模方法。
    since 2025-2-6
"""

from zmlx import *


def create():
    """
    创建并配置实验室尺度CH4水合物降压分解的数值模型 (低温和低压条件)。

    本函数与 case_1 的 create() 结构相同，但在以下参数上做了调整:
        - 初始温度: 285K -> 276.15K (约3°C，更接近实际水合物藏温度)
        - 初始压力: 10MPa -> 4MPa
        - 生产压力: 3MPa -> 0.3MPa (更大的压降，更强的分解驱动力)
        - 忽略重力相关警告 (warnings_ignored={'gravity'})

    参数:
        无 (所有参数在函数内部定义)

    返回:
        model (tfc.Model): 配置完成的TFC耦合模型对象

    注意:
        - 与case_1一样采用虚拟单元实现生产边界条件
        - 更低的温度和水合物相平衡压力对应，使分解行为更真实
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

    # 定义初始饱和度: 虚拟单元全水，其余单元含水0.6 + 水合物0.4
    def get_s(x, y, z):
        if is_prod(x, y, z):
            return {'h2o': 1}
        else:
            return {'h2o': 0.6, 'ch4_hydrate': 0.4}

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
        temperature=273.15 + 3.0, # 初始温度 (K) = 3°C (更低，接近海底温度)
        p=4e6,                    # 初始压力 (Pa) = 4 MPa (更低的初始压力)
        s=get_s,                  # 初始饱和度函数
        perm=1.0e-14,             # 绝对渗透率 (m^2) ≈ 10 mD
        dist=0.001,               # 裂隙/网格特征尺度 (m)
        heat_cond=heat_cond,      # 热导率函数
        prods=[{'index': -1,      # 生产井: 连接最后一个单元
                't': [0, 1e20],   # 从0时刻到无穷大持续生产
                'p': [0.3e6, 0.3e6]}]  # 恒定生产压力 0.3 MPa (更低，分解更强)
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
