import math
from random import uniform


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


if __name__ == '__main__':
    for i in range(30):
        print(rand_dir3())
