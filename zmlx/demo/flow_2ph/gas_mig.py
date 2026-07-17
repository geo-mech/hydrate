# ** desc = '浮力作用下气体运移成藏过程模拟'
#
# 物理问题描述：
#   本模型模拟天然气（CH4）在浮力作用下从深层气源向上运移并聚集成藏的过程。
#   模型为二维垂直剖面，区域范围：水平方向0~300m，垂直方向-500m~0m（地表为0）。
#   在深部（-500m处）有一个半径为50m的圆形气源区，初始为纯CH4饱和，
#   其余区域初始为纯水（H2O）饱和。由于CH4密度远小于水，在浮力作用下
#   CH4向上运移，模拟6年的天然气运移成藏过程。
#
# 建模技术要点：
#   1. 使用 create_cube 生成二维垂直剖面网格（60x100）
#   2. 初始地温梯度：地表278K，地温梯度0.0443 K/m
#   3. 初始压力梯度：静水压力梯度1e4 Pa/m
#   4. 气源区设置高孔隙度（1.0）以提供充足的气源
#   5. 考虑重力作用（gravity=(0,0,-10)）
#   6. 上下边界设置高存储系数（denc=1e20）模拟封闭边界
#   7. 使用 NIST 物性参数（create_ch4, create_h2o）计算流体密度和粘度随温压的变化

from zmlx import *


def create(jx, jz):
    """
    创建天然气运移成藏模拟模型。

    Args:
        jx: 水平方向（x）的网格单元数量
        jz: 垂直方向（z）的网格单元数量

    Returns:
        model: 渗流模型对象，包含网格、温压场、物性参数等
    """
    # 生成二维垂直剖面网格：水平0~300m，垂直-500m~0m
    mesh = create_cube(
        x=linspace(0, 300, jx + 1),
        y=(-0.5, 0.5),
        z=linspace(-500, 0, jz + 1)
    )

    def get_t(x, y, z):
        """
        定义地温梯度函数。地表温度约300K（278+22.15），
        地温梯度约0.0443 K/m（即每加深1m温度升高约0.0443K）。
        """
        return 278 + 22.15 - 0.0443 * z

    def get_p(x, y, z):
        """
        定义初始压力场。顶部压力约15MPa（10+5），
        按静水压力梯度1e4 Pa/m随深度增加。
        """
        return 10e6 + 5e6 - 1e4 * z

    def is_gas_region(x, y, z):
        """
        判断给定坐标是否属于气源区。
        气源区位于底部中心（150, 0, -500），半径50m的半球形区域。
        """
        return get_distance([x, y, z], [150, 0, -500]) < 50

    def get_s(x, y, z):
        """定义初始饱和度：气源区为纯CH4，其他区域为纯H2O。"""
        if is_gas_region(x, y, z):
            return {'ch4': 1}
        else:
            return {'h2o': 1}

    z0, z1 = mesh.get_pos_range(2)  # 获取z方向的最小和最大坐标

    def get_denc(x, y, z):
        """
        定义存储系数（denc，即密度*比热容或储集系数）。
        上下边界（z=z0和z=z1）设为极大值1e20，模拟封闭边界条件；
        内部区域设为1e6（正常值）。
        """
        if abs(z - z0) < 0.1 or abs(z - z1) < 0.1:
            return 1.0e20
        else:
            return 1.0e6

    def get_k(x, y, z):
        """均匀渗透率分布：1e-14 m2（约10mD）。"""
        return 1.0e-14

    def get_porosity(x, y, z):
        """
        定义孔隙度分布：气源区为1.0（确保有充足的气体供应），
        其余区域为0.1。
        """
        if is_gas_region(x, y, z):
            return 1.0  # 使得有更多的气体
        else:
            return 0.1

    # 创建渗流模型
    model = tfc.create(
        mesh, porosity=get_porosity, pore_modulus=100e6,
        denc=get_denc, dist=0.1,
        temperature=get_t, p=get_p, s=get_s,
        perm=get_k, heat_cond=2.0,
        fludefs=[create_ch4(name='ch4'),       # CH4流体：使用NIST物性参数
                 create_h2o(name='h2o')],       # H2O流体：使用NIST物性参数
        dt_max=3600 * 24 * 30.0, gravity=(0, 0, -10)  # 最大时间步长30天，重力加速度-10 m/s2
    )

    # 设置求解参数：模拟总时长6年
    model.set_text(
        key='solve',
        text={'time_max': 3600 * 24 * 365 * 6, }
    )

    return model


def show(model, jx, jz):
    """
    在界面上显示模型状态（压力、CH4饱和度、H2O饱和度）。

    Args:
        model: 渗流模型对象
        jx: 水平方向网格单元数量
        jz: 垂直方向网格单元数量
    """
    def on_figure(fig):
        x = tfc.get_x(model, shape=(jx, jz))
        z = tfc.get_z(model, shape=(jx, jz))
        p = tfc.get_p(model, shape=(jx, jz))
        v0 = tfc.get_v(model, fid=0, shape=(jx, jz))
        v1 = tfc.get_v(model, fid=1, shape=(jx, jz))
        v = v0 + v1
        angles = np.linspace(0, np.pi, 100)

        # 三列并排显示：压力、CH4饱和度、H2O饱和度
        layout = AutoLayout(fig, 3, subplot_aspect_ratio=0.6, aspect='equal', xlabel='x/m', ylabel='z/m')
        ax = layout.add_axes2(add_contourf, x, z,
                              p, cbar=dict(label='p', shrink=0.6), title='pressure', cmap='coolwarm')
        ax.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), 'k--')  # 气源区边界

        ax = layout.add_axes2(add_contourf, x, z,
                              v0 / v, cbar=dict(label='s0', shrink=0.6), title='ch4 saturation')
        ax.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), 'r--')

        ax = layout.add_axes2(add_contourf, x, z,
                              v1 / v, cbar=dict(label='s1', shrink=0.6), title='h2o saturation')
        ax.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), 'r--')

    plot(on_figure, caption=f'Seepage({model.handle_str})', suptitle=f'时间: {tfc.get_time(model, as_str=True)}',
         tight_layout=True)


def main():
    """
    主函数：创建60x100网格的气体运移模型，求解6年的运移成藏过程。
    """
    jx, jz = 60, 100
    model = create(jx, jz)
    tfc.solve(model, extra_plot=lambda: show(model, jx, jz))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
