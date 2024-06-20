"""
定义，在模型执行到某一个时刻的时候来执行的操作
"""

from zml import Seepage


def get_settings(model: Seepage):
    """
    读取设置
    """
    text = model.get_text('timers')
    if len(text) > 2:
        data = eval(text)
        assert isinstance(data, list)
        return data
    else:
        return []


def add_setting(model: Seepage, time, name, args=None, kwds=None):
    """
    添加设置
    """
    setting = get_settings(model)
    setting.append({'time': time,
                    'name': name,
                    'args': args,
                    'kwds': kwds,
                    })
    # 排序，确保顺序正确，从而，方便后续的执行
    setting = sorted(setting, key=lambda item: item['time'])
    model.set_text('timers', setting)


# 一些预定义函数
standard_slots = {'print': print}


def iterate(model: Seepage, t0, t1, slots):
    if t0 >= t1:
        return

    if slots is not None:
        temp = standard_slots.copy()
        temp.update(slots)
        slots = temp
    else:
        slots = standard_slots

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
            name = setting.get('name')
            func = slots.get(name)
            if func is not None:
                args = setting.get('args')
                if args is None:
                    args = []
                kwds = setting.get('kwds')
                if kwds is None:
                    kwds = {}
                # 替换@model
                args = [model if equal(item, '@model') else item for item in args]
                kwds = {key: model if equal(value, '@model') else value for key, value in kwds.items()}
                # 替换@time
                args = [time if equal(item, '@time') else item for item in args]
                kwds = {key: time if equal(value, '@time') else value for key, value in kwds.items()}
                func(*args, **kwds)

