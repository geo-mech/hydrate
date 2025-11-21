"""
给定空间的散点，计算各个散点位置的压力梯度.
todo:
    宇轩补全.
"""
from scipy.spatial import Delaunay

from zmlx.base.zml import np


def compute_pressure_gradient_2D(x, y, p):
    """
    根据散乱点 (x, y, p) 计算每个点上的压力梯度 (dp/dx, dp/dy)。
    x, y, p: 一维等长数组或列表
    返回值: 与 x, y 长度相同的二维数组 grad，每行是 (dp/dx, dp/dy)
    """
    # 转换为 numpy 数组
    x = np.asarray(x)
    y = np.asarray(y)
    p = np.asarray(p)

    # 组合坐标点
    points = np.column_stack((x, y))

    # 若点数太少，或者所有点共线等情况，无法进行三角剖分时，需要特殊处理
    if len(points) < 3:
        # 至少需要 3 个点才能三角剖分
        # 这里可以直接返回零梯度或根据需求处理
        return np.zeros((len(points), 2))

    # Delaunay 三角剖分
    tri = Delaunay(points)

    # 用于累计每个点的梯度和，以及统计该点参与的三角形数量
    grad_sum = np.zeros((len(points), 2), dtype=float)
    count = np.zeros(len(points), dtype=int)

    # 对每个三角形计算梯度，并加到对应的顶点上
    for simplex in tri.simplices:
        # 取出三角形顶点下标
        i0, i1, i2 = simplex
        # 顶点坐标
        x0, y0 = x[i0], y[i0]
        x1, y1 = x[i1], y[i1]
        x2, y2 = x[i2], y[i2]
        # 对应压力
        p0, p1, p2 = p[i0], p[i1], p[i2]

        # 组装矩阵 M 和向量 Δp
        M = np.array([[x1 - x0, y1 - y0],
                      [x2 - x0, y2 - y0]], dtype=float)
        dp = np.array([p1 - p0, p2 - p0], dtype=float)

        # 尝试求解梯度 g = M^-1 * dp
        # 若三点共线或矩阵奇异则捕获异常
        try:
            g = np.linalg.solve(M, dp)
        except np.linalg.LinAlgError:
            # 可能出现退化三角形(如三点共线)，可根据需求选择跳过或赋值0
            g = np.zeros(2)

        # 将这个三角形的梯度加到三个顶点上
        grad_sum[i0] += g
        grad_sum[i1] += g
        grad_sum[i2] += g

        # 同时计数
        count[i0] += 1
        count[i1] += 1
        count[i2] += 1

    # 对每个顶点求平均梯度
    # 避免除以0，安全起见可以加一个判断
    nonzero_mask = count > 0
    grad = np.zeros((len(points), 2), dtype=float)
    grad[nonzero_mask] = grad_sum[nonzero_mask] / count[nonzero_mask, None]

    return grad


if __name__ == "__main__":
    # 示例数据
    x_data = [0, 1, 2, 1]
    y_data = [0, 0, 0, 1]
    p_data = [1, 2, 3, 2.5]  # 压力值

    gradients = compute_pressure_gradient_2D(x_data, y_data, p_data)
    for i, (gx, gy) in enumerate(gradients):
        print(f"Point {i}: (x={x_data[i]}, y={y_data[i]}), "
              f"p={p_data[i]}, grad=({gx:.4f}, {gy:.4f})")


def compute_pressure_gradient_3D(x, y, z, p):
    """
    根据散乱点 (x, y, z, p) 计算每个点上的压力梯度 (dp/dx, dp/dy, dp/dz)。
    输入:
        x, y, z, p: 一维等长数组或列表
    输出:
        grad: (N, 3) 大小的数组，grad[i] = (dp/dx, dp/dy, dp/dz) 对应第 i 个点
    """
    # 转为 numpy 数组
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)
    p = np.asarray(p, dtype=float)

    points = np.column_stack((x, y, z))
    n_points = len(points)

    # 如果点太少或退化，无法进行 3D Delaunay
    if n_points < 4:
        # 根据需要可返回0，也可以抛出异常等
        return np.zeros((n_points, 3))

    # 3D Delaunay 剖分
    try:
        tri = Delaunay(points)
    except Exception as e:
        # 剖分失败（退化等），根据需求处理，这里简单返回0
        print(f"Delaunay failed: {e}")
        return np.zeros((n_points, 3))

    # 用于累计每个点的梯度和，以及统计该点被多少个四面体使用
    grad_sum = np.zeros((n_points, 3), dtype=float)
    count = np.zeros(n_points, dtype=int)

    # 遍历所有四面体
    for simplex in tri.simplices:
        i0, i1, i2, i3 = simplex
        # 顶点坐标
        x0, y0, z0 = x[i0], y[i0], z[i0]
        x1, y1, z1 = x[i1], y[i1], z[i1]
        x2, y2, z2 = x[i2], y[i2], z[i2]
        x3, y3, z3 = x[i3], y[i3], z[i3]
        # 对应标量值
        p0, p1, p2, p3 = p[i0], p[i1], p[i2], p[i3]

        # 组装矩阵 M 和向量 Δp
        M = np.array([
            [x1 - x0, y1 - y0, z1 - z0],
            [x2 - x0, y2 - y0, z2 - z0],
            [x3 - x0, y3 - y0, z3 - z0]
        ], dtype=float)
        dp = np.array([
            p1 - p0,
            p2 - p0,
            p3 - p0
        ], dtype=float)

        # 计算四面体内梯度 g = M^-1 * dp
        try:
            g = np.linalg.solve(M, dp)
        except np.linalg.LinAlgError:
            # 若四面体退化，无法求逆，这里简单设为0梯度
            g = np.zeros(3)

        # 将此梯度累加到四个顶点
        grad_sum[i0] += g
        grad_sum[i1] += g
        grad_sum[i2] += g
        grad_sum[i3] += g

        # 计数
        count[i0] += 1
        count[i1] += 1
        count[i2] += 1
        count[i3] += 1

    # 求平均梯度
    grad = np.zeros((n_points, 3), dtype=float)
    nonzero_mask = (count > 0)
    grad[nonzero_mask] = grad_sum[nonzero_mask] / count[nonzero_mask, None]

    return grad


if __name__ == "__main__":
    # 构造一些简易示例数据：这里用几个点模拟一个立方体角上的变化
    x_data = [0, 1, 1, 0, 0, 1, 1, 0]
    y_data = [0, 0, 1, 1, 0, 0, 1, 1]
    z_data = [0, 0, 0, 0, 1, 1, 1, 1]
    # 构造一个简单的标量场，比如 p = x + 2y + 3z
    p_data = [x_i + 2 * y_i + 3 * z_i for x_i, y_i, z_i in
              zip(x_data, y_data, z_data)]

    # 计算梯度
    gradients = compute_pressure_gradient_3D(x_data, y_data, z_data, p_data)

    # 输出
    for i, (gx, gy, gz) in enumerate(gradients):
        print(f"Point {i}: (x={x_data[i]}, y={y_data[i]}, z={z_data[i]}), "
              f"p={p_data[i]}, gradient=({gx:.4f}, {gy:.4f}, {gz:.4f})")
