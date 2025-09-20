"""
根据step，按照给定的间隔来执行操作
"""

from zmlx.exts.base import Seepage
from zmlx.config.slots import get_slots

text_key = 'step_iteration'


def get_settings(model: Seepage):
    """
    读取设置
    """
    text = model.get_text(text_key)
    if len(text) > 2:
        data = eval(text)
        assert isinstance(data, list)
        return data
    else:
        return []


def add_setting(model: Seepage, start=0, step=1, stop=999999999, name=None,
                args=None, kwds=None):
    """
    添加设置
    """
    if name is None or start >= stop or step <= 0:
        return
    setting = get_settings(model)
    setting.append({'start': start,
                    'step': step,
                    'stop': stop,
                    'name': name,
                    'args': args,
                    'kwds': kwds,
                    })
    model.set_text(text_key, setting)


def iterate(model: Seepage, current_step, slots):
    slots = get_slots(slots)

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

        start = setting.get('start')
        step = setting.get('step')
        stop = setting.get('stop')

        if start <= current_step < stop:
            if (current_step - start) % step == 0:
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
                    args = [model if equal(item, '@model') else item for item in
                            args]
                    kwds = {key: model if equal(value, '@model') else value for
                            key, value in kwds.items()}
                    # 替换@step
                    args = [current_step if equal(item, '@step') else item for
                            item in args]
                    kwds = {
                        key: current_step if equal(value, '@step') else value
                        for key, value in kwds.items()}
                    func(*args, **kwds)
