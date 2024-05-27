from zml import Interp2, Seepage
from zmlx.utility.Interp2 import Interp2 as Interpolator


def get_max(data, get, max_):
    """
    找到一列元素的最大值
    """
    if data is None:
        return

    result = None
    for item in data:
        value = get(item)
        if value is not None:
            if result is None:
                result = value
            else:
                result = max_(result, value)

    return result


def get_itp(data, get_x, get_y, get_v, dx=None, dy=None,
            x_min=None, x_max=None,
            y_min=None, y_max=None,
            v_min=None, v_max=None):
    """
    创建插值，用于创建流体. 其中v_min和v_max指定了数据的有效范围，超过这个范围的数据将会被忽略.
    """
    if data is None:
        return

    if len(data) == 0:
        return

    if x_min is None:
        x_min = get_max(data, get_x, min)
    if x_max is None:
        x_max = get_max(data, get_x, max)

    if x_min is None or x_max is None:
        return
    if x_min > x_max:
        return

    if y_min is None:
        y_min = get_max(data, get_y, min)
    if y_max is None:
        y_max = get_max(data, get_y, max)

    if y_min is None or y_max is None:
        return
    if y_min > y_max:
        return

    vx = []
    vy = []
    vv = []

    # 允许的数值的范围，在此范围之外的数据将会被忽略掉
    if v_min is None:
        v_min = -1.0e100

    if v_max is None:
        v_max = 1.0e100

    assert v_min <= v_max

    for item in data:
        x = get_x(item)
        y = get_y(item)
        v = get_v(item)
        if x is not None and y is not None and v is not None:
            if v_min <= v <= v_max:
                vx.append(x)
                vy.append(y)
                vv.append(v)

    if len(vx) == 0:
        return

    f = Interpolator(vx, vy, vv, rescale=True)

    def get(a, b):
        assert x_min <= a <= x_max
        assert y_min <= b <= y_max
        return f(a, b)

    if dx is None:
        dx = (x_max - x_min) / 20

    if dy is None:
        dy = (y_max - y_min) / 20

    itp = Interp2()
    itp.create(x_min, dx, x_max, y_min, dy, y_max, get)
    return itp


def from_data(data, get_t, get_p, get_den, get_vis,
              t_min=None, t_max=None, p_min=None, p_max=None,
              name=None, specific_heat=None):
    """
    创建流体的定义.
        注意，对于流体数据，小于1.0e-20的密度或者粘性系数，将会被忽略掉
    """
    den = get_itp(data, get_x=get_p, get_y=get_t, get_v=get_den,
                  dx=1e6, dy=1, x_min=p_min, x_max=p_max,
                  y_min=t_min, y_max=t_max,
                  v_min=1.0e-20, v_max=1.0e50)

    vis = get_itp(data, get_x=get_p, get_y=get_t, get_v=get_vis,
                  dx=1e6, dy=1, x_min=p_min, x_max=p_max,
                  y_min=t_min, y_max=t_max,
                  v_min=1.0e-20, v_max=1.0e50)

    if specific_heat is None:
        specific_heat = 2000.0

    return Seepage.FluDef(den=den, vis=vis, specific_heat=specific_heat,
                          name=name)
