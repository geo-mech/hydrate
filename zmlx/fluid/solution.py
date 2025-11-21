"""
定义水溶液中的溶质。主要处理密度和粘度. 假设：
溶质的质量相对于水的质量是一个比较小的量，因此：
    1、溶液的密度/粘性随着溶质的浓度而线性变化；
    2、而溶液的比热等于水的比热。

@2025-11-20  张召彬
"""

from zmlx.exts.base import Seepage


def create_solute(
        solvent: Seepage.FluDef,
        c=0.01, den_times=1.0, vis_times=1.0, name=None
):
    """
    创建一个“溶质”对象。

    Args:
        solvent: “溶剂”的流体定义 (返回的“溶质”对象，将参考这个“溶剂”的密度/粘性/比热).
        c: “溶质”的质量浓度：“溶质”质量/“溶液”质量
        den_times: “溶液”的密度变化量（相对于“溶剂”）
        vis_times: “溶液”的粘性变化量（相对于“溶剂”）
        name: “溶质”的名称。如果为None，则使用“溶剂”的名称。

    Returns:
        Seepage.FluDef: “溶质”的流体定义
    """
    assert 0.0 < c <= 0.2, 'c must be in (0, 0.2]'

    # 溶质的定义
    res = solvent.get_copy(name=name)

    # 定义一个包含了两个组分的流体来测试
    flu = Seepage.FluData()
    flu.component_number = 2
    flu.get_component(0).mass = 1.0 - c
    flu.get_component(1).mass = c
    flu.get_component(0).den = 1
    flu.get_component(0).vis = 1

    # 计算密度(通过二分法来寻找)
    lr, rr = 1.0e-6, 1.0e6
    while rr - lr > 1.0e-8:
        den = (lr + rr) / 2.0
        flu.get_component(1).den = den
        if flu.den < den_times:
            lr = den
        else:
            rr = den
    assert 1.0e-5 < lr < rr < 1.0e5, f'density min: {lr}, max: {rr}'
    flu.get_component(1).den = (lr + rr) / 2.0

    # 计算粘性(通过二分法来寻找)
    lr, rr = 1.0e-6, 1.0e6
    while rr - lr > 1.0e-8:
        vis = (lr + rr) / 2.0
        flu.get_component(1).vis = vis
        if flu.vis < vis_times:
            lr = vis
        else:
            rr = vis
    assert 1.0e-5 < lr < rr < 1.0e5, f'viscosity min: {lr}, max: {rr}'
    flu.get_component(1).vis = (lr + rr) / 2.0

    # 根据组分1的密度和粘性来定义
    res.den *= flu.get_component(1).den
    res.vis *= flu.get_component(1).vis

    # 返回
    return res


def test():
    from zmlx import plot, add_axes2, curve
    import numpy as np

    c = 0.05

    # 溶剂
    solvent = Seepage.FluDef(den=1000.0, vis=1, specific_heat=4200)

    # 溶质
    solute = create_solute(
        solvent, c=c,
        den_times=1.05, vis_times=1.05)

    # 流体的定义
    flu = Seepage.FluData()
    flu.component_number = 2
    flu.get_component(0).den = solvent.get_den(10e6, 300)
    flu.get_component(0).vis = solvent.get_vis(10e6, 300)
    flu.get_component(1).den = solute.get_den(10e6, 300)
    flu.get_component(1).vis = solute.get_vis(10e6, 300)

    # 计算溶液的密度和粘性随着浓度的变化趋势
    vx = np.linspace(0.0, c*2, 100)
    y1 = []
    y2 = []

    for x in vx:
        # 创建流体
        flu.get_component(0).mass = 1.0 - x
        flu.get_component(1).mass = x
        y1.append(flu.den)
        y2.append(flu.vis)

    def show(fig):
        add_axes2(fig, curve, vx, y1, nrows=2, ncols=1, index=1,
                  xlabel='c', ylabel='Density')
        add_axes2(fig, curve, vx, y2, nrows=2, ncols=1, index=2,
                  xlabel='c', ylabel='Viscosity')

    plot(show, tight_layout=True)


if __name__ == '__main__':
    test()
