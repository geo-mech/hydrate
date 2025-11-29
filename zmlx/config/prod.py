"""
控制用来生产的Cell的压力。
"""

from zmlx.alg.interp import interp1
from zmlx.base.seepage import get_time
from zmlx.base.zml import Seepage
from zmlx.config.alg import settings

text_key = 'prod_settings'


def _modify_pore(cell: Seepage.CellData, target_fp):
    """
    通过调整pore的方式来控制压力
    """
    target_fv = max(0.0, cell.p2v(target_fp))
    dv = cell.fluid_vol - target_fv
    if dv > 0:  # 只允许增加，从而使得只是用来生产流体
        cell.v0 = max(0.0, cell.v0 + dv)


def get_settings(model: Seepage):
    """
    读取设置
    """
    return settings.get(model, text_key=text_key)


def set_settings(model: Seepage, data):
    """
    写入设置
    """
    settings.put(model, text_key=text_key, data=data)


def add_setting(model: Seepage,
                index=None, pos=None, t=None, p=None):
    """
    添加设置. 其中index为cell的序号
    (当index为None的时候，使用pos最为接近的Cell)
    """
    if index is None and pos is not None:
        # 当index没有给定的时候，使用pos来找到最为接近的index
        cell = model.get_nearest_cell(pos=pos)
        if cell is not None:
            index = cell.index

    if index is None or t is None or p is None:  # 这些数据必须给定.
        return

    assert isinstance(index, int), f'The index should be integer type'

    if index < 0:
        index += model.cell_number

    if index < model.cell_number:  # 添加一个用于生产的确定压力的设置.
        assert len(t) == len(p) and len(t) >= 2
        data = get_settings(model)
        assert isinstance(data, list)
        # 检查idx是否已经被设置了
        exists = False
        for item in data:
            assert isinstance(item, dict)
            if index == item.get('index'):
                exists = True
                break
        if not exists:  # 只有当不存在的时候，才去设置
            data.append({'index': index, 'time': t, 'pressure': p})
            set_settings(model, data=data)


def iterate(model: Seepage, *, time=None):
    """
    根据此刻的时间来更新pore。
    注意：
        后续，这个函数有效率优化的空间。这里，可能会有一个比较长的
        向量以文本的形式存储。这可能会带来一定的计算消耗。
    """
    data = get_settings(model)
    if len(data) == 0:
        return

    if time is None:
        time = get_time(model)

    assert isinstance(data, list)
    for item in data:
        try:
            assert isinstance(item, dict)
            index = item.get('index')
            if index < model.cell_number:
                t = item.get('time')
                p = item.get('pressure')
                target_fp = interp1(x=t, y=p, xq=time)  # 获取此刻的目标压力
                if target_fp > 0:  # 压力必须大于0
                    _modify_pore(cell=model.get_cell(index), target_fp=target_fp)
        except Exception as err:  # 打印错误，但是不中断执行.
            print(err)
