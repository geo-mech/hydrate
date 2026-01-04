"""
关于裂缝网络相关的基础的操作。不依赖于frac中的其他的模块。
"""
import math
from typing import Optional, Union, Callable, Tuple, List

from zmlx.exts import FractureNetwork, Tensor2, Coord2
from zmlx.geometry import point_distance


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
        if key == 'p' or key == 'fp' or key == 'pressure':
            key = -3
        elif key == 'w' or key == 'width':
            key = -2
        elif key == 's' or key == 'shear':
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


def _set_fracture_attrs(obj: Union[FractureNetwork.FractureData, FractureNetwork], **opts):
    """
    设置裂缝的一些属性
    """
    if isinstance(obj, FractureNetwork.FractureData):
        for k, v in opts.items():
            if isinstance(k, str) and v is not None:
                setattr(obj, k, v)
    else:
        assert isinstance(obj, FractureNetwork)
        for f in obj.fractures:
            _set_fracture_attrs(f, **opts)


def set_w_fixed(
        obj: Union[FractureNetwork.FractureData, FractureNetwork], w: float, k: Optional[float] = None,
        p: Optional[float] = None
):
    """
    设置p0和k，使得裂缝的宽度在接下来的迭代中能够固定到给定的值
    Args:
        obj: 裂缝单元(或者裂缝网络)数据
        w: 目标宽度值
        k: 刚度系数值，默认为None (此时使用默认值1e12)
        p: 在给定w下的流体压力，默认为0
    Note:
        基于裂缝内的如下关系来设置
        p = p0 + k * dn
    """
    assert w >= 0, f'Fracture width must be non-negative, but got {w}.'

    if k is None:
        k = 1.0e12  # make it a very big value
    else:
        assert k > 0, f'Fracture stiffness must be positive, but got {k}.'

    if p is None:
        p = 0.0
    else:
        assert p >= 0, f'Fluid pressure must be non-negative, but got {p}.'

    _set_fracture_attrs(obj, p0=p + k * w, k=k, dn=-w)


def set_p_fixed(
        obj: Union[FractureNetwork.FractureData, FractureNetwork], p: float, k: Optional[float] = None,
        w: Optional[float] = None
):
    """
    设置p0和k，使得裂缝的流体压力在接下来的迭代中能够固定到给定的值
    Args:
        obj: 裂缝单元/裂缝网络
        p: 目标流体压力值
        k: 刚度系数值，默认为None (此时使用默认值1e-6)
        w: 目标裂缝宽度
    Note:
        基于裂缝内的如下关系来设置
        p = p0 + k * dn
    """
    assert p >= 0, f'Fluid pressure must be non-negative, but got {p}.'

    if k is None:
        k = 1.0e-6
    else:
        assert k > 0, f'Fracture stiffness must be positive, but got {k}.'

    if w is None:
        w = 0.0
    else:
        assert w >= 0, f'Fracture width must be non-negative, but got {w}.'

    _set_fracture_attrs(obj, p0=p + k * w, k=k, dn=-w)


def set_local_stress(
        obj: Union[FractureNetwork.Fracture, FractureNetwork],
        global_stress: Union[Tensor2, Callable],
        fa_yy: Optional[int] = None, fa_xy: Optional[int] = None,
        global_coord: Optional[Coord2] = None,
):
    """
    设置裂缝的局部应力属性.
    Args:
        obj: 需要设置应力属性的裂缝或者裂缝网络
        fa_yy: 法向应力属性ID
        fa_xy: 切向应力属性ID
        global_stress: 全局坐标系下面的应力张量（或者一个根据x、y坐标来返回应力张量的函数）
        global_coord: 全局坐标系，默认为Coord2()
    """
    if isinstance(obj, FractureNetwork.Fracture):
        x0, y0, x1, y1 = obj.pos
        local_coord = Coord2(origin=[0, 0], xdir=[x1 - x0, y1 - y0])
        if global_coord is None:
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
        if global_coord is None:
            global_coord = Coord2()
        for f in obj.fractures:
            set_local_stress(f, fa_yy=fa_yy, fa_xy=fa_xy, global_stress=global_stress, global_coord=global_coord)
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


def get_nearest_vertex(
        network: FractureNetwork, x: float, y: float, dist_max: float = 1e100
) -> Optional[int]:
    """
    获取距离目标位置最近的Vertex的ID
    Args:
        network: 裂缝网络
        x: 目标位置的x坐标
        y: 目标位置的y坐标
        dist_max: 最大距离，默认为1e100
    Returns:
        最近的Vertex的ID
    """
    assert dist_max > 0, f'dist_max must be non-negative, but got {dist_max}.'
    res = None
    dist_min = dist_max
    for idx in range(network.vertex_number):
        v = network.get_vertex(idx)
        assert v is not None
        dist = math.sqrt((v.x - x) ** 2 + (v.y - y) ** 2)
        if dist < dist_min:
            res = idx
            dist_min = dist
    return res


def set_vertex_attr(
        obj: Union[FractureNetwork.VertexData, FractureNetwork],
        index: int, value: Union[float, Callable]
):
    """
    设置Vertex的属性
    Args:
        obj: 裂缝顶点/裂缝网络
        index: Vertex的属性ID
        value: 属性值
    Returns:
        None
    """
    if isinstance(obj, FractureNetwork.VertexData):
        if callable(value):
            x, y = obj.pos
            v = value(x, y)
        else:
            v = value
        obj.set_attr(index=index, value=v)
    else:
        assert isinstance(obj, FractureNetwork)
        for f in obj.vertexes:
            set_vertex_attr(f, index=index, value=value)


