"""
定义，在模型执行到某一个时刻的时候来执行的操作
"""

from zmlx.base.seepage import get_time, get_dt
from zmlx.base.zml import Seepage, clock
from zmlx.config.alg import settings as alg_settings
from zmlx.config.slots import get_slot, get_slots

text_key = 'timers'


def get_settings(model: Seepage):
    """
    读取设置
    """
    return alg_settings.get(model, text_key=text_key)


def add_setting(
        model: Seepage, *,
        time, name, args=None, kwds=None):
    """
    添加设置
    """
    setting = get_settings(model)
    x = dict(time=time, name=name)
    if args is not None:
        x['args'] = args
    if kwds is not None:
        x['kwds'] = kwds
    setting.append(x)
    setting = sorted(setting, key=lambda item: item['time'])
    model.set_text(text_key, setting)


def get(x: dict, key, default=None):
    """
    返回字典的值（忽略None）
    """
    value = x.get(key)
    if value is None:
        return default
    else:
        return value


def replace(data, table):
    """
    替换参数列表或者关键词列表的值
    """
    if isinstance(data, str):  # 此时，尝试替换字符串
        return table.get(data, data)
    elif isinstance(data, (list, tuple)):
        return [replace(item, table) for item in data]
    elif isinstance(data, dict):
        return {key: replace(value, table) for key, value in data.items()}
    else:
        return data


@clock
def iterate(*models):
    for model in models:
        assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'
        # 所有的回调函数
        slots = get_slots(model.temps.get('slots'))

        t0 = get_time(model)
        t1 = t0 + get_dt(model)

        if t0 >= t1:
            continue

        settings = get_settings(model)
        if len(settings) == 0:
            continue

        for setting in settings:
            assert isinstance(setting, dict)
            time = setting.get('time')
            if t0 <= time < t1:
                table = {'@time': time, '@model': model}  # 需要替换的数据表格
                func = get_slot(setting.get('name'), slots=slots)
                if func is not None:
                    args = get(setting, 'args', [])
                    kwds = get(setting, 'kwds', {})
                    args = replace(args, table)
                    kwds = replace(kwds, table)
                    func(*args, **kwds)
