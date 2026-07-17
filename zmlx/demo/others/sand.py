# ** desc = '砂浓度计算（考虑固体颗粒的运移与沉积，正在测试，尚未完成）'
#
# 本示例模拟含砂流体在多孔介质中的流动过程，涉及三种组分：
#   - 水（h2o）：载液
#   - 悬浮砂（flu_sand）：随水流运移的固体颗粒
#   - 固体砂（sol_sand）：沉积在孔隙中的固体骨架
# 模型为50m×50m的二维区域，采用100×100网格剖分。
# 在左下角设置注入井（3MPa注入），其余区域初始压力1MPa，
# 初始饱和度：水90%，固体砂10%。
# 本模型使用sand_config模块定义砂的启动-运移-沉积过程，
# 通过压力梯度控制砂从固相到悬浮相的转化，模拟出砂现象。
# 注意：本示例仍在测试中，功能尚未完全完成。

from zmlx import *


def create():
    """
    创建一个含砂流体流动模型。

    模型为50m×50m的二维区域，左下角设置注水井（3MPa注入），
    其余区域初始压力1MPa。包含三种组分：水、悬浮砂和固体沉积砂。
    使用sand_config模块处理砂的启动（固相→悬浮相）和运移过程。

    注水驱动孔隙水流动，当压力梯度超过临界值时，固体砂启动进入
    悬浮状态并随水流运移。通过自定义属性i0和i1控制各组分
    的启动特性。

    Returns:
        返回创建的Seepage模型对象。
    """
    mesh = create_cube(x=np.linspace(0, 50, 100),  # x方向：0~50m，100个网格
                       y=np.linspace(0, 50, 100),  # y方向：0~50m，100个网格
                       z=[0, 1])  # z方向厚度1m

    # 所有流体组分的定义
    fludefs = [FluDef.create(defs=[
        FluDef(den=1000, vis=0.001, specific_heat=1000, name='h2o'),  # 水：密度1000，粘度0.001
        FluDef(den=1000, vis=0.001, specific_heat=1000,
               name='flu_sand')],  # 悬浮砂：密度1000，粘度与水相同
        name='flu'),  # 流体相（包含水和悬浮砂两种组分）
        FluDef(den=1000, vis=1e30, specific_heat=1000,
               name='sol_sand')  # 固体沉积砂：极高粘度，不发生流动
    ]

    x_min, x_max = mesh.get_pos_range(0)  # x方向坐标范围
    y_min, y_max = mesh.get_pos_range(0)  # y方向坐标范围

    def get_fai(x, y, z):
        """定义孔隙度：边界和注入井处设极大值固定压力"""
        if abs(x - x_max) < 0.1 or abs(y - y_max) < 0.1:
            return 1e10  # 上/右边界：大孔隙固定压力
        if abs(x - x_min) < 0.1 and abs(y - y_min) < 0.1:
            return 1e10  # 左下角注入井位置：大孔隙固定压力
        else:
            return 0.2  # 正常孔隙度20%

    def get_p(x, y, z):
        """定义初始压力：注入井处3MPa，其余区域1MPa"""
        if abs(x - x_min) < 0.1 and abs(y - y_min) < 0.1:
            return 3e6  # 左下角注入井：3MPa
        else:
            return 1e6  # 其余区域：1MPa

    def get_k(x, y, z):
        return 1e-14

    def get_s(x, y, z):
        """定义初始饱和度：水90%，固体砂10%"""
        return {'h2o': 0.9, 'sol_sand': 0.1}

    model = tfc.create(mesh=mesh, cfl=0.2,
                       fludefs=fludefs,
                       porosity=get_fai, pore_modulus=200e6,
                       p=get_p, s=get_s, perm=get_k,
                       has_solid=True  # 启用固体相支持，追踪固体沉积
                       )

    tfc.set_solve(model,
                  show_cells={'dim0': 0, 'dim1': 1, 'show_t': False},  # 显示xy平面，不显示温度
                  time_max=3600 * 24 * 365 * 30  # 模拟总时长30年
                  )

    # 添加压力梯度到饱和度变化率的映射曲线（砂启动函数）
    x = [0, 0.01e6, 0.03e6, 0.1e6]  # 压力梯度阈值（Pa/m）
    y0 = [0, 0.0, 0.0, 0.1]  # 曲线0：固相→悬浮相转化率
    y1 = [0, 0.0001, 0.001, 0.2]  # 曲线1：悬浮相浓度变化率

    model.set_curve(index=0, curve=Interp1(x=x, y=y0))  # 设置曲线0（用于组分0的启动）
    model.set_curve(index=1, curve=Interp1(x=x, y=y1))  # 设置曲线1（用于组分1的启动）

    idx = model.reg_cell_key('i0')  # 注册自定义属性'i0'（控制组分0的启动参数）
    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        x, y, z = cell.pos
        if abs(x - x_min) > 0.1 or abs(y - y_min) > 0.1:
            cell.set_attr(index=idx, value=0)  # 除注入井附近外，属性i0=0

    idx = model.reg_cell_key('i1')  # 注册自定义属性'i1'（控制组分1的启动参数）
    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        x, y, z = cell.pos
        if abs(x - x_min) > 0.1 or abs(y - y_min) > 0.1:
            cell.set_attr(index=idx, value=1)  # 除注入井附近外，属性i1=1

    # 配置砂运移模型：指定固体砂、悬浮砂的组分名称，
    # 以及控制砂启动的自定义属性键
    sand_config.add_setting(model,
                            sol_sand='sol_sand', flu_sand='flu_sand',
                            ca_i0='i0', ca_i1='i1')

    return model


def show_gradient(model: Seepage):
    """
    可视化模型中的压力梯度分布。

    提取各单元的压力梯度值，绘制等值线图，
    用于分析砂启动的驱动力分布。

    Args:
        model: 待可视化的Seepage渗流模型对象。
    """
    x = as_numpy(model).cells.x  # 提取所有单元的x坐标
    y = as_numpy(model).cells.y  # 提取所有单元的y坐标
    v = sand_config.get_gradient(model, fluid=[0])  # 计算流体相的压力梯度
    tricontourf(x, y, v, caption='gradient')  # 绘制梯度等值线图


def update_sand(*args, **kwargs):
    """
    自定义砂运移更新函数。

    在tfc迭代循环中被调用，用于在每个时间步更新砂的启动、运移和沉积。
    调用sand_config.iterate执行具体的砂运移计算逻辑。

    Args:
        *args: 传递给sand_config.iterate的位置参数。
        **kwargs: 传递给sand_config.iterate的关键字参数。
    """
    print('my update sand')  # 调试输出，提示砂更新正在进行
    sand_config.iterate(*args, **kwargs)  # 执行实际的砂运移计算


def test_1():
    """
    测试函数：创建模型并运行含砂流动模拟。

    在tfc.solve的slots中注册自定义的update_sand函数，
    替换默认的砂更新逻辑。同时注册extra_plot以实时显示
    压力梯度分布。

    Returns:
        无返回值。
    """
    model = create()

    def extra_plot():
        show_gradient(model)  # 求解过程中实时显示压力梯度

    tfc.solve(model,
              extra_plot=extra_plot,  # 每步迭代后回调
              slots={'update_sand': update_sand}  # 注册自定义砂更新函数
              )


if __name__ == '__main__':
    gui.execute(test_1, close_after_done=False)
