from zmlx.react import endothermic
from zmlx.react.add_reaction import add_reaction


def create(left, right, temp, heat, rate, fa_t=None, fa_c=None):
    """
    创建一个物质燃烧的反应. 其中left是燃烧的物质，右侧right是燃烧的产物. temp是燃点，即只有温度超过这个临界值，燃烧反应才会发生.
        heat为燃烧释放的热量，必须大于0;  rate是燃烧的速率(应该是一个和温度相关的量，但是目前简化起见，先用一个常量吧).
        fa_t和fa_c为流体温度和比热的属性值.

    注：
        此反应目前尚未测试.
    """
    teq = 2e3  # 定义燃烧能达到的最高的温度(类似于这个反应的平衡温度)

    # 创建一个映射
    #    其中的t为实际温度偏离平衡温度的数值，q为在该温度下反应的速率.
    #    这里要做的，是在实际温度低于燃点的时候，让反应的速率等于0，从而确保只有温度大于燃点，反应才可以启动.
    t = [-1e4, temp - teq, temp - teq + 1, -1, 0, 1e4]
    q = [0, 0, -rate, -rate, 0, 0]
    return endothermic.create(left=right, right=left,  # 交换左右两侧
                              temp=teq,  # 用于定义能量的参考温度
                              heat=heat,  # 在参考温度下，1kg物质产生的热量
                              rate=1,  # 无用的参数
                              fa_t=fa_t, fa_c=fa_c,
                              l2r=False, r2l=True,  # 仅仅允许从右侧向左侧反应
                              p2t=([0.01e6, 100e6], [teq, teq]),  # 定义燃烧能达到的最高的温度
                              t2q=(t, q)
                              )


def test(t_ini=510):
    """
    测试
    """
    import numpy as np
    print(f'\n\nTest when initial temperature is {t_ini}')
    from zml import Seepage, get_pointer64

    model = Seepage()
    cell = model.add_cell()
    cell.fluid_number = 3
    fa_t = 0
    fa_c = 1
    for i in range(3):
        f = cell.get_fluid(i)
        f.mass = 1
        f.set_attr(fa_t, t_ini)
        f.set_attr(fa_c, 1000)
    r = create(left=[(0, 0.5), (1, 0.5)], right=[(2, 1.0)], temp=500, heat=1.0e6, rate=1.0e-2, fa_t=fa_t, fa_c=fa_c)
    add_reaction(model, r)

    buf = np.zeros(shape=model.cell_number)
    for step in range(20):
        model.get_reaction(0).react(model, 1.0, buf=get_pointer64(buf))
        print(
            f'{buf}:  {cell.get_fluid(0).mass}  {cell.get_fluid(1).mass}  {cell.get_fluid(2).mass}  {cell.get_fluid(0).get_attr(fa_t)}  {cell.get_fluid(1).get_attr(fa_t)}  {cell.get_fluid(2).get_attr(fa_t)}')


if __name__ == '__main__':
    test(510)
    test(490)
