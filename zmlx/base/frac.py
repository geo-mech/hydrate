from zmlx.exts.base import FractureNetwork


def get_fn2(network: FractureNetwork, key=None):
    """将裂缝网络转换为可用于绘图的fn2数据。

    宽度为-dn，颜色由key指定。

    Args:
        network (FractureNetwork): 裂缝网络对象。
        key (int, optional): 指定颜色的属性索引。默认为None，表示使用宽度作为颜色。

    Returns:
        tuple: 包含三个列表的元组：
            - pos (list): 裂缝位置列表
            - w (list): 裂缝宽度列表（值为-dn）
            - c (list): 裂缝颜色列表，根据key的不同取值：
                * None: 使用宽度作为颜色
                * >=0: 使用指定属性作为颜色
                * -1: 使用ds作为颜色
                * -2: 使用-dn作为颜色
                * 其他: 使用宽度作为颜色
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
