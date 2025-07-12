from zml import Seepage
from zmlx.fluid import ch4


def get_test_fludefs():
    """
    构建一个用于测试的流体定义 (气、水、油三相流动)
    """
    gas = ch4.create(
        t_min=270, t_max=400, p_min=1e6, p_max=40e6, name='gas')

    water = Seepage.FluDef(
        den=1000.0, vis=1.0e-3, specific_heat=4200, name='water')

    oil = Seepage.FluDef(
        den=900.0, vis=1.0e-2, specific_heat=2000, name='oil')

    return [gas, water, oil]


def test():
    fludefs = get_test_fludefs()
    for flu in fludefs:
        print(flu)
    print(fludefs)


if __name__ == '__main__':
    test()
