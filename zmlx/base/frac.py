from typing import Optional, Union, Callable

from zml import FractureNetwork, Tensor2, Coord2


def get_fn2(network: FractureNetwork, key: Optional[Union[str, int]] = None):
    """将裂缝网络转换为可用于绘图的fn2数据。

    宽度为-dn，颜色由key指定。

    Args:
        network (FractureNetwork): 裂缝网络对象。
        key (Union[str, int], optional): 指定颜色的属性索引。默认为None，表示使用宽度作为颜色。

    Returns:
        tuple: 包含三个列表的元组：
            - pos (list): 裂缝位置列表
            - w (list): 裂缝宽度列表（值为-dn）
            - c (list): 裂缝颜色列表，根据key的不同取值：
                * None: 使用宽度作为颜色
                * >=0: 使用指定属性作为颜色
                * -1: 使用ds作为颜色
                * -2: 使用-dn作为颜色
                * -3: 使用fp作为颜色
                * 其他: 使用宽度作为颜色
    """
    pos = []
    w = []
    c = []

    if isinstance(key, str):
        if key == 'fp':
            key = -3
        elif key == 'w':
            key = -2
        elif key == 's':
            key = -1

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
        if key == -3:
            c.append(fracture.fp)
            continue
        # 默认情况下，显示宽度
        c.append(-fracture.dn)
    return pos, w, c


def set_w_fixed(obj: Union[FractureNetwork.FractureData, FractureNetwork], w: float, k: Optional[float] = None,
                fp: Optional[float] = None):
    """
    设置p0和k，使得裂缝的宽度在接下来的迭代中能够固定到给定的值
    Args:
        obj: 裂缝单元(或者裂缝网络)数据
        w: 目标宽度值
        k: 刚度系数值，默认为None (此时使用默认值1e12)
        fp: 在给定w下的流体压力，默认为0
    Note:
        基于裂缝内的如下关系来设置
        fp = p0 + k * dn
    """
    assert w >= 0, f'Fracture width must be non-negative, but got {w}.'

    if k is None:
        k = 1.0e12  # make it a very big value
    else:
        assert k > 0, f'Fracture stiffness must be positive, but got {k}.'

    if fp is None:
        fp = 0.0
    else:
        assert fp >= 0, f'Fluid pressure must be non-negative, but got {fp}.'

    p0 = fp - k * (-w)

    if isinstance(obj, FractureNetwork.FractureData):
        f = obj
        f.p0 = p0
        f.k = k
        f.dn = -w
    else:
        assert isinstance(obj, FractureNetwork)
        for f in obj.fractures:
            f.p0 = p0
            f.k = k
            f.dn = -w


def set_p_fixed(obj: Union[FractureNetwork.FractureData, FractureNetwork], fp: float, k: Optional[float] = None):
    """
    设置p0和k，使得裂缝的流体压力在接下来的迭代中能够固定到给定的值
    Args:
        obj: 裂缝单元/裂缝网络
        fp: 目标流体压力值
        k: 刚度系数值，默认为None (此时使用默认值1e-6)
    Note:
        基于裂缝内的如下关系来设置
        fp = p0 + k * dn
    """
    assert fp >= 0, f'Fluid pressure must be non-negative, but got {fp}.'

    if k is None:
        k = 1.0e-6
    else:
        assert k > 0, f'Fracture stiffness must be positive, but got {k}.'

    if isinstance(obj, FractureNetwork.FractureData):
        f = obj
        f.p0 = fp
        f.k = k
    else:
        assert isinstance(obj, FractureNetwork)
        for f in obj.fractures:
            f.p0 = fp
            f.k = k


def set_local_stress(obj: Union[FractureNetwork.Fracture, FractureNetwork], global_stress: Union[Tensor2, Callable],
                     fa_yy: Optional[int] = None, fa_xy: Optional[int] = None):
    """
    设置裂缝的局部应力属性.
    Args:
        obj: 需要设置应力属性的裂缝或者裂缝网络
        fa_yy: 法向应力属性ID
        fa_xy: 切向应力属性ID
        global_stress: 全局坐标系下面的应力张量
    """
    if isinstance(obj, FractureNetwork.Fracture):
        x0, y0, x1, y1 = obj.pos
        local_coord = Coord2(origin=[0, 0], xdir=[x1 - x0, y1 - y0])
        global_coord = Coord2()
        if isinstance(global_stress, Tensor2):
            local_stress = local_coord.view(coord=global_coord, o=global_stress)
        else:
            assert callable(global_stress), f"The global_stress must be a callable, but got: {type(global_stress)}."
            stress = global_stress((x0 + x1) / 2, (y0 + y1) / 2)
            assert isinstance(stress, Tensor2), f"The global_stress should be Tensor2, but got: {type(stress)}."
            local_stress = local_coord.view(coord=global_coord, o=stress)
        assert isinstance(local_stress, Tensor2)
        yy = local_stress.yy
        xy = local_stress.xy
        if isinstance(fa_yy, int):
            obj.set_attr(fa_yy, yy)
        if isinstance(fa_xy, int):
            obj.set_attr(fa_xy, xy)
        return yy, xy
    else:  # 设置裂缝网络的
        assert isinstance(obj, FractureNetwork)
        for f in obj.fractures:
            set_local_stress(f, fa_yy=fa_yy, fa_xy=fa_xy, global_stress=global_stress)
        return None


def set_h(obj: Union[FractureNetwork.Fracture, FractureNetwork], h: Union[float, Callable]):
    """
    设置裂缝的高度属性.
    Args:
        obj: 需要设置高度属性的裂缝或者裂缝网络
        h: 裂缝的高度
    """
    if isinstance(obj, FractureNetwork.Fracture):
        if callable(h):
            x0, y0, x1, y1 = obj.pos
            obj.h = h((x0 + x1) / 2, (y0 + y1) / 2)
        else:
            obj.h = h
    else:  # 设置裂缝网络的
        assert isinstance(obj, FractureNetwork)
        for f in obj.fractures:
            set_h(f, h=h)
