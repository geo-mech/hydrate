# ** desc = '实验室尺度的水合物分解过程模拟 (仅供参考)'
"""
=============================================================
CH4水合物降压分解的实验室尺度数值模拟 (case_1)
=============================================================

物理问题:
    本模型模拟圆柱形岩心样品中甲烷水合物的降压分解过程。
    样品长0.5米，半径0.1米，初始水合物饱和度40%，初始温度285K，
    初始压力10MPa。通过在样品一端施加3MPa的背压，模拟降压开采过程。
    总模拟时长3天 (3 x 24 x 3600 秒)。

建模技术:
    - 采用柱坐标系网格 (create_cylinder)，通过swap_yz转换为标准坐标
    - 使用虚拟生产单元 (add_cell_face) 实现边界条件控制
    - 采用TFC (Thermal-Flow-Chemical) 耦合框架进行热-流-化多场耦合求解
    - 自适应时间步长: dt_min=1e-4, dt_max=10
    - 虚拟单元的导热系数设为0，避免热量从生产端异常传递
    - 虚拟单元渗透率通过denc参数设为极大值(1e20)，实现自由流动边界

关键参数:
    - 孔隙度: 0.3
    - 绝对渗透率: 1.0e-14 m^2 (约10 mD)
    - 孔隙模量: 100 MPa
    - 初始含水饱和度: 0.6, 初始水合物饱和度: 0.4

注意事项:
    此case不针对任何特定实验，仅用于说明实验室尺度水合物分解建模方法。
    since 2025-2-6
"""

from zmlx import *


def create():
    """
    创建并配置实验室尺度CH4水合物降压分解的数值模型。

    该函数完成以下工作:
        1. 生成柱形网格 (长0.5m, 半径0.1m, 50x10个单元)
        2. 添加虚拟生产单元，用于施加背压边界条件
        3. 定义初始饱和度、密度和热导率空间分布函数
        4. 调用 hydrate.create_kwargs 组装水合物模拟参数
        5. 创建 TFC 模型实例并设置求解器选项

    参数:
        无 (所有参数在函数内部定义)

    返回:
        model (tfc.Model): 配置完成的TFC耦合模型对象，可直接传入 tfc.solve() 求解

    注意:
        - 虚拟生产单元的体积和面积设置较大，以减小局部流动阻力
        - 上层边界 (is_upper) 使用极大的denc值模拟不渗透边界
        - 时间步长自适应范围: 1e-4 ~ 10 秒
    """
    # 创建柱坐标系网格: 轴向50等分 (0~0.5m), 径向10等分 (0~0.1m)
    mesh = create_cylinder(x=np.linspace(0, 0.5, 50),
                           r=np.linspace(0, 0.1, 10))
    # 交换Y和Z轴坐标，使柱体轴向与Z方向对齐 (便于后续边界处理)
    swap_yz(mesh)

    # 添加虚拟的cell和face用于生产 (位于偏移位置，大体积/面积以减小阻力)
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

    # 定义初始饱和度分布: 生产单元全水，其余单元含水0.6 + 水合物0.4
    def get_s(x, y, z):
        if is_prod(x, y, z):
            return {'h2o': 1}
        else:
            return {'h2o': 0.6, 'ch4_hydrate': 0.4}

    # 定义密度/渗透率乘数: 顶部边界极高值(不渗透)，内部正常值5e6
    def denc(*pos):
        return 1e20 if is_upper(*pos) else 5e6

    # 定义热导率: 确保不会有热量通过用于生产的虚拟的cell传递过来.
    # abs(y)<2 为实体区域 (正常导热)，其余 (虚拟单元区域) 导热系数为0
    def heat_cond(x, y, z):
        return 1.0 if abs(y) < 2 else 0.0

    # 组装水合物模拟的关键字参数
    kw = hydrate.create_kwargs(
        gravity=[0, 0, 0],       # 忽略重力 (实验室尺度，方向影响小)
        dt_min=1.0e-4,           # 最小时间步长 (秒)，捕捉快速动力学变化
        dt_max=10,               # 最大时间步长 (秒)，提高计算效率
        cfl=0.1,         # 体积变化相对容差，控制迭代精度
        mesh=mesh,                # 网格对象
        porosity=0.3,             # 孔隙度
        pore_modulus=100e6,       # 孔隙模量 (Pa)，控制孔隙压缩性
        denc=denc,                # 密度/渗透率乘数函数
        temperature=285,          # 初始温度 (K) = 11.85°C
        p=10e6,                   # 初始压力 (Pa) = 10 MPa
        s=get_s,                  # 初始饱和度函数
        perm=1.0e-14,             # 绝对渗透率 (m^2) ≈ 10 mD
        dist=0.001,               # 裂隙/网格特征尺度 (m)
        heat_cond=heat_cond,      # 热导率函数
        prods=[{'index': -1,      # 生产井: 连接最后一个单元 (虚拟单元)
                't': [0, 1e20],   # 时间序列 (从0到无穷大)
                'p': [3e6, 3e6]}] # 恒定生产压力 3 MPa
    )
    # 创建TFC耦合模型
    model = tfc.create(**kw)

    # 配置求解器选项
    model.set_text(
        key='solve',
        text={'monitor': {'cell_ids': [model.cell_number - 1]},  # 监控最后一个单元 (虚拟生产单元) 的状态
              'show_cells': {'dim0': 0,           # 沿轴向 (第0维) 显示剖面
                             'dim1': 2,            # 沿Z方向 (第2维) 显示剖面
                             'mask': tfc.get_cell_mask(
                                 model=model, yr=[-1, 1])},  # 仅显示Y在[-1,1]范围的单元格
              'time_max': 3 * 24 * 3600,           # 最大模拟时间: 3天 (秒)
              }
    )
    # 返回模型
    return model


if __name__ == '__main__':
    # 创建并求解模型 (求解完毕后GUI窗口保持打开，便于查看结果)
    gui.execute(lambda: tfc.solve(create()), close_after_done=False)
