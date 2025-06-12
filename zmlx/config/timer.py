"""
定义，在模型执行到某一个时刻的时候来执行的操作
"""

from zml import Seepage
from zmlx.config.slots import get_slot

text_key = 'timers'


def get_settings(model: Seepage):
    """
    读取设置
    """
    text = model.get_text(text_key)
    if len(text) > 2:
        data = eval(text)
        assert isinstance(data, list), 'timers must be a list'
        return data
    else:
        return []


def add_setting(model: Seepage, time, name, args=None, kwds=None):
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
    value = x.get(key, default)
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


def iterate(model: Seepage, t0, t1, slots):
    if t0 >= t1:
        return

    settings = get_settings(model)
    if len(settings) == 0:
        return

    def equal(a, b):
        if isinstance(a, str) and isinstance(b, str):
            return a == b
        else:
            return False

    for setting in settings:
        assert isinstance(setting, dict)
        time = setting.get('time')
        if t0 <= time < t1:
            table = {'@time': time, '@model': model}  # 需要替换的数据表格
            func = get_slot(setting.get('name'), slots)
            if func is not None:
                args = get(setting, 'args', [])
                kwds = get(setting, 'kwds', {})
                args = replace(args, table)
                kwds = replace(kwds, table)
                func(*args, **kwds)


def test_1():
    table = {'xx': 1, 'yy': 2, 'zz': 3}
    print(replace(['yy', 'zz', 4, 5, 'xx'], table))
    print(replace({'xx': 1, 'name': 'yy', 'age': 'xx'}, table))


if __name__ == '__main__':
    test_1()
