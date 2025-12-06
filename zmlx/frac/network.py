from zmlx.base.zml import FractureNetwork
from zmlx.geometry.dfn2 import get_avg_length as get_dfn2_avg_length


def create_network(
        fractures, *, l_ave=None, height=50.0, data=None):
    """
    根据给定的离散网络数据，创建裂缝网络模型。
        fractures的每一个元素代表一个裂缝，且裂缝fracture是一个长度为4的list，
        格式为 x0  y0  x1  y1.
    """

    assert len(fractures) > 0, 'There is no fracture.'

    if l_ave is None:
        l_ave = get_dfn2_avg_length(fractures) / 5.0
        print(f'Warning, l_ave not given, use l_ave: {l_ave}')

    if data is None:
        data = FractureNetwork.FractureData.create(
            h=height, dn=0, ds=0, f=0.9, p0=1e6, k=0.0)
    else:
        assert isinstance(data, FractureNetwork.FractureData)

    network = FractureNetwork()

    for fracture in fractures:
        assert len(fracture) == 4
        network.add_fracture(pos=fracture, lave=l_ave, data=data)

    return network  # 返回生成的裂缝网络
