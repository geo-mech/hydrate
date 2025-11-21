"""
在计算流动的时候，"临时"修改流体的粘性系数，从而去调整流动的阻力。这里，所谓的“临时”修改，是提供了两个函数，第一是进行调整和备份，第二是恢复备份。
在此模块执行的时候，会读取cell的一个属性，并以此属性为倍率，来调整给定流体的粘性系数。
"""

from zmlx.base.seepage import as_numpy
from zmlx.exts.base import Seepage

text_key = 'adjust_vis'


def get_settings(model: Seepage):
    """
    读取设置

    参数:
    - model: Seepage 对象

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


def add_setting(model: Seepage, name: str | None = None, key: str | None = None):
    """
    添加设置. 其中name为流体的名字，key为cell的属性.

    参数:
    - model: Seepage 对象
    - name: 流体的名字
    - key: cell的属性

    返回值:
    - 无

    如果name和key都是字符串，则将它们添加到模型的设置中
    """
    if isinstance(name, str) and isinstance(key, str):
        settings = get_settings(model)
        settings.append(dict(name=name, key=key))
        model.set_text(text_key, text=f'{settings}')


def adjust(model: Seepage):
    """
    1. 备份流体的粘性系数，然后 2. 调整流体的粘性系数

    参数:
    - model: Seepage 对象

    返回值:
    - None

    该函数会备份模型中所有设置的流体的粘性系数，并根据每个设置中的属性值（key）调整相应流体的粘性系数
    """
    for setting in get_settings(model):
        assert isinstance(setting, dict)

        # 流体的名字， 以及 cell 的属性（倍率）
        name, key = setting.get('name'), setting.get('key')

        # 检查，之前是否已经备份过(如果已经备份过，则跳过)
        key_backup = f'viscosity_backup_of_{name}'
        if getattr(model, key_backup, None) is not None:
            print(f'流体{name}的粘性已经备份过. 请先恢复备份，然后才能调整粘性系数')
            continue

        # 检查属性是否注册
        ca = model.get_cell_key(key=key)
        if ca is None:
            print(f'Cell属性{key}未注册. 必须先注册该属性并设置各个Cell的属性值，然后才能调整粘性系数')
            continue

        # 粘性放大的倍率（允许的值在 1.0e-10 到 1.0e+10 之间）
        ratio = as_numpy(model).cells.get(index=ca)
        ratio[ratio < 1.0e-10] = 1
        ratio[ratio > 1.0e+10] = 1

        # 流体的numpy代理
        fid = model.find_fludef(name=name)
        assert fid is not None, f'未找到流体{name}'
        flu = as_numpy(model).fluids(*fid)

        # 所有流体的粘性系数
        vis = flu.vis
        setattr(model, key_backup, vis)  # 临时用属性来备份
        flu.vis = vis * ratio  # 修改粘性系数


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
    for setting in settings:
        name = setting.get('name')
        key_backup = f'viscosity_backup_of_{name}'
        vis = getattr(model, key_backup, None)
        if vis is None:
            print(f'流体{name}的粘性系数未备份. 请先备份粘性系数，然后才能恢复粘性系数')
            continue
        fid = model.find_fludef(name=name)
        flu = as_numpy(model).fluids(*fid)
        flu.vis = vis
        setattr(model, key_backup, None)  # 在恢复了之后，则删除之前的备份，使得这种备份/恢复只能执行一次
