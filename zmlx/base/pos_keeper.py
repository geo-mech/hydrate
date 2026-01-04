import os
from ctypes import c_void_p, c_size_t

from zml import load_cdll, in_windows, dll as zml_dll, f64_ptr, const_f64_ptr, get_func

try:
    import numpy as np
except ImportError:
    np = None

# 导入dll
dll = load_cdll(
    'pos_keeper.dll' if in_windows() else 'pos_keeper_impl.so',
    first=os.path.dirname(os.path.realpath(__file__))
)


def get_pointers(cells):
    """
    返回cell的指针数组. 这是后续进行向量化计算的前提。
    """
    # 检查所有handle是否重复
    all_handles = []

    # 收集所有source handle
    for cell in cells:
        all_handles.append(cell.handle)

    # 检查是否有重复
    if len(set(all_handles)) != len(all_handles):
        # 找出重复的handle
        seen = set()
        duplicates = set()
        for handle in all_handles:
            if handle in seen:
                duplicates.add(handle)
            else:
                seen.add(handle)
        raise ValueError(f"发现重复的handle: {duplicates}")

    pointers = (c_void_p * len(cells))()

    for idx, cell in enumerate(cells):
        pointers[idx] = cell.handle

    return pointers


get_func(dll, None, 'write_cell_pos', c_void_p, c_size_t, c_void_p, c_void_p, c_void_p, c_void_p)


def write_cell_pos(pointers, count):
    """
    对于给定的cell，备份并返回当前的位置
    """
    # 为x, y, z准备缓冲区
    x = np.zeros(shape=count, dtype=np.float64)
    y = np.zeros(shape=count, dtype=np.float64)
    z = np.zeros(shape=count, dtype=np.float64)

    # 写入坐标
    dll.write_cell_pos(pointers, count, f64_ptr(x), f64_ptr(y), f64_ptr(z), zml_dll.seepage_cell_get_pos)

    # 返回备份的坐标
    return x, y, z


get_func(dll, None, 'read_cell_pos', c_void_p, c_size_t, c_void_p, c_void_p, c_void_p, c_void_p)


def read_cell_pos(pointers, count, *, x, y, z):
    """
    恢复cell的位置
    """
    dll.read_cell_pos(
        pointers, count, const_f64_ptr(x), const_f64_ptr(y), const_f64_ptr(z), zml_dll.seepage_cell_set_pos)


class CellPosKeeper:
    def __init__(self, cells):
        if cells is not None and len(cells) > 0:
            self.pointers = get_pointers(cells)
            self.count = len(cells)
        else:
            self.pointers = None
            self.count = 0

        if self.pointers is not None:
            self.x, self.y, self.z = write_cell_pos(self.pointers, self.count)

    def restore(self):
        if self.pointers is not None:
            read_cell_pos(self.pointers, self.count, x=self.x, y=self.y, z=self.z)


def test():
    from zml import Seepage

    model = Seepage()
    c = model.add_cell()
    c.x = 0
    c = model.add_cell()
    c.x = 1
    c = model.add_cell()
    c.x = 2

    keep = CellPosKeeper([c for c in model.cells])
    model.get_cell(0).x = 100
    model.get_cell(1).x = 45

    keep.restore()
    for c in model.cells:
        print(c.pos)


if __name__ == "__main__":
    test()
