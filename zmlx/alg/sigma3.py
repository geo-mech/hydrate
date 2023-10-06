from zml import *

dll = load_cdll(name='sigma3.dll', first=os.path.dirname(__file__))
core = DllCore(dll=dll)

core.use(None, 'sigma3_get1', c_void_p,
         c_double, c_double, c_double,
         c_double, c_double, c_double,
         c_double, c_double, c_double)

core.use(None, 'sigma3_get2', c_void_p,
         c_double, c_double, c_double,
         c_double, c_double, c_double,
         c_double, c_double, c_double,
         c_double, c_double, c_double,
         c_double, c_double, c_double,
         c_double, c_double)


def get_induced(pos, disp, G, mu, area=None, triangle=None, buffer=None):
    """
    返回诱导应力.
    """
    if not isinstance(buffer, Tensor3):
        buffer = Tensor3()
    if area is not None:
        core.sigma3_get1(buffer.handle, pos[0], pos[1], pos[2], disp[0], disp[1], disp[2], area, G, mu)
        return buffer
    else:
        assert triangle is not None
        p0, p1, p2 = triangle
        x0, y0, z0 = p0
        x1, y1, z1 = p1
        x2, y2, z2 = p2
        core.sigma3_get2(buffer.handle, pos[0], pos[1], pos[2],
                         x0, y0, z0,
                         x1, y1, z1,
                         x2, y2, z2,
                         disp[0], disp[1], disp[2],
                         G, mu)
        return buffer
