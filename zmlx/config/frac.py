from zml import FractureNetwork


def get_fn2(network: FractureNetwork, key=None):
    """
    转化为可以用来绘图的fn2数据. 其中宽度为-dn，颜色由key指定

    参数：
        network (FractureNetwork)：裂缝网络对象。
        key (int)：指定颜色的属性索引，默认为 None。

    返回：
        tuple：包含位置、宽度和颜色数据的元组。
    """
    pos = []
    w = []
    c = []

    for fracture in network.fractures:
        pos.append(fracture.pos)
        w.append(-fracture.dn)

        # 默认情况下，显示宽度
        if key is None:
            c.append(-fracture.dn)
            continue
        if key >= 0:
            c.append(fracture.get_attr(key))
            continue
        if key == -1:
            c.append(fracture.ds)
            continue
        if key == -2:
            c.append(-fracture.dn)
            continue
        # 默认情况下，显示宽度
        c.append(-fracture.dn)
    return pos, w, c
