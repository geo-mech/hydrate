"""
标记可以扩展的裂缝的尖端
"""
import random
from typing import Set, List, Dict, Tuple, Optional

from zmlx.exts import FractureNetwork
from zmlx.geometry.segment import seg_point_distance
from zmlx.scen.frac._base import get_nearest_vertex
from zmlx.scen.frac._rate import get_rates
from zmlx.scen.frac._resist import get_resist
from zmlx.scen.frac._topo import get_topo


def _extendable(network: FractureNetwork, vertex_index: int, dist_min: Optional[float] = None) -> bool:
    """
    根据距离，来判断一个Vertex是否应该扩展.
    """
    if dist_min is None:
        return True

    vertex = network.get_vertex(vertex_index)
    assert vertex is not None

    special_fractures: Set[int] = set()  # 避免去检查这些裂缝的距离
    for f0 in vertex.fractures:
        special_fractures.add(f0.index)
        for v1 in f0.vertexes:
            for f1 in v1.fractures:
                special_fractures.add(f1.index)

    x2, y2 = vertex.pos
    for f in network.fractures:
        if f.index in special_fractures:
            continue
        x0, y0, x1, y1 = f.pos
        if seg_point_distance(seg=[(x0, y0), (x1, y1)], point=(x2, y2)) < dist_min:
            return False

    return True


def update_wmin(
        network: FractureNetwork, *,
        x_inj: float, y_inj: float, q_inj: float, va_wmin: int, fa_resist: int, va_pc: int,
        dist_min: Optional[float] = None
) -> None:
    """
    基于渗流，计算各个裂缝尖端扩展的速率，并标记各个裂缝尖端是否能够扩展。对于能够扩展的尖端，将wmin属性设置为
    一个比较小的，容易达到的数值；对于其他不能扩展的尖端，将wmin属性设置为非常大，不可能达到的数值。
    这里，wmin属性表示一个裂缝尖端能够扩展所容许的最小的裂缝宽度。如果间断裂缝的开度小于此数值，则无论其他条件
    如何，裂缝都不会在这个尖端扩展。
    Args:
        network: 裂缝网络对象
        x_inj: 注入点的x坐标
        y_inj: 注入点的y坐标
        q_inj: 注入流量
        va_wmin: Vertex的wmin属性的ID
        fa_resist: 裂缝阻力系数(在流量等于1的时候，单位长度裂缝上的流体阻力)属性的ID
        va_pc: Vertex的临界扩展压力pc属性的ID
        dist_min: 能够扩展的裂缝尖端具有已有裂缝的临界距离
    Returns:
        None
    """
    # step 0. 设置裂缝的一些默认的属性
    for v in network.vertexes:
        v.set_attr(index=va_wmin, value=1.0e6)  # 可以扩展的最小的宽度，默认设置为非常大的数值，表示禁止扩展

    # step 1. 获得结构
    i_inj = get_nearest_vertex(network, x=x_inj, y=y_inj)
    if i_inj is None:
        return

    v_tips, v_fids = get_topo(network=network, vertex_start=i_inj)  # 此时，将网络表征成一串串的裂缝单元
    if v_tips is None or v_fids is None:
        return
    assert len(v_tips) == len(
        v_fids), f'v_tips (len={len(v_tips)}) and v_fids (len={len(v_fids)}) have different lengths'

    # step 2. 计算阻力系数
    vertexes_set: Set[int] = set()  # 所有的顶点的ID
    for tips in v_tips:
        assert len(tips) == 2
        for i in tips:
            assert 0 <= i < network.vertex_number
            vertexes_set.add(i)

    vertexes: List[int] = list(vertexes_set)
    local_ids: Dict[int, int] = {}  # 根据顶点的全局ID，返回局部ID
    for i in range(len(vertexes)):
        local_ids[vertexes[i]] = i

    # 顶点序号对(局部ID)
    links: List[Tuple[int, int]] = [(local_ids[tips[0]], local_ids[tips[1]]) for tips in v_tips]
    # 对应的阻力
    link_resists: List[float] = []
    for fids in v_fids:
        assert len(fids) > 0
        resist: float = 0
        for fid in fids:
            assert 0 <= fid < network.fracture_number
            f = network.get_fracture(fid)
            assert f is not None
            a = f.get_attr(index=fa_resist, left=1.0e-10, right=1.0e20, default_val=None)
            assert a is not None
            resist += a * f.length
        link_resists.append(resist)

    # 注入点的ID (局部ID)
    start: int = local_ids[i_inj]
    # 尖端的局部ID
    ends: List[int] = []
    for tips in v_tips:
        assert len(tips) == 2
        for i in tips:
            assert 0 <= i < network.vertex_number
            v = network.get_vertex(i)
            assert v is not None
            if i != i_inj and v.fracture_number == 1:  # 找到了裂缝尖端 (也就是忽略了内部的顶点)
                if _extendable(network, vertex_index=v.index, dist_min=dist_min):
                    ends.append(local_ids[i])

    # 通过渗流计算，来评估从注入点，到各个ends之间的阻力
    end_resists = get_resist(links=links, link_resists=link_resists, start=start, ends=ends)

    # step 3. 计算流体流量
    outlet_pres: List[float] = []
    for i in ends:
        assert 0 <= i < len(vertexes)
        v = network.get_vertex(vertexes[i])
        assert v is not None
        assert v.fracture_number == 1
        a = v.get_attr(index=va_pc, left=-1e20, right=1.0e20, default_val=None)
        assert a is not None, f'pc is None for vertex {i}'
        outlet_pres.append(a)

    end_rates: List[float] = get_rates(q_inject=q_inj, resists=end_resists, outlet_pres=outlet_pres)
    assert len(end_rates) == len(ends)

    # step 4. 按照概率扩展顶点(将一些裂缝顶点设置为可以扩展的).
    for i in range(len(ends)):
        q = end_rates[i]
        assert 0 <= q <= q_inj
        if random.uniform(0, 1) < q / q_inj:
            v = network.get_vertex(vertexes[ends[i]])
            assert v is not None, f'vertex {vertexes[ends[i]]} is None'
            v.set_attr(index=va_wmin, value=1.0e-10)
