"""
定义FractureNetwork类的扩展接口
"""

from zml import FractureNetwork, Tensor2, LinearExpr, Seepage


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


def get_average_length(network: FractureNetwork):
    """计算裂缝网络中所有裂缝的平均长度。
    Args:
        network (FractureNetwork): 裂缝网络对象。
    Returns:
        float: 所有裂缝的平均长度 (当没有裂缝的时候，返回None)
    """
    if network.fracture_number == 0:
        return
    total_length = 0
    for fracture in network.fractures:
        assert isinstance(fracture, FractureNetwork.Fracture)
        total_length += fracture.length
    return total_length / network.fracture_number


def get_average_height(network: FractureNetwork):
    """计算裂缝网络中所有裂缝的平均高度。
    Args:
        network (FractureNetwork): 裂缝网络对象。
    Returns:
        float: 所有裂缝的平均高度  (当没有裂缝的时候，返回None)
    """
    if network.fracture_number == 0:
        return
    total_height = 0
    for fracture in network.fractures:
        assert isinstance(fracture, FractureNetwork.Fracture)
        total_height += fracture.h
    return total_height / network.fracture_number


def set_local_stress(
        network: FractureNetwork, fa_yy, fa_xy, stress):
    """
    设置原始的地应力。在程序计算的时候，需要用到各个裂缝单元的位置的法向和切向应力。
    这个函数就是根据
    给定的应力张量（或者是应力张量在控件的分布）来设置各个裂缝单元位置的法向和切向应力。

    Args:
        stress: 原始的地应力，应该是一个Tensor2，或者是一个位置x和y的函数，
                且函数返回一个Tensor2
        network: 需要设置的裂缝网络
        fa_xy: 存储局部剪切应力的属性
        fa_yy: 存储局部的法向应力的属性
    """
    local_stress = Tensor2()
    for fracture in network.fractures:
        assert isinstance(fracture, FractureNetwork.Fracture)

        if callable(stress):
            temp = stress(*fracture.center)
        else:
            temp = stress

        if isinstance(temp, Tensor2):
            temp.get_rotate(fracture.angle, buffer=local_stress)
            fracture.set_attr(fa_xy, local_stress.xy)
            fracture.set_attr(fa_yy, local_stress.yy)
        else:
            fracture.set_attr(fa_xy, 0)
            fracture.set_attr(fa_yy, 0)


def reset_flu_expr(network: FractureNetwork):
    """重置裂缝网络中每个裂缝的流体表达式。

    Args:
        network (FractureNetwork): 需要重置的裂缝网络

    Returns:
        None
    """
    for fracture in network.fractures:
        assert isinstance(fracture, FractureNetwork.Fracture)
        fracture.flu_expr = LinearExpr.create(index=fracture.index)


def set_cell_pos(
        model: Seepage, network: FractureNetwork, z_coord=0.0):
    """设置Seepage模型中每个单元格的位置。所有的Cell的z坐标是一样的

    Args:
        model (Seepage): 需要设置的Seepage模型
        network (FractureNetwork): 裂缝网络对象
        z_coord (float): network所在的z坐标

    Returns:
        None
    """
    for idx in range(model.cell_number):
        x, y = network.get_fracture(idx).center
        model.get_cell(idx).pos = [x, y, z_coord]


def create_network(
        fractures, *, lave, height=50.0):
    """
    创建固体计算的模型.
    fractures的每一个元素代表一个裂缝，且裂缝fracture是一个长度为4的list，
    格式为 x0  y0  x1  y1.
    """
    from zmlx.geometry.dfn2 import get_avg_length as get_dfn2_avg_length
    assert len(fractures) > 0, 'There is no fracture.'

    if lave is None:
        lave = get_dfn2_avg_length(fractures) / 5.0
        print(f'Warning, lave not given, use lave: {lave}')

    data = FractureNetwork.FractureData.create(
        h=height, dn=0, ds=0, f=0.9, p0=1e6, k=0.0)

    network = FractureNetwork()

    for fracture in fractures:
        assert len(fracture) == 4
        network.add_fracture(pos=fracture, lave=lave, data=data)

    return network  # 返回生成的裂缝网络


def set_aperture_fixed(obj, aperture, k=1.0e11):
    """
    设置裂缝的边界条件，是的在后续的迭代中，裂缝的开度可以固定在给定的aperture附近
    Args:
        obj: 目标的裂缝或者裂缝的网络
        aperture: 目标的开度
            (当obj是裂缝网络的时候，其可以是一个函数，接受裂缝的索引作为参数)
        k: 刚度系数。这个数值越大，则对裂缝开度的约束就越强

    Returns:
        None
    """
    if isinstance(obj, FractureNetwork.FractureData):
        assert aperture >= 0, (f'aperture must be greater equal than 0, '
                               f'but got {aperture}')
        obj.p0 = k * aperture
        obj.k = k
        obj.dn = -aperture
    else:
        assert isinstance(obj, FractureNetwork)
        if callable(aperture):
            for index in range(obj.fracture_number):
                value = max(0, aperture(index))
                set_aperture_fixed(obj.get_fracture(index), value, k)
        else:
            for item in obj.fractures:
                set_aperture_fixed(item, aperture, k)
