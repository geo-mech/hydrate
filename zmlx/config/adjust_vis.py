"""
在计算流动的时候，"临时"修改流体的粘性系数，从而去调整流动的阻力。
这里，所谓的“临时”修改，是提供了两个函数，第一是进行调整和备份，第二是恢复备份。
在此模块执行的时候，会读取cell的一个属性，并以此属性为倍率，来调整给定流体的粘性系数。

最后修改：2025-11-25
"""

from zmlx.base.seepage import as_numpy
from zmlx.base.zml import Seepage
from zmlx.config.alg import settings

text_key = 'adjust_vis'


def get_settings(model: Seepage):
    """
    读取设置

    Args:
        model: Seepage 对象

    Returns:
        list[dict]: 一个列表，包含从模型中读取的设置.
        每个dict都包含'name'和'key'两个键值对.
        'name'是流体的名字 (或者流体的ID),
        'key'是cell的属性 (一个字符串，用来存储调整粘性系数的倍率).
    """
    return settings.get(model, text_key=text_key)


def add_setting(
        model: Seepage,
        name: str | None = None,
        key: str | None = None):
    """
    添加设置. 其中name为流体的名字，key为cell的属性.

    Args:
        model: Seepage 对象
        name: 流体的名字 (或者流体的ID)
        key: cell的属性 (一个字符串，用来存储调整粘性系数的倍率)

    Returns:
        None
    """
    assert isinstance(name, str) and isinstance(key, str)
    settings.add(model, text_key=text_key,
                 name=name, key=key)


def adjust(model: Seepage):
    """
    1. 备份流体的粘性系数，然后 2. 调整流体的粘性系数

    Args:
        model: Seepage 对象

    Returns:
        None
    """
    if model.temps.get('vis_backups') is not None:
        print('已经备份过流体的粘性系数. 请先恢复备份，然后才能调整粘性系数')
        return

    vis_backups = []
    for setting in get_settings(model):
        assert isinstance(setting, dict)

        # 获得粘性放大的倍率（允许的值在 1.0e-10 到 1.0e+10 之间）
        ca = setting.get('key')
        if not isinstance(ca, int):
            ca = model.get_cell_key(key=ca)
        if not isinstance(ca, int):
            print(f'Cell属性{ca}未注册. 必须先注册该属性并设置各个Cell的属性值，'
                  f'然后才能调整粘性系数')
            vis_backups.append(None)
            continue
        times = as_numpy(model).cells.get(index=ca)
        times[times < 1.0e-10] = 1
        times[times > 1.0e+10] = 1

        # 流体的名字， 以及 cell 的属性（倍率）
        flu = setting.get('name')
        if isinstance(flu, str):
            flu = model.find_fludef(name=flu)
        if isinstance(flu, int):
            flu = [flu]
        if not isinstance(flu, list | tuple):
            print(f'未识别的流体{flu}. 必须是流体的名字或ID')
            vis_backups.append(None)
            continue

        # 调整粘性系数，并且备份
        vis = as_numpy(model).fluids(*flu).vis
        vis_backups.append(vis)
        as_numpy(model).fluids(*flu).vis = vis * times  # 修改粘性系数


def restore(model: Seepage):
    """
    恢复之前备份的流体的粘性

    Args:
        model: Seepage 模型对象

    Returns:
        None
    """
    vis_backups = model.temps.get('vis_backups')
    if vis_backups is None:
        print('未备份过流体的粘性系数. 请先备份粘性系数，然后才能恢复粘性系数')
        return

    index = 0
    for setting in get_settings(model):
        assert isinstance(setting, dict)

        assert index < len(vis_backups)
        vis = vis_backups[index]
        index += 1

        if vis is None:
            continue

        flu = setting.get('name')
        if isinstance(flu, str):
            flu = model.find_fludef(name=flu)
        if isinstance(flu, int):
            flu = [flu]

        as_numpy(model).fluids(*flu).vis = vis

    del model.temps['vis_backups']
