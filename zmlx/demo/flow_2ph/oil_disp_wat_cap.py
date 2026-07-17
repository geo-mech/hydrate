# ** desc = '两相流，油驱替水模拟。考虑驱替压力+毛管力效应'
#
# 物理问题描述：
#   本模型模拟在驱替压力和毛管压力共同作用下的油驱水过程。
#   模型采用二维平面网格（30x30），区域范围0~30m x 0~30m。
#   左下角（x=0,y=0）为注入点，初始油饱和度0.9、压力11MPa；
#   其余区域初始油饱和度0.1、水饱和度0.9、压力10MPa。
#   通过1MPa的初始压差驱动油向四周驱替水。
#   同时，模型考虑了毛管压力效应（使用sand_J毛管压力曲线），
#   展示了毛管力对驱替效率的影响。
#
# 建模技术要点：
#   1. 使用 create_cube 生成30x30平面网格
#   2. 左下角和右上角设置大体积单元作为定压边界
#   3. 注入点设置初始高压（11MPa），形成驱替压差
#   4. 使用 capillary.add_setting 添加毛管压力曲线（sand_J型砂岩）
#   5. 初始饱和度在注入点附近设置为油富集（oil=0.9）
#   6. 总模拟时长10000天（考虑毛管力效应后驱替速度减慢）

from zmlx import *

# 砂岩J的毛管压力曲线数据
# 第一列：Oil饱和度  第二列：Water压力 - Oil压力（即毛管压力Pc，单位Pa）
# 该曲线反映了油-水两相系统中，毛管压力随油饱和度变化的关系
sand_J = """0	757.5757576
0.011	1167.929293
0.0339	1849.747475
0.0806	2891.414141
0.2015	4595.959596
0.2934	7304.292929
0.3564	11691.91919
0.4365	18636.36364
0.5081	29008.83838
0.5789	46193.18182
0.6408	73257.57576
0.6923	117146.4646
0.7346	186887.6263
0.7477	290119.9495
0.7514	460871.2121
0.7541	732171.7172
0.7576	1154223.485
0.7634	1846483.586
0.7724	2888648.99
0.7867	4626369.949
0.8086	7346635.101
0.8561	12562297.98"""


def create(jx: int, jy: int, s=None) -> Seepage:
    """
    创建考虑毛管力效应的油驱水模型。

    Args:
        jx: x方向的网格单元数量
        jy: y方向的网格单元数量
        s: 初始饱和度分布。若为None，则默认在注入点附近油饱和度为0.9，其余为0.1

    Returns:
        model: 渗流模型对象
    """
    # 生成二维平面网格：0~30m x 0~30m，厚度1m
    mesh: SeepageMesh = create_cube(
        linspace(0, 30, jx + 1),
        linspace(0, 30, jy + 1), (-0.5, 0.5)
    )

    x0, x1 = mesh.get_pos_range(0)  # x方向坐标范围
    y0, y1 = mesh.get_pos_range(1)  # y方向坐标范围

    # 将左下角和右上角的单元体积设为极大值，模拟定压边界
    for cell in mesh.cells:
        x, y, z = cell.pos
        if abs(y - y1) < 0.1 and abs(x - x1) < 0.1:
            cell.vol = 1.0e8  # 右上角：定压出口
        if abs(y - y0) < 0.1 and abs(x - x0) < 0.1:
            cell.vol = 1.0e8  # 左下角：定压注入

    # 定义两种流体
    fluid_defs = [
        FluDef(den=50, vis=1.0e-2, name='oil'),
        FluDef(den=1000, vis=1.0e-3, name='water')
    ]

    if s is None:
        def s(x, y, z):
            if abs(x - x0) < 0.01 and abs(y - y0) < 0.01:
                return {'oil': 0.9, 'water': 0.1}  # 注入点附近：油多水少
            else:
                return {'oil': 0.1, 'water': 0.9}  # 其他区域：水多油少

    def p(x, y, z):
        """定义初始压力：注入点为11MPa（高压，提供驱替动力），其余为10MPa。"""
        if abs(x - x0) < 0.01 and abs(y - y0) < 0.01:
            return 11e6
        else:
            return 10e6

    # 创建渗流模型（禁用密度/粘度/热传导更新以简化计算）
    model: Seepage = tfc.create(
        mesh, porosity=0.2, pore_modulus=100e6,
        p=p, temperature=280,
        s=s,
        perm=1e-14,
        disable_update_den=True,
        disable_update_vis=True,
        disable_ther=True,
        disable_heat_exchange=True,
        fludefs=fluid_defs
    )

    def get_idx(x, y, z):
        """
        定义不同区域所使用的毛管压力曲线ID。
        本模型中所有单元均使用同一毛管压力曲线（ID=0）。
        """
        return 0

    # 添加毛管压力设置：油-水两相，使用sand_J曲线
    capillary.add_setting(model, fid0='water', fid1='oil', get_idx=get_idx,
                          data=[sand_J])
    # 设置最大时间步长为1周（7天）
    tfc.set_dt_max(model, 3600 * 24 * 7 * 1)
    return model


def show(model: Seepage, jx: int, jy: int):
    """
    在界面上显示模型的状态（压力和油饱和度云图）。

    Args:
        model: 渗流模型对象
        jx: x方向的网格单元数量
        jy: y方向的网格单元数量
    """
    x = tfc.get_x(model, shape=(jx, jy))
    y = tfc.get_y(model, shape=(jx, jy))
    p = tfc.get_p(model, shape=(jx, jy))
    s = tfc.get_v(model, 0, shape=(jx, jy)) / tfc.get_v(model, None, shape=(jx, jy))

    opts = dict(aspect='equal', xlabel='x/m', ylabel='y/m')
    obj = fig.auto_layout(
        fig.axes2(
            fig.contourf(x, y, p, cbar=dict(label='Pressure', shrink=0.7)),
            index=1,
            title='Pressure', **opts
        ),
        fig.axes2(
            fig.contourf(x, y, s, cbar=dict(label='Saturation', shrink=0.7), cmap='coolwarm'),
            index=2,
            title='oil saturation', **opts
        ),
        fig.suptitle(f'时间: {tfc.get_time(model, as_str=True)}'),
        fig.tight_layout(),
        aspect_ratio=1,
    )
    fig.show(obj, caption='模型状态')


def oil_disp_wat():
    """
    主函数：创建30x30网格的油驱水模型（考虑毛管力），模拟10000天的驱替过程。
    """
    jx, jy = 30, 30
    model = create(jx, jy)
    tfc.solve(model, extra_plot=lambda: show(model, jx, jy), time_forward=10000 * 24 * 3600,
              folder=opath('oil_disp_wat_cap')
              )


if __name__ == '__main__':
    gui.execute(oil_disp_wat, close_after_done=False)
