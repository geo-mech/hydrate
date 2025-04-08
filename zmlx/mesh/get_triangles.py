import numpy as np
from scipy.spatial import Delaunay


def get_triangles(points):
    """
    给定二维点列表，返回由点索引构成的所有非退化三角形
    (每个三角形由三个点索引组成，从0开始计数)

    Args:
        points: 二维点列表，格式 [(x0,y0), (x1,y1), ...]

    Returns:
        三角形列表，格式 [[i,j,k], ...]，其中i,j,k为点索引
    """
    if len(points) < 3:
        return []

    points_array = np.array(points)

    try:
        tri = Delaunay(points_array)
    except:
        return []

    triangles = []
    for simplex in tri.simplices:
        # 获取三个点坐标
        a, b, c = points_array[simplex]

        # 计算向量叉积判断共线性
        cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        if abs(cross) < 1e-10:  # 浮点数容差处理
            continue

        # 转换为Python原生int类型
        triangles.append([int(i) for i in simplex])

    return triangles
