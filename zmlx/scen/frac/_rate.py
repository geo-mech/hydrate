"""
计算到尖端的流量
"""
from typing import List


def _get_rate(inlet_pre: float, resists: List[float], outlet_pres: List[float]):
    """
    给定入口的压力，出口的压力，阻力系数，计算流量
    Args:
        inlet_pre: 入口的的压力
        resists: 阻力系数
        outlet_pres: 出口压力
    Returns:
        总的流量
    """
    assert len(resists) == len(outlet_pres), f'the length of resists and outlet_pres must match'
    res = 0.0
    for i in range(len(resists)):
        resist = resists[i]
        assert resist > 0, f'resist {resist} should be greater than 0'
        q = (inlet_pre - outlet_pres[i]) / resist
        if q > 0:
            res += q
    return res


def get_rates(q_inject: float, resists: List[float], outlet_pres: List[float]):
    """
    根据流动的阻力，扩展的压力，计算流量。
    Args:
        q_inject: 注入的总的速率
        resists: 从入口到各个出口的阻力系数
        outlet_pres: 各个出口的临界压力
    Returns:
        各个出口的流量。确保流量非负，且流量的总和等于注入的流量
    """
    assert len(resists) == len(outlet_pres), f'the length of resists and outlet_pres must match'
    assert len(resists) > 0, f'reists must be non-empty'
    assert q_inject > 0, f'q_inject {q_inject} should be greater than 0'

    outlet_p_min: float = min(outlet_pres)
    for i in range(len(outlet_pres)):
        outlet_pres[i] -= outlet_p_min

    inlet_p_max = max(outlet_pres)
    while _get_rate(inlet_pre=inlet_p_max, resists=resists, outlet_pres=outlet_pres) < q_inject:
        inlet_p_max += 1.0
        inlet_p_max *= 2.0

    inlet_p_min = 0.0
    while inlet_p_max - inlet_p_min > (inlet_p_max + inlet_p_min) * 1.0e-4:
        q = _get_rate(inlet_pre=(inlet_p_max + inlet_p_min) / 2.0, resists=resists, outlet_pres=outlet_pres)
        if q < q_inject:
            inlet_p_min = (inlet_p_max + inlet_p_min) / 2.0
        else:
            inlet_p_max = (inlet_p_max + inlet_p_min) / 2.0

    inlet_pre = (inlet_p_max + inlet_p_min) / 2.0

    q_sum = 0.0
    rates: List[float] = []
    for i in range(len(resists)):
        resist = resists[i]
        assert resist > 0, f'resist {resist} should be greater than 0'
        q = (inlet_pre - outlet_pres[i]) / resist
        if q > 0:
            rates.append(q)
            q_sum += q
        else:
            rates.append(0.0)

    ratio = q_inject / max(q_sum, 1.0e-20)
    for i in range(len(rates)):
        rates[i] *= ratio

    return rates


def test_1():
    q_inject: float = 1.0
    resists: List[float] = [1, 2, 3, 4, 5]
    outlet_pres: List[float] = [0.4, 0, 0, 0, 0]
    rates = get_rates(q_inject, resists, outlet_pres)
    print(rates)
    print(sum(rates))


if __name__ == '__main__':
    test_1()
