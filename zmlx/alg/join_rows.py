import numpy as np


def join_rows(*args):
    """
    堆叠具有相同列数但行数可能不同的矩阵。

    参数:
        matrices: 一个或多个NumPy矩阵。

    返回:
        堆叠后的矩阵。
    """
    return np.vstack(args)


def test():
    a = np.array([[1, 2], [3, 4]])
    b = np.array([[5, 6]])

    combined_matrix = join_rows(a, b)
    print(combined_matrix)


if __name__ == '__main__':
    test()
