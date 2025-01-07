from zml import *

core = DllCore(dll=load_cdll(name='beta.dll',
                             first=os.path.dirname(__file__)))

core.use(None, 'seepage_update_sand', c_void_p,
         c_size_t, c_size_t,
         c_size_t, c_size_t, c_size_t,
         c_size_t, c_size_t, c_size_t, c_void_p, c_void_p)


def update_sand(model: Seepage, *, sol_sand, flu_sand, ca_i0, ca_i1,
                force, ratio=None):
    """
    更新流动的砂和沉降的砂之间的体积. 其中:
        sol_sand, flu_sand: 表示流动的砂和沉降的砂的Index.
        force: 一个指针，给定各个cell位置的单位面积孔隙表面的剪切力;
        ratio: 一个指针，定义各个Cell位置砂子趋向于目标浓度的达成比率(默认为1).
        ca_i0, ca_i1: Cell的属性ID，定义的是存储的曲线的ID。曲线的横坐标是剪切力，纵轴为流动砂的浓度.
    """
    if isinstance(sol_sand, str):
        sol_sand = model.find_fludef(name=sol_sand)
        assert sol_sand is not None

    if isinstance(flu_sand, str):
        flu_sand = model.find_fludef(name=flu_sand)
        assert flu_sand is not None

    if isinstance(ca_i0, str):
        ca_i0 = model.get_cell_key(ca_i0)
        assert ca_i0 is not None

    if isinstance(ca_i1, str):
        ca_i1 = model.get_cell_key(ca_i1)
        assert ca_i1 is not None

    core.seepage_update_sand(model.handle, ca_i0, ca_i1,
                             *parse_fid3(sol_sand),
                             *parse_fid3(flu_sand),
                             ctypes.cast(force, c_void_p), ctypes.cast(ratio, c_void_p))


if __name__ == '__main__':
    print(core.time_compile)
