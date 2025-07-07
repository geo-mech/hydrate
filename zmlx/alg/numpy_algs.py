from io import StringIO

import numpy as np


def text_to_numpy(text, delimiter=' '):
    """
    将文本字符串转换为NumPy数组

    参数:
    text : str
        包含数组数据的文本字符串
    delimiter : str, 可选
        列分隔符（默认：空格）

    返回:
    numpy.ndarray : 从文本重建的NumPy数组
    """
    # 将字符串转换为类似文件对象
    buffer = StringIO(text)

    # 使用np.loadtxt加载数据
    arr = np.loadtxt(
        buffer,
        delimiter=delimiter,
        dtype=None  # 自动识别数据类型
    )

    return arr


def numpy_to_text(arr, fmt='%.18e', delimiter=' ', newline='\n'):
    """
    将NumPy数组转换为文本字符串

    参数:
    arr : numpy.ndarray
        要转换的NumPy数组
    fmt : str or sequence of strs, 可选
        输出格式（默认：科学计数法高精度）
    delimiter : str, 可选
        列分隔符（默认：空格）
    newline : str, 可选
        行分隔符（默认：换行符 \n）

    返回:
    str : 数组的文本表示形式
    """
    # 创建内存中的文本流
    buffer = StringIO()

    # 将数组数据写入内存缓冲区
    np.savetxt(
        fname=buffer,
        X=arr,
        fmt=fmt,
        delimiter=delimiter,
        newline=newline
    )

    # 获取字符串内容并移除末尾多余换行
    result = buffer.getvalue().rstrip('\n')
    buffer.close()

    return result


def test_1():
    # 创建示例数组
    data = np.array([[1, 2.5], [3.33, 4]])

    # 转换为字符串（默认格式）
    print(numpy_to_text(data))
    # 输出：
    # 1.000000000000000000e+00 2.500000000000000000e+00
    # 3.330000000000000000e+00 4.000000000000000000e+00

    # 自定义格式和分隔符
    print(numpy_to_text(
        data,
        fmt='%.2f',
        delimiter=','
    ))
    # 输出：
    # 1.00,2.50
    # 3.33,4.00

    # 处理一维数组
    vector = np.array([1, 2, 3])
    print(numpy_to_text(vector, fmt='%d'))
    # 输出：
    # 1
    # 2
    # 3

def test_2():
    # 从之前保存的文本创建数组
    data_str = "1.0 2.5\n3.33 4.0"
    recovered = text_to_numpy(data_str)
    print("恢复的数组:")
    print(recovered)
    print("数据类型:", recovered.dtype)

    csv_str = "1.00,2.50\n3.33,4.00"
    arr_from_csv = text_to_numpy(csv_str, delimiter=',')
    print("带逗号分隔符的数组:")
    print(arr_from_csv)

    vector_str = "1\n2\n3"
    vector = text_to_numpy(vector_str)
    print("恢复的向量:")
    print(vector)
    print("形状:", vector.shape)


if __name__ == '__main__':
    test_2()