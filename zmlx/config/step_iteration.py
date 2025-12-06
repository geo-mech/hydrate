"""
根据step，按照给定的间隔来执行操作
"""

from zmlx.base.seepage import get_step
from zmlx.base.zml import Seepage, clock
from zmlx.config.alg import settings as alg_settings
from zmlx.config.slots import get_slots

text_key = 'step_iteration'


def get_settings(model: Seepage):
    """
    读取设置
    """
    return alg_settings.get(model, text_key=text_key)


def add_setting(
        model: Seepage, start=0, step=1, stop=999999999, name=None,
        args=None, kwds=None):
    """
    添加设置
    """
    if name is None or start >= stop or step <= 0:
        return
    alg_settings.add(
        model, text_key=text_key,
        start=start, step=step, stop=stop,
        name=name, args=args, kwds=kwds
    )


@clock
def iterate(*models):
    """
    model: Seepage, current_step, slots
    Returns:
    """

    def equal(a, b):
        if isinstance(a, str) and isinstance(b, str):
            return a == b
        else:
            return False

    for model in models:
        assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'
        slots = get_slots(model.temps.get('slots'))

        settings = get_settings(model)
        if len(settings) == 0:
            continue

        current_step = get_step(model)

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
