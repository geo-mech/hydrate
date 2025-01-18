import ctypes

from zml import *

core = DllCore(dll=load_cdll(name='beta.dll',
                             first=os.path.dirname(__file__)))

core.use(None, 'seepage_update_sand', c_void_p,
         c_size_t, c_size_t,
         c_size_t, c_size_t, c_size_t,
         c_size_t, c_size_t, c_size_t, c_void_p)


def update_sand(model: Seepage, *, sol_sand, flu_sand, ca_i0, ca_i1,
                stress):
    """
    更新流动的砂和沉降的砂之间的体积. 其中stress是一个指针，给定各个cell位置的孔隙表面的流体应力。
    """
    if isinstance(sol_sand, str):
        sol_sand = model.find_fludef(name=sol_sand)
        assert sol_sand is not None

    if isinstance(flu_sand, str):
        flu_sand = model.find_fludef(name=flu_sand)
        assert flu_sand is not None

    if isinstance(ca_i0, str):
        ca_i0 = model.reg_cell_key(ca_i0)

    if isinstance(ca_i1, str):
        ca_i1 = model.reg_cell_key(ca_i1)

    core.seepage_update_sand(model.handle, ca_i0, ca_i1,
                             *parse_fid3(sol_sand),
                             *parse_fid3(flu_sand),
                             ctypes.cast(stress, c_void_p))


if __name__ == '__main__':
    print(core.time_compile)
