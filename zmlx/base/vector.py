from zmlx.exts.base import c_double, POINTER, np, Vector


def read_numpy(vec: Vector, data):
    """
    读取给定的numpy数组的数据
    """
    data = np.ascontiguousarray(data)  # 如果不是C连续的内存，必须强制转换
    vec.size = len(data)
    vec.read_memory(data.ctypes.data_as(POINTER(c_double)))


def write_numpy(vec: Vector, data):
    """
    将数据写入到numpy数组，必须保证给定的numpy数组的长度和self一致
    """
    data = np.ascontiguousarray(data)  # 如果不是C连续的内存，必须强制转换
    vec.write_memory(data.ctypes.data_as(POINTER(c_double)))
    return data


def to_numpy(vec: Vector):
    """
    将这个Vector转化为一个numpy的数组
    """
    a = np.zeros(shape=vec.size, dtype=float)
    return write_numpy(vec, a)
