"""
在计算流动的时候，临时修改流体的粘性系数，从而去调整流动的阻力。在此模块执行的时候，会读取cell的一个属性，并以此属性为
倍率，来调整给定流体的粘性系数。

注：
    此模块后续可能会被标记为弃用。
"""

from zml import Seepage
from zmlx.base.seepage import as_numpy

text_key = 'adjust_vis'


def get_settings(model: Seepage):
    """
    读取设置

    参数:
    - model: Seepage 模型对象

    返回值:
    - 一个列表，包含从模型中读取的设置

    如果模型中没有找到相应的设置，则返回一个空列表
    """
    text = model.get_text(text_key)
    if len(text) > 2:
        data = eval(text)
        assert isinstance(data, list)
        return data
    else:
        return []


def add_setting(model: Seepage, name=None, key=None):
    """
    添加设置. 其中name为流体的名字，key为cell的属性.

    参数:
    - model: Seepage 模型对象
    - name: 流体的名字
    - key: cell的属性

    返回值:
    - 无

    如果name和key都是字符串，则将它们添加到模型的设置中
    """
    if isinstance(name, str) and isinstance(key, str):
        settings = get_settings(model)
        settings.append({'name': name,
                         'key': key})
        model.set_text(text_key, text=f'{settings}')


data_backups_dict = {}


def adjust(model: Seepage):
    """
    备份流体的粘性系数，并且进行调整

    参数:
    - model: Seepage 模型对象

    返回值:
    - 无

    该函数会备份模型中所有设置的流体的粘性系数，并根据每个设置中的属性值（key）调整相应流体的粘性系数
    """
    data_backups = []
    for setting in get_settings(model):
        assert isinstance(setting, dict)
        name, key = setting.get('name'), setting.get('key')

        ratio = as_numpy(model).cells.get(index=model.reg_cell_key(key=key))
        ratio[ratio < 1.0e-10] = 1
        ratio[ratio > 1.0e+10] = 1

        fid = model.find_fludef(name=name)
        flu = as_numpy(model).fluids(*fid)
        vis = flu.vis
        data_backups.append(vis)
        flu.vis = vis * ratio  # 修改粘性系数
    data_backups_dict[model.handle] = data_backups


def restore(model: Seepage):
    """
    恢复之前备份的流体的粘性

    参数:
    - model: Seepage 模型对象

    返回值:
    - 无

    该函数会根据之前备份的流体粘性系数，恢复模型中相应流体的粘性系数
    """
    settings = get_settings(model)
    data_backups = data_backups_dict.pop(model.handle)
    assert len(data_backups) == len(settings)
    for idx in range(len(settings)):
        name = settings[idx].get('name')
        fid = model.find_fludef(name=name)
        flu = as_numpy(model).fluids(*fid)
        flu.vis = data_backups[idx]
