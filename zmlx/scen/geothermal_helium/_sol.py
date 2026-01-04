from typing import Callable, Union, Optional

from zmlx.tfc import flu_keys, Seepage, cell_keys


def update_solubility(model: Seepage, ca: int, sol: Union[Callable, float]):
    """
    更新溶解度属性(根据压力和温度计算)
    Args:
        model: 计算模型
        ca: 溶解度属性的索引
        sol: 获取溶解度的函数 get_sol(pressure, temperature) -> solubility
    Returns:
        None
    """
    fid = model.find_fludef('liq')
    assert fid is not None
    assert len(fid) > 0

    fa_t = flu_keys(model).temperature
    for cell in model.cells:
        if callable(sol):
            liq = cell.get_fluid(*fid)
            assert liq is not None
            temp = liq.get_attr(index=fa_t)
            pressure = cell.pre
            v = sol(pressure, temp)
            assert 0.0 <= v <= 0.1
            cell.set_attr(ca, v)
        else:
            cell.set_attr(ca, sol)


def get_he_sol(pressure, temperature):
    """
    计算氦气的溶解度
    todo:
        实现氦气的溶解度计算
    """
    return 0.01


def get_n2_sol(pressure, temperature):
    """
    计算氮气的溶解度
    todo:
        实现氮气的溶解度计算
    """
    return 0.01


def update_he_sol(model: Seepage, sol: Optional[Union[float, Callable]] = None):
    """
    更新氦气的溶解度
    """
    if sol is None:
        sol = get_he_sol
    ca = cell_keys(model)
    update_solubility(model, ca=ca.he_sol, sol=sol)


def update_n2_sol(model: Seepage, sol: Optional[Union[float, Callable]] = None):
    """
    更新氮气的溶解度
    """
    if sol is None:
        sol = get_n2_sol
    ca = cell_keys(model)
    update_solubility(model, ca=ca.n2_sol, sol=sol)
