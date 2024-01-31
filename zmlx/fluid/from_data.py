from zml import Interp2, Seepage
from zmlx.utility.Interp2 import Interp2 as Interpolator


def get_max(data, get, max_):
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


def get_itp(data, get_x, get_y, get_v, dx=None, dy=None, x_min=None, x_max=None, y_min=None, y_max=None):
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

    for item in data:
        x = get_x(item)
        y = get_y(item)
        v = get_v(item)
        if x is not None and y is not None and v is not None:
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
              t_min=None, t_max=None, p_min=None, p_max=None, name=None, specific_heat=None):
    """
    创建液态co2的定义.
    """
    den = get_itp(data, get_x=get_p, get_y=get_t, get_v=get_den,
                  dx=1e6, dy=1, x_min=p_min, x_max=p_max, y_min=t_min, y_max=t_max)

    vis = get_itp(data, get_x=get_p, get_y=get_t, get_v=get_vis,
                  dx=1e6, dy=1, x_min=p_min, x_max=p_max, y_min=t_min, y_max=t_max)

    if specific_heat is None:
        specific_heat = 2000.0

    return Seepage.FluDef(den=den, vis=vis, specific_heat=specific_heat, name=name)
