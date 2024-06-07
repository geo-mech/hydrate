import numpy as np
from ctypes import c_double, POINTER


def ip_nodes_write(ip_model, index, pointer=None, buf=None):
    """
    导出属性:
        index=-1, x坐标
        index=-2, y坐标
        index=-3, z坐标
        index=-4, phase
    """
    if pointer is None:
        if buf is None:
            buf = np.zeros(shape=ip_model.node_n, dtype=float)
        else:
            assert len(buf) == ip_model.node_n
        if not buf.flags['C_CONTIGUOUS']:
            buf = np.ascontiguous(buf, dtype=buf.dtype)
        pointer = buf.ctypes.data_as(POINTER(c_double))

    if index == -1 or index == -2 or index == -3:
        ip_model.write_pos(-index - 1, pointer)
        return buf

    if index == -4:
        ip_model.write_phase(pointer)
        return buf
