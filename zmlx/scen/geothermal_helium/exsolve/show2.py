# -*- coding: utf-8 -*-

from zmlx import tfc, Seepage, plt


def show_xy(model: Seepage):
    """
    xy 平面显示函数。

    显示内容：
    1. 压力场；
    2. 温度场；
    3. He_sol 质量分布；
    4. N2_sol 质量分布；
    5. CH4_sol 质量分布。

    注意：
    这里显示的是水相溶解组分质量，而不是游离气相质量。
    """

    # 只显示真实储层平面，不显示 z<-2 和 z>2 的虚拟井网格
    mask = tfc.get_cell_mask(model, zr=[-1, 1])

    # 提取坐标
    x = tfc.get_x(model, mask=mask)
    y = tfc.get_y(model, mask=mask)

    # 提取物理场数据
    p = tfc.get_p(model, mask=mask)
    t = tfc.get_t(model, mask=mask)

    # ============================================================
    # 读取溶解组分质量
    # ============================================================

    def safe_get_m(fid):
        """
        安全读取某个组分质量。
        如果当前模型中不存在该组分，则返回全 0。
        """
        try:
            return tfc.get_m(model, fid=fid, mask=mask)
        except Exception:
            return [0.0 for _ in x]

    he_sol_mass = safe_get_m('he_sol')
    n2_sol_mass = safe_get_m('n2_sol')
    ch4_sol_mass = safe_get_m('ch4_sol')

    # ================= 绘图函数区 =================

    def f_p(fig):
        ax = plt.add_axes2(
            fig,
            aspect='equal',
            xlabel='x (m)',
            ylabel='y (m)',
            title='Pressure Field'
        )
        plt.add_tricontourf(
            ax,
            x,
            y,
            p / 1e6,
            cbar=dict(label='Pressure (MPa)')
        )

    def f_t(fig):
        ax = plt.add_axes2(
            fig,
            aspect='equal',
            xlabel='x (m)',
            ylabel='y (m)',
            title='Temperature Field'
        )
        plt.add_tricontourf(
            ax,
            x,
            y,
            t,
            cbar=dict(label='Temperature (K)')
        )

    def f_he_sol_mass(fig):
        ax = plt.add_axes2(
            fig,
            aspect='equal',
            xlabel='x (m)',
            ylabel='y (m)',
            title='He_sol Mass Field'
        )
        plt.add_tricontourf(
            ax,
            x,
            y,
            he_sol_mass,
            cbar=dict(label='He_sol mass (kg)')
        )

    def f_n2_sol_mass(fig):
        ax = plt.add_axes2(
            fig,
            aspect='equal',
            xlabel='x (m)',
            ylabel='y (m)',
            title='N2_sol Mass Field'
        )
        plt.add_tricontourf(
            ax,
            x,
            y,
            n2_sol_mass,
            cbar=dict(label='N2_sol mass (kg)')
        )

    def f_ch4_sol_mass(fig):
        ax = plt.add_axes2(
            fig,
            aspect='equal',
            xlabel='x (m)',
            ylabel='y (m)',
            title='CH4_sol Mass Field'
        )
        plt.add_tricontourf(
            ax,
            x,
            y,
            ch4_sol_mass,
            cbar=dict(label='CH4_sol mass (kg)')
        )

    # ================= 输出面板区 =================

    plt.plot_on_figure(f_p, caption='Pressure')
    plt.plot_on_figure(f_t, caption='Temperature')
    plt.plot_on_figure(f_he_sol_mass, caption='He_sol Mass')
    plt.plot_on_figure(f_n2_sol_mass, caption='N2_sol Mass')
    plt.plot_on_figure(f_ch4_sol_mass, caption='CH4_sol Mass')