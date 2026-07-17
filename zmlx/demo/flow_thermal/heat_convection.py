# ** desc = '单相流，初始有密度的差异，在重力的驱动下自然对流的过程'
#
# 本案例模拟了密度差异驱动下的自然对流（Natural Convection）过程：
# 在一个矩形区域内（x方向[-0.6,0.6]，z方向[-1,1]），水作为单相流体充满孔隙介质。
# 在左上角（-0.1,0.5）附近有一个低温区（280K），右下角（0.1,-0.5）附近有一个高温区（320K），
# 其余区域温度为300K。温度差异导致水的密度发生变化（高温区密度低、低温区密度高），
# 在重力场（z方向-10）的作用下，高密度流体下沉、低密度流体上浮，形成自然对流。
# 同时，模型关闭了热传导（添加标记'disable_ther'），仅考虑对流传热机制，
# 更加清晰地展示了流体流动对温度场的影响。添加了z0辅助变量用于追踪流体运动。

from zmlx import *


def create(jx, jz):
    """
    创建自然对流模型。

    参数:
        jx: int，x方向的网格数量
        jz: int，z方向的网格数量
    返回:
        Seepage对象，配置好的渗流-热耦合模型
    """
    # 创建矩形网格：x方向[-0.6,0.6]，z方向[-1,1]，y方向厚度很薄（二维近似）
    mesh = create_cube(
        x=linspace(-0.6, 0.6, jx + 1), y=[-0.5, 0.5], z=linspace(-1, 1, jz + 1)
    )

    def is_region1(x, y, z):
        """判断是否在左上角低温区域（中心在(-0.1, 0.5)，半径0.2的圆）"""
        return point_distance([x, z], [-0.1, 0.5]) < 0.2

    def is_region2(x, y, z):
        """判断是否在右下角高温区域（中心在(0.1, -0.5)，半径0.2的圆）"""
        return point_distance([x, z], [0.1, -0.5]) < 0.2

    def get_denc(x, y, z):
        """
        获取体积热容（密度乘以比热容）。
        在区域1和区域2所在的位置使用极大的值（1e20）来模拟热边界条件，
        相当于恒温边界，其他区域使用正常值1e6。
        """
        return 1.0e20 if is_region1(x, y, z) or is_region2(x, y, z) else 1.0e6

    def get_temp(x, y, z):
        """
        获取初始温度分布函数。

        区域1（左上）为280K（低温），
        区域2（右下）为320K（高温），
        其余区域为300K（环境温度）。
        """
        if is_region1(x, y, z):
            return 280
        if is_region2(x, y, z):
            return 320
        else:
            return 300

    def dist(x, y, z):
        """获取热扩散率（此处统一返回1.0）"""
        return 1.0

    # 使用tfc（热-流-化学耦合）框架创建模型
    model = tfc.create(
        mesh=mesh, cfl=0.5,  # 网格和孔隙体积的相对变化容差
        fludefs=[h2o.create(t_min=272.0, t_max=340.0, p_min=1e6, p_max=40e6,
                            name='h2o')],  # 定义流体为水（H2O），指定温度和压力适用范围
        porosity=0.2,         # 孔隙度为0.2
        p=5e6, s=1.0,         # 初始压力5MPa，初始饱和度为1（完全饱和水）
        perm=1e-12,            # 渗透率为1e-12 m^2（约1 Darcy）
        temperature=get_temp, denc=get_denc,  # 温度和体积热容（使用函数形式支持空间变化）
        gravity=[0, 0, -10],  # 重力加速度，沿z轴负方向（竖直向下），大小为10 m/s^2
        dist=dist,             # 热扩散率
    )

    model.add_tag('disable_ther')  # 添加标记禁用热传导机制，仅保留对流传热
    tfc.set_fa(model, 0, 'z0', tfc.get_z(model))  # 设置辅助变量z0为单元格的z坐标，用于追踪流体运动轨迹

    return model


def show(model, jx, jz, caption=None):
    """
    显示模型的当前状态：温度分布、密度分布和辅助变量z0分布。

    参数:
        model: Seepage对象，要显示的模型
        jx: int，x方向网格数量
        jz: int，z方向网格数量
        caption: str或None，图形的标题
    """
    def on_figure(figure):
        """
        绘图回调函数：在指定图形中绘制三个子图。

        参数:
            figure: matplotlib的Figure对象
        """
        from zmlx.plt import calculate_subplot_layout
        nrows, ncols = calculate_subplot_layout(3, 0.6, fig=figure)  # 自动计算子图布局
        opts = dict(nrows=nrows, ncols=ncols, xlabel='x', ylabel='z', aspect='equal')
        x = tfc.get_x(model, shape=[jx, jz])  # 获取x坐标矩阵
        z = tfc.get_z(model, shape=[jx, jz])  # 获取z坐标矩阵
        args = ['contourf', x, z, ]            # 填充等值线图的基础参数

        # 绘制两个圆形区域的边界参考线（用于标识初始高低温区的位置）
        angles = linspace(0, np.pi * 2, 100)
        c1 = item('xy', 0.2 * np.cos(angles) + 0.1, 0.2 * np.sin(angles) - 0.5, 'r--')  # 高温区边界（红色虚线）
        c2 = item('xy', 0.2 * np.cos(angles) - 0.1, 0.2 * np.sin(angles) + 0.5, 'k--')  # 低温区边界（黑色虚线）

        # 温度分布等值线图
        temp = item(*args, tfc.get_fa(model, 0, 'temperature', shape=[jx, jz]),
                    cbar=dict(label='温度', shrink=0.6))
        # 密度分布等值线图
        den = item(*args, tfc.get_den(model, 0, shape=[jx, jz]),
                   cbar=dict(label='密度', shrink=0.6))
        # z0辅助变量分布等值线图（反映流体运动导致的物质输运）
        z0 = item(*args, tfc.get_fa(model, 0, 'z0', shape=[jx, jz]),
                  cbar=dict(label='z0', shrink=0.6))

        # 创建三个子图，分别显示温度、密度和z0，并叠加区域边界线
        add_axes2(figure, add_items, temp, c1, c2, title='流体温度', index=1, **opts)
        add_axes2(figure, add_items, den, c1, c2, title='密度', index=2, **opts)
        add_axes2(figure, add_items, z0, c1, c2, title='流体z0', index=3, **opts)

    # 执行绘图
    plot(on_figure, caption=caption, clear=True, tight_layout=True,
         suptitle=f'time = {tfc.get_time(model, as_str=True)}'
         )


def main():
    """
    主函数：创建自然对流模型并执行求解。

    使用60x100的精细网格，计算时间达500天，每步输出实时状态图形。
    """
    jx, jz = 60, 100                        # 定义网格分辨率：x方向60格，z方向100格
    model = create(jx, jz)                  # 创建自然对流模型
    show(model, jx, jz, caption='初始状态')  # 显示初始状态
    # 求解模型：最大时间500天，每步回调show函数以实时显示状态
    tfc.solve(model, time_max=3600 * 24 * 500, extra_plot=lambda: show(model, jx, jz, caption='实时状态'))


if __name__ == '__main__':
    # 通过GUI执行主函数；--no-gui参数用于无图形界面运行
    gui.execute(main, close_after_done=False)
