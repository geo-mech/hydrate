"""
用于模拟砂的沉降及脱离
"""
import numpy as np

from zml import Seepage, get_pointer64
from zmlx.config.alg import settings
from zmlx.config.alg.pressure_gradient import get_face_pressure_gradient

# 存储的text
text_key = 'sand_settings'


def get_settings(model: Seepage):
    """
    读取设置
    """
    return settings.get(model, text_key=text_key)


def set_settings(model: Seepage, data):
    """
    写入设置
    """
    return settings.put(model, data=data, text_key=text_key)


def add_setting(model: Seepage, *, sol_sand, flu_sand, ca_i0, ca_i1, use_average=False):
    """
    添加设置
    """
    return settings.add(model, text_key=text_key,
                        sol_sand=sol_sand,
                        flu_sand=flu_sand,
                        ca_i0=ca_i0, ca_i1=ca_i1, use_average=use_average)

def get_gradient(model: Seepage, fluid=None, use_average=False):
    """
    计算Face位置的剪切应力
    """
    face_f = get_face_pressure_gradient(model=model, fluid=fluid)
    face_f = np.abs(face_f)
    if use_average:
        cell_f = model.get_cell_average(fa=get_pointer64(face_f))
    else:
        cell_f = model.get_cell_max(fa=get_pointer64(face_f))
    return cell_f


def iterate(model: Seepage):
    """
    更新砂
    """
    for item in get_settings(model):
        assert isinstance(item, dict)

        sol_sand = item.get('sol_sand')
        flu_sand = item.get('flu_sand')
        ca_i0 = item.get('ca_i0')
        ca_i1 = item.get('ca_i1')
        use_average = item.get('use_average')

        if isinstance(sol_sand, str):
            sol_sand = model.find_fludef(name=sol_sand)

        if isinstance(flu_sand, str):
            flu_sand = model.find_fludef(name=flu_sand)

        assert len(flu_sand) >= 2
        grad = get_gradient(model, fluid=[flu_sand[0]], use_average=use_average)

        # 更新砂的体积
        model.update_sand(sol_sand=sol_sand, flu_sand=flu_sand,
                          ca_i0=ca_i0, ca_i1=ca_i1, force=get_pointer64(grad))
