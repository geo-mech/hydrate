from zml import Seepage


def get_density(pre, temp, flu_def: Seepage.FluDef):
    """
    返回给定压力和温度下的密度
    """
    data = flu_def.den

    if data is not None:
        return data(pre, temp)


def get_viscosity(pre, temp, flu_def: Seepage.FluDef):
    """
    返回给定压力和温度下的密度
    """
    data = flu_def.vis

    if data is not None:
        return data(pre, temp)
