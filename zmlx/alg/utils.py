import math
from random import uniform

try:
    import numpy as np
except Exception as e:
    print(e)
    np = None

from zml import read_text, Vector, is_array


def year_to_seconds(year):
    """
    将年转化为秒
    """
    return 365.0 * 24.0 * 3600.0 * year


def rand_dir3(norm=1.0, max_try=200, default=None):
    """
    返回一个三维空间的随机的方向 <返回三维向量的长度等于1>
    """
    for times in range(max_try):
        x = uniform(-1, 1)
        y = uniform(-1, 1)
        z = uniform(-1, 1)
        r = math.sqrt(x * x + y * y + z * z)
        if 0.001 < r < 1:
            r /= norm
            return [x / r, y / r, z / r]
    if default is None:
        return [norm, 0, 0]
    else:
        return default


def make_index(index):
    if is_array(index):
        return index
    else:
        return index,


def clamp(value, left=None, right=None):
    """
    对于给定值，将它限定在给定的范围内
    """
    if left is None and right is None:
        return value
    if left is None:
        return min(value, right)
    if right is None:
        return max(value, left)
    if left < right:
        return max(left, min(right, value))
    else:
        return max(right, min(left, value))


def linspace(start, stop, num=50):
    """
    Return evenly spaced numbers over a specified interval.
    """
    dv = (stop - start) / max(num - 1, 1)
    return [start + dv * i for i in range(num)]


def mean(*args):
    """
    计算给定的各个参数的平均值
    """
    n = len(args)
    if n > 0:
        return sum(args) / n
    else:
        return None


def code_config(path=None, encoding=None, text=None):
    """
    获取脚本中的配置信息.
    """
    try:
        if text is None:
            text = read_text(path=path,
                             encoding='utf-8' if encoding is None else encoding,
                             default=None)
        config = {}
        if text is not None:
            code = ""
            for line in text.splitlines():
                line = line.strip()
                if len(line) >= 4:
                    if line[0: 4] == '# **':
                        code += line[4:].strip() + '\n'
            if len(code) > 0:
                try:
                    exec(code, None, config)
                except Exception as e:
                    print(e)
        return config
    except Exception as e2:
        print(e2)
        return {}


def divide_list(lst, n):
    # 计算列表长度
    total_elements = len(lst)
    # 使用整除得到每个子列表的基本元素数量
    base_size = total_elements // n
    # 使用取余得到剩余的元素数量
    remainder = total_elements % n

    # 初始化结果列表
    result = []
    # 初始化当前索引
    start_index = 0

    # 循环创建子列表
    for i in range(n):
        # 确定当前子列表的大小，前remainder个子列表会多一个元素
        if i < remainder:
            end_index = start_index + base_size + 1
        else:
            end_index = start_index + base_size
            # 切片操作获取子列表
        sub_list = lst[start_index:end_index]
        # 将子列表添加到结果列表中
        result.append(sub_list)
        # 更新下一个子列表的起始索引
        start_index = end_index

    return result


def less(x, y):
    """
    比较两个数的大小

    参数:
    x: 要比较的第一个数。
    y: 要比较的第二个数。

    返回:
    bool: 如果 x 小于 y，则返回 True，否则返回 False。
    """
    return x < y


def is_sorted(vx, compare=None):
    """
    检查列表是否已排序

    参数:
    vx (list): 要检查的列表。
    compare (function, 可选): 用于比较列表元素的函数。如果未提供，则使用默认的小于比较。

    返回:
    bool: 如果列表已排序则返回 True，否则返回 False。

    异常:
    ValueError: 如果 compare 参数不是一个函数。
    """
    if compare is not None and not callable(compare):
        raise ValueError("compare should be a function")
    if compare is None:
        compare = less
    for i in range(len(vx) - 1):
        if not compare(vx[i], vx[i + 1]):
            return False
    return True


def join_cols(*args):
    """
    将给定的多个vector作为列来合并成为一个np的矩阵
    """
    assert np is not None, 'numpy is not installed'
    cols = []
    for v in args:
        if isinstance(v, Vector):
            a = np.zeros(shape=(v.size, 1), dtype=float)
            v.write_numpy(a)
            cols.append(a)
        else:
            v = np.reshape(np.asarray(v), (-1, 1))
            cols.append(v)
    return np.hstack(cols)


def join_rows(*args):
    """
    堆叠具有相同列数但行数可能不同的矩阵。

    参数:
        matrices: 一个或多个NumPy矩阵。

    返回:
        堆叠后的矩阵。
    """
    assert np is not None, 'numpy is not installed'
    return np.vstack(args)
