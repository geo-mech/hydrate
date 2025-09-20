"""
一些尚未分类的、比较小的工具函数
"""
import math
from random import uniform

from zmlx.exts.base import read_text, Vector, is_array, np


def year_to_seconds(year):
    """
    将年转化为秒.
    Args:
        year: 年
    Returns:
        秒
    """
    return 365.0 * 24.0 * 3600.0 * year


def rand_dir3(norm=1.0, max_try=200, default=None):
    """
    返回一个三维空间的随机的方向 <返回三维向量的长度等于1>
    Args:
        norm: 向量的长度
        max_try: 最大尝试次数
        default: 默认值
    Returns:
        三维向量
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
    """
    将给定的索引转换为元组/list形式
    """
    if is_array(index):
        return index
    else:
        return index,


def clamp(value, left=None, right=None):
    """
    对于给定值，将它限定在给定的范围内
    Args:
        value: 给定的值
        left: 左边界
        right: 右边界
    Returns:
        限定后的值
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
    Args:
        start: The starting value of the sequence.
        stop: The end value of the sequence, not included in the result.
        num: Number of samples to generate. Default is 50.
    Returns:
        list: An array of evenly spaced values.
    """
    dv = (stop - start) / max(num - 1, 1)
    return [start + dv * i for i in range(num)]


def mean(*args):
    """
    计算给定的各个参数的平均值
    Args:
        *args: 给定的参数
    Returns:
        平均值
    """
    n = len(args)
    if n > 0:
        return sum(args) / n
    else:
        return None


def code_config(path=None, encoding=None, text=None):
    """
    获取脚本中的配置信息.
    脚本中的配置信息以 # ** 开头，后面的内容为python代码.
    Args:
        path: 脚本路径
        encoding: 脚本编码
        text: 脚本内容
    Returns:
        配置信息
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
    """
    将一个列表分成n个部分
    Args:
        lst: 列表
        n: 部分的数量

    Returns:
        list: 包含n个部分的列表
    """
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

    Args:
        x: 要比较的第一个数。
        y: 要比较的第二个数。

    Returns:
        bool: 如果 x 小于 y，则返回 True，否则返回 False。
    """
    return x < y


def is_sorted(vx, compare=None):
    """
    检查列表是否已排序

    Args:
        vx (list): 要检查的列表。
        compare (function, 可选): 用于比较列表元素的函数。如果未提供，则使用默认的小于比较。

    Returns:
        bool: 如果列表已排序则返回 True，否则返回 False。

    Raises:
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
    Args:
        *args: 要合并的vector或其他可转换为vector的对象
    Returns:
        np.ndarray: 合并后的矩阵
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

    Args:
        *args: 一个或多个NumPy矩阵。

    Returns:
        堆叠后的矩阵。
    """
    assert np is not None, 'numpy is not installed'
    return np.vstack(args)


def mass2str(kg):
    """将千克为单位的质量转换为带合适单位的字符串表示。

    根据质量大小自动选择合适的计量单位，转换优先级为：微克(ug) < 毫克(mg) < 克(g) < 千克(kg) < 吨(t)
    转换阈值为2000（当数值绝对值超过2000时使用更大单位）

    Args:
        kg (float): 以千克为单位的质量值，支持正负值

    Returns:
        str: 格式化的带单位字符串，保留两位小数。单位符号直接附加在数值后，吨(t)除外：
            - 数值范围在±2000ug内时返回ug单位
            - 数值范围在±2000mg内时返回mg单位
            - 数值范围在±2000g内时返回g单位
            - 数值范围在±2000kg内时返回kg单位
            - 超过±2000kg时返回吨(t)单位
    """
    ug = kg * 1.0e9
    if abs(ug) < 2000:
        return '%.2fug' % ug
    mg = ug / 1000
    if abs(mg) < 2000:
        return '%.2fmg' % mg
    g = mg / 1000
    if abs(g) < 2000:
        return '%.2fg' % g
    kg = g / 1000
    if abs(kg) < 2000:
        return '%.2fkg' % kg
    t = kg / 1000
    return '%.2ft' % t


def time2str(s):
    """将时间从秒转换为字符串表示，使用纳秒（ns）、微秒（us）、毫秒（ms）、秒（s）、
    分钟（m）、小时（h）、天（d）和年（y）作为单位。

    Args:
        s (float): 要转换的时间，单位为秒。

    Returns:
        str: 时间的字符串表示，格式为 'x.xxns', 'x.xxus', 'x.xxms', 'x.xxs',
        'x.xxm', 'x.xxh', 'x.xxd' 或 'x.xxy'。
    """
    if abs(s) < 200:
        if s > 2.0:
            return '%.2fs' % s
        s *= 1000
        if s > 2.0:
            return '%.2fms' % s
        s *= 1000
        if s > 2.0:
            return '%.2fus' % s
        s *= 1000
        return '%.2fns' % s
    m = s / 60
    if abs(m) < 200:
        return '%.2fm' % m
    h = m / 60
    if abs(h) < 60:
        return '%.2fh' % h
    d = h / 24
    if abs(d) < 800:
        return '%.2fd' % d
    y = d / 365
    return '%.2fy' % y


def fsize2str(size):
    """
    将文件大小从字节转换为字符串表示，使用KB、MB、GB和TB作为单位。
    Args:
        size: 文件大小，单位为字节

    Returns:
        str: 文件大小的字符串表示，格式为 'x.xxkb', 'x.xxMb', 'x.xxGb' 或 'x.xxTb'。
    """
    size /= 1024
    if size < 2000:
        return '%0.2f kb' % size

    size /= 1024
    if size < 2000:
        return '%0.2f Mb' % size

    size /= 1024
    if size < 2000:
        return '%0.2f Gb' % size
    else:
        size /= 1024
        return '%0.2f Tb' % size
