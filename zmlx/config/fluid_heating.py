import numpy as np

from zml import Seepage
from zmlx.alg.Vector import to_numpy
from zmlx.config.seepage_base import get_dt
from zmlx.utility.SeepageNumpy import as_numpy

text_key = 'fluid_heating'


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


def add_setting(model: Seepage, fluid=None, power=None, temp_max=None):
    """
    添加设置
    """
    if fluid is None:
        return
    setting = get_settings(model)
    setting.append({'fluid': fluid,
                    'power': power,
                    'temp_max': temp_max})
    model.set_text(text_key, setting)


def iterate(model: Seepage, dt=None):
    """
    更新pore
    """
    if dt is None:
        dt = get_dt(model)

    setting = get_settings(model)
    if len(setting) == 0 or dt <= 0:
        return

    for item in setting:
        assert isinstance(item, dict)

        # 确定流体
        fluid = item.get('fluid')
        if not isinstance(fluid, list):
            fluid = model.find_fludef(name=fluid)
            assert isinstance(fluid, list)

        # 确定功率
        power = item.get('power')

        if isinstance(power, str):
            power = to_numpy(model.get_buffer(key=power))
        else:
            power = np.array(power)

        # 加热
        if len(power) == model.cell_number:  # 长度必须和cell的数量一致

            m = as_numpy(model).fluids(*fluid).mass
            c = as_numpy(model).fluids(*fluid).get(model.reg_flu_key('specific_heat'))
            d_temp = (power * dt) / (m * c)
            d_temp[d_temp < 0] = 0  # 温度不能降低
            t0 = as_numpy(model).fluids(*fluid).get(model.reg_flu_key('temperature'))
            t1 = t0 + d_temp  # 加温之后的温度

            temp_max = item.get('temp_max')
            if temp_max is not None:
                if isinstance(temp_max, str):
                    temp_max = to_numpy(model.get_buffer(key=temp_max))
                else:
                    temp_max = np.array(temp_max)
                if len(temp_max) == model.cell_number:
                    mask = t1 > temp_max
                    t1[mask] = temp_max[mask]

            as_numpy(model).fluids(*fluid).set(model.reg_flu_key('temperature'), t1)
