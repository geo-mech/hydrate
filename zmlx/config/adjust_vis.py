"""
在计算流动的时候，临时修改流体的粘性系数.
"""

from zmlx.utility.SeepageNumpy import as_numpy
from zml import Seepage

text_key = 'adjust_vis'


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


def add_setting(model: Seepage, name=None, key=None):
    """
    添加设置. 其中name为流体的名字，key为cell的属性.
    """
    if isinstance(name, str) and isinstance(key, str):
        settings = get_settings(model)
        settings.append({'name': name,
                         'key': key})
        model.set_text(text_key, text=f'{settings}')


data_backups = []


def adjust(model: Seepage):
    """
    备份流体的粘性系数，并且进行调整
    """
    assert len(data_backups) == 0
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
        flu.vis = vis * ratio   # 修改粘性系数


def restore(model: Seepage):
    """
    恢复之前备份的流体的粘性
    """
    settings = get_settings(model)
    assert len(data_backups) == len(settings)
    for idx in range(len(settings)):
        name = settings[idx].get('name')
        fid = model.find_fludef(name=name)
        flu = as_numpy(model).fluids(*fid)
        flu.vis = data_backups[idx]
    data_backups.clear()  # 清空数据


