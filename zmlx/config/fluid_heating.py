from zmlx.base.seepage import get_dt, as_numpy
from zmlx.base.vector import to_numpy
from zmlx.base.zml import Seepage, np
from zmlx.config.alg import settings as _settings

text_key = 'fluid_heating'


def get_settings(model: Seepage):
    """
    读取设置
    """
    return _settings.get(model, text_key=text_key)


def add_setting(
        model: Seepage, fluid=None, power=None,
        temp_max=None):
    """
    添加设置.
    Args:
        model (Seepage): 需要添加设置的模型
        fluid: 即将被加热的流体的名称（或者ID）
        power: 加热的功率（可以是一个数组，也可以是一个缓冲区的名称）
        temp_max: 流体的最大温度（可以是一个数组，也可以是一个缓冲区的名称）

    Returns:
        None
    """
    if fluid is not None:
        _settings.add(
            model, text_key=text_key, fluid=fluid,
            power=power, temp_max=temp_max)


def iterate(model: Seepage, dt=None):
    """
    迭代更新流体的温度。
    Args:
        model (Seepage): 需要迭代更新的模型
        dt: 时间步长（如果为None，则使用模型默认的时间步长）

    Returns:
        None
    """
    if dt is None:
        dt = get_dt(model)

    the_settings = get_settings(model)
    if len(the_settings) == 0 or dt <= 0:
        return

    for setting in the_settings:
        assert isinstance(setting, dict)

        # 确定流体
        fluid = setting.get('fluid')
        if not isinstance(fluid, list):
            assert isinstance(fluid, str)
            fluid = model.find_fludef(name=fluid)
            assert isinstance(fluid, list)

        # 确定功率
        power = setting.get('power')

        # 这里，从缓冲区中读取功率的数据
        if isinstance(power, str):
            power = to_numpy(model.get_buffer(key=power))
        else:
            power = np.array(power)

        # 加热
        if len(power) == model.cell_number:  # 长度必须和cell的数量一致
            m = as_numpy(model).fluids(*fluid).mass
            c = as_numpy(model).fluids(*fluid).get(
                model.get_flu_key('specific_heat'))
            d_temp = (power * dt) / (m * c)
            d_temp[d_temp < 0] = 0  # 温度不能降低
            t0 = as_numpy(model).fluids(*fluid).get(
                model.get_flu_key('temperature'))
            t1 = t0 + d_temp  # 加温之后的温度

            temp_max = setting.get('temp_max')
            if temp_max is not None:
                if isinstance(temp_max, str):
                    temp_max = to_numpy(model.get_buffer(key=temp_max))
                else:
                    temp_max = np.array(temp_max)
                if len(temp_max) == model.cell_number:
                    mask = t1 > temp_max
                    t1[mask] = temp_max[mask]

            as_numpy(model).fluids(*fluid).set(
                model.get_flu_key('temperature'), t1)