def set_fracture_attr(
        obj: Union[FractureNetwork.FractureData, FractureNetwork.Fracture, FractureNetwork],
        index: int, value: Union[float, Callable]
):
    """
    设置裂缝的属性
    Args:
        obj: 裂缝顶点/裂缝网络
        index:裂缝的属性ID
        value: 属性值
    Returns:
        None
    """
    if isinstance(obj, FractureNetwork.FractureData):
        if callable(value):
            assert isinstance(obj, FractureNetwork.Fracture)
            x, y = obj.center
            v = value(x, y)
        else:
            v = value
        obj.set_attr(index=index, value=v)
    else:
        assert isinstance(obj, FractureNetwork)
        for f in obj.fractures:
            set_fracture_attr(f, index=index, value=value)


def clamp_dn(
        obj: Union[FractureNetwork.FractureData, FractureNetwork.Fracture, FractureNetwork],
        left: Optional[float] = None, right: Optional[float] = None
):
    """
    修改裂缝dn属性，使得其在给定的范围内
    Args:
        obj: 裂缝顶点/裂缝网络
        left: dn的左边界
        right: dn的右边界
    Returns:
        None
    """
    if isinstance(obj, FractureNetwork.FractureData):
        if left is not None or right is not None:
            if left is None:
                assert right is not None, f'right must be not None, but got {right}.'
                assert right <= 0, f'right must be <= 0, but got right={right}.'
                obj.dn = min(obj.dn, right)
            elif right is None:
                assert left is not None, f'left must be not None, but got {left}.'
                assert left <= 0, f'left must be <= 0, but got left={left}.'
                obj.dn = max(obj.dn, left)
            else:
                assert left is not None and right is not None
                if left > right:
                    left, right = right, left
                assert left <= right <= 0, f'left must be <= right <= 0, but got left={left}, right={right}.'
                obj.dn = min(max(obj.dn, left), right)
    else:
        assert isinstance(obj, FractureNetwork)
        if left is not None or right is not None:
            for f in obj.fractures:
                clamp_dn(f, left=left, right=right)


def clamp_width(obj: Union[FractureNetwork.FractureData, FractureNetwork.Fracture, FractureNetwork],
                left: Optional[float] = None, right: Optional[float] = None):
    """
    修改dn属性，使得裂缝宽度(=-dn)位于给定的范围内
    Args:
        obj: 裂缝顶点/裂缝网络
        left: 宽度的左边界
        right: 宽度的右边界
    Returns:
        None
    """
    clamp_dn(obj, left=-right if right is not None else None, right=-left if left is not None else None)


def get_dn_range(network: FractureNetwork) -> Tuple[Optional[float], Optional[float]]:
    """
    返回dn的范围
    Args:
        network: 裂缝网络

    Returns:
        (dn_min, dn_max)
    """
    dn_min: Optional[float] = None
    dn_max: Optional[float] = None
    for f in network.fractures:
        dn = f.dn
        if dn_min is None:
            dn_min = dn
        else:
            dn_min = min(dn_min, dn)
        if dn_max is None:
            dn_max = dn
        else:
            dn_max = max(dn_max, dn)

    return dn_min, dn_max


def get_ds_range(network: FractureNetwork) -> Tuple[Optional[float], Optional[float]]:
    """
    返回ds的范围
    Args:
        network: 裂缝网络

    Returns:
        (ds_min, ds_max)
    """
    ds_min: Optional[float] = None
    ds_max: Optional[float] = None
    for f in network.fractures:
        ds = f.ds
        if ds_min is None:
            ds_min = ds
        else:
            ds_min = min(ds_min, ds)
        if ds_max is None:
            ds_max = ds
        else:
            ds_max = max(ds_max, ds)

    return ds_min, ds_max


def get_fp_range(network: FractureNetwork) -> Tuple[Optional[float], Optional[float]]:
    """
    返回fp的范围
    Args:
        network: 裂缝网络

    Returns:
        (fp_min, fp_max)
    """
    fp_min: Optional[float] = None
    fp_max: Optional[float] = None
    for f in network.fractures:
        fp = f.fp
        if fp_min is None:
            fp_min = fp
        else:
            fp_min = min(fp_min, fp)
        if fp_max is None:
            fp_max = fp
        else:
            fp_max = max(fp_max, fp)

    return fp_min, fp_max


def create_network(trajectory: List[float], l_eps: float = 1.0e-6):
    """
    根据轨迹来创建裂缝网络.
    """

    assert isinstance(trajectory, list), f'fracture {trajectory} is not a list'
    assert len(trajectory) % 2 == 0
    assert len(trajectory) >= 4

    points = []
    for i in range(len(trajectory) // 2):
        points.append([trajectory[i * 2], trajectory[i * 2 + 1]])

    # 将各个点作为Vertex添加
    network = FractureNetwork()
    for p in points:
        if p[0] is None or p[1] is None:
            continue

        vertex = network.get_nearest_vertex(pos=p)
        if vertex is None:
            network.add_vertex(x=p[0], y=p[1])
            continue

        if point_distance(p, vertex.pos) > l_eps:
            network.add_vertex(x=p[0], y=p[1])
            continue

    # 创建裂缝单元
    for i in range(len(points) - 1):
        p0, p1 = points[i], points[i + 1]
        if p0[0] is None or p0[1] is None or p1[0] is None or p1[1] is None:
            continue
        else:
            v0 = network.get_nearest_vertex(pos=p0)
            v1 = network.get_nearest_vertex(pos=p1)
            assert v0 is not None
            assert v1 is not None
            if v0.index != v1.index:
                network.add_fracture(first=v0.index, second=v1.index)

    return network


def test_1():
    trajectory = [
        0, 0, 1, 0, 2, 0, 3, 0, None, None, 3, 0, 3, 1
    ]
    network = create_network(trajectory)
    print(network)
