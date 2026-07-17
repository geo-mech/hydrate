# ** desc = '重力驱动下的气水分层'
#
# 物理问题描述：
#   本模型模拟在重力作用下，气-水两相在孔隙介质中的重力分异（分层）过程。
#   模型为二维垂直剖面，区域范围：水平方向0~300m，垂直方向-500m~0m。
#   初始时，CH4和H2O均匀混合（各占50%），由于CH4密度远小于水，
#   在重力作用下CH4逐渐向上运移聚集在顶部，H2O向下运移聚集在底部，
#   最终形成气在上、水在下的重力平衡状态。
#   模拟时间100年，观察气水完全分离的过程。
#
# 建模技术要点：
#   1. 使用 create_cube 生成垂直剖面网格（30x100）
#   2. 初始均匀饱和度：CH4=50%, H2O=50%
#   3. 考虑重力加速度 gravity=(0,0,-10)
#   4. 使用 NIST 物性参数（create_ch4, create_h2o）精确计算密度
#   5. 最大时间步长设为1年，总模拟时长100年

from zmlx import *


def create(jx, jz, s=None):
    """
    创建重力分异模型。

    Args:
        jx: 水平方向（x）的网格单元数量
        jz: 垂直方向（z）的网格单元数量
        s: 初始饱和度分布。若为None，默认CH4和H2O各占50%

    Returns:
        model: 渗流模型对象
    """
    # 生成二维垂直剖面网格：水平0~300m，垂直-500m~0m
    mesh = create_cube(
        x=np.linspace(0, 300, jx + 1),
        y=(-0.5, 0.5),
        z=np.linspace(-500, 0, jz + 1)
    )
    if s is None:
        s = {'ch4': 0.5, 'h2o': 0.5}

    # 创建渗流模型：
    #   孔隙度0.1，孔隙模量100MPa，存储系数1e6
    #   温度280K，压力10MPa，渗透率1e-15 m2
    #   热传导系数2.0 W/(m·K)，最大时间步长1年
    #   考虑重力加速度-10 m/s2
    model = tfc.create(
        mesh, porosity=0.1, pore_modulus=100e6,
        denc=1.0e6,
        temperature=280,
        p=10e6,
        s=s,
        perm=1.0e-15,
        heat_cond=2.0,
        fludefs=[create_ch4(name='ch4'),
                 create_h2o(name='h2o')],
        dt_max=3600 * 24 * 365,
        gravity=(0, 0, -10))

    return model


def show(model, jx, jz, caption=None):
    """
    在界面上显示模型状态（压力、CH4饱和度、H2O饱和度）。

    Args:
        model: 渗流模型对象
        jx: 水平方向网格单元数量
        jz: 垂直方向网格单元数量
        caption: 窗口标题
    """
    def on_figure(fig):
        args = [fig, add_contourf, tfc.get_x(model, shape=(jx, jz)), tfc.get_z(model, shape=(jx, jz))]
        p = tfc.get_p(model, shape=(jx, jz))
        v = tfc.get_v(model, shape=(jx, jz))
        s0 = tfc.get_v(model, fid=0, shape=(jx, jz)) / v
        s1 = tfc.get_v(model, fid=1, shape=(jx, jz)) / v
        opts = dict(aspect='equal', xlabel='x/m', ylabel='z/m', nrows=1, ncols=3)
        add_axes2(*args, p, cbar=dict(label='pressure', shrink=0.7), title='pressure', index=1, cmap='coolwarm', **opts)
        add_axes2(*args, s0, cbar=dict(label='ch4 saturation', shrink=0.7), title='ch4 saturation', index=2, **opts)
        add_axes2(*args, s1, cbar=dict(label='h2o saturation', shrink=0.7), title='h2o saturation', index=3, **opts)
        fig.suptitle(f'时间: {tfc.get_time(model, as_str=True)}')

    plot(on_figure, caption=caption, tight_layout=True)


def main():
    """
    主函数：创建30x100网格的重力分异模型（初始均匀混合），
    先显示初始状态，然后模拟100年的重力分异过程。
    """
    jx, jz = 30, 100
    model = create(jx, jz)
    show(model, jx, jz, caption='初始状态')
    tfc.solve(model, extra_plot=lambda: show(model, jx, jz, caption='当前状态'),
              time_forward=3600 * 24 * 365 * 100  # 模拟100年
              )


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
