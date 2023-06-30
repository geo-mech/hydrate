import numpy as np
import matplotlib.pyplot as plt
"""
计算两个三维空间的矩形的相交情况，相交返回交点，不相交返回None

by xutao 

2023.06.29
"""

# print控制
print_enable = True


def calculate_rectangle_vertices(center, midpoint1, midpoint2):
    """
    获取矩形顶点坐标

    :param center: 中心点
    :param midpoint1: 邻边1中点坐标
    :param midpoint2: 邻边2中点坐标
    :return: 四个顶点坐标
    """
    C = np.array(center)
    M1 = np.array(midpoint1)
    M2 = np.array(midpoint2)

    V1 = M1 - C
    V2 = M2 - C
    # 向量方法计算: 邻边1上顶点为起始，顺时针输出
    P1 = C + V1 + V2
    P2 = C + V1 - V2
    P3 = C - V1 - V2
    P4 = C - V1 + V2
    vertices = [P1, P2, P3, P4]
    return vertices


def calculate_max_centers_distance(vertices1, vertices2):
    """
    计算两个矩形对角线长度和的一半，判定两个矩形一定不会相交

    :param vertices1: 矩形1顶点坐标
    :param vertices2: 矩形2顶点坐标
    :return: 两个矩形对角线长度和一半
    """
    # 矩形1对角线长度
    length1 = np.linalg.norm(vertices1[0] - vertices1[2])

    # 矩形2对角线长度
    length2 = np.linalg.norm(vertices2[0] - vertices2[2])

    return (length1 + length2) / 2


def find_different_sign_index(arr):
    """
    找出不同符号的数的索引

    :param arr:np.array()
    :return: 是否存在不同符号的数，存在返回其索引
    """
    signs = np.sign(arr)
    unique_signs = np.unique(signs)

    if len(unique_signs) == 1:
        return None

    different_sign = unique_signs[0] if np.count_nonzero(
        signs == unique_signs[0]) == 1 else unique_signs[1]
    different_sign_index = np.where(signs == different_sign)[0][0]

    return different_sign_index


def get_points_distribution(local_z):
    """
    获得矩形1顶点的在矩形2的两侧分布情况

    :param local_z:局部坐标系下的矩形四个顶点z坐标
    :return: 返回点的分布情况及对应的索引（字典）
    """
    #获得四个z坐标的，检查四个数的符号
    assert len(local_z) == 4

    product = np.prod(local_z)
    signs = np.sign(local_z)
    unique_signs = np.unique(signs)
    if product > 0 and len(unique_signs) == 1:
        # 一侧四点
        return {'no': None}

    elif product > 0 and len(unique_signs) == 2:
        # 两侧两点
        positive_indices = np.where(np.array(local_z) > 0)[0]
        negative_indices = np.where(np.array(local_z) < 0)[0]
        return {'22': np.hstack((positive_indices, negative_indices))}

    elif product < 0 and len(unique_signs) == 2:
        # 一侧一点，一侧三点
        negative_index = find_different_sign_index(local_z)
        return {'13': negative_index}

    elif product == 0:
        # 点在面上
        zero_indices = np.where(np.array(local_z) == 0)[0]
        return {'inside': zero_indices}


def calculate_intersection_point(line_begin, line_end):
    """
    计算线段与局部坐标系X-O-Y的交点

    :param line_begin: 线段起始点坐标
    :param line_end: 线段结束点坐标
    :return: 线段与局部坐标系的交点
    """
    # z = 0, 利用向量共线计算交点x,y坐标
    x = (line_begin[0] * line_end[2] -
         line_begin[2] * line_end[0]) / (line_end[2] - line_begin[2])
    y = (line_begin[1] * line_end[2] -
         line_begin[2] * line_end[1]) / (line_end[2] - line_begin[2])
    return np.array([x, y])


def point_in_rectangle(point, rect2_local_xy_range):
    """
    判断二维平面中点是否在矩形内部

    :param point: 点坐标
    :param rectangle: local矩形2顶点的x_min, y_min, x_max, y_max
    :return: bool 内部：True；外部：False
    """
    x, y = point
    x_min, y_min, x_max, y_max = rect2_local_xy_range

    if x_min <= x <= x_max and y_min <= y <= y_max:
        return True
    else:
        return False


# 关于x和y的范围利用局部坐标系x和y轴去限制，不要自己定义
def line_rect_intersection(p1, p2, local_rect2, rect2_local_xy_range):
    """
    计算2d线段与矩形的位置情况

    :param p1: 线段起点
    :param p2: 线段终点
    :param local_rect2: 矩形2顶点local坐标
    :param rect2_local_xy_range: 矩形2local_xy范围x_min, y_min, x_max, y_max
    :return: 有交点返回交点，无交点返回None

    """
    # center到mid1的距离为x，center到mid2的距离为y
    rectangle = rect2_local_xy_range



    # 矩形的四个顶点
    r1, r2, r3, r4 = local_rect2

    # 矩形的四条边
    edges = [(r1, r2), (r2, r3), (r3, r4), (r4, r1)]
    
    intersections = []
    for edge in edges:
        intersection = line_line_intersection(p1, p2, edge[0], edge[1])
        if intersection is not None:
            intersections.append(intersection)
    # 如果两个点都在矩形内部，直接返回交点
    p1_bool = point_in_rectangle(p1, rectangle)
    p2_bool = point_in_rectangle(p2, rectangle)
    # 判断交点情况
    if p1_bool and p2_bool:
        return p1, p2
    elif len(intersections) == 0:
        # 线段与矩形边无交点
        return None
    else: 
        # 1个或2个交点
        return intersections


def line_line_intersection(p1, p2, p3, p4):
    """
    计算两条线之间的位置情况

    :param p1: 线段1起点
    :param p2: 线段1终点
    :param p3: 线段2起点
    :param p4: 线段2终点
    :return: 相交返回顶点，不相交返回None
    """
    # 利用numpy求解两条线段的交点
    A = np.array([[p2[0] - p1[0], p3[0] - p4[0]],
                  [p2[1] - p1[1], p3[1] - p4[1]]])
    b = np.array([p3[0] - p1[0], p3[1] - p1[1]])
    try:
        t, s = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return None
    if 0 <= t <= 1 and 0 <= s <= 1:
        return np.array(
            [p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1])])
    else:
        return None


def plot_rectangle(vertices, ax):
    """
    绘制矩形轮廓

    :param vertices: 矩形四个点坐标
    :param ax: plt轴对象
    :return: 矩形轮廓绘图结果
    """
    # 提取顶点坐标的x、y、z分量
    x = [vertex[0] for vertex in vertices]
    y = [vertex[1] for vertex in vertices]
    z = [vertex[2] for vertex in vertices]

    # 连接矩形的四个顶点
    ax.plot([x[0], x[1]], [y[0], y[1]], [z[0], z[1]], 'b-')
    ax.plot([x[1], x[2]], [y[1], y[2]], [z[1], z[2]], 'b-')
    ax.plot([x[2], x[3]], [y[2], y[3]], [z[2], z[3]], 'b-')
    ax.plot([x[3], x[0]], [y[3], y[0]], [z[3], z[0]], 'b-')


def calculate_3d_rectangle_intersect(center1, r1_mid1, r1_mid2, center2,
                                     r2_mid1, r2_mid2):
    """
    判断三维空间中的两个矩形的相交情况，并计算交线

    :param center1: 矩形1中心点
    :param r1_mid1: 矩形1邻边中点1
    :param r1_mid2: 矩形1邻边中点2
    :param center1: 矩形2中心点
    :param r1_mid1: 矩形2邻边中点1
    :param r1_mid2: 矩形2邻边中点2
    :return: 相交情况，有交线返回交线，无交线返回None，相同平面相互包含返回一个标签？
    """
    # 获取矩形的四个顶点坐标
    rect1_vertices = calculate_rectangle_vertices(center1, r1_mid1, r1_mid2)
    rect2_vertices = calculate_rectangle_vertices(center2, r2_mid1, r2_mid2)

    # 获取矩形相交情况下，中心点最大距离
    max_distance = calculate_max_centers_distance(rect1_vertices,
                                                  rect2_vertices)

    # 矩形中心点距离
    distance = np.linalg.norm(np.array(center1) - np.array(center2))

    # 定义距离精度
    e_dist = 0

    # 判断是否可能相交
    if distance - max_distance > e_dist:
        if print_enable:
            print("两个矩形不可能相交")
        return None
    else:
        # 矩形2中心点为O，中心点到mid1,mid2分别为X、Y轴，两轴叉乘法向量为Z轴
        vector_x = np.array(r2_mid1) - np.array(center2)
        vector_y = np.array(r2_mid2) - np.array(center2)
        vector_z = np.cross(vector_x, vector_y)
        norm_x = np.linalg.norm(vector_x)
        norm_y = np.linalg.norm(vector_y)
        norm_z = np.linalg.norm(vector_z)
        vector_x_unit = vector_x / norm_x
        vector_y_unit = vector_y / norm_y
        vector_z_unit = vector_z / norm_z

        # 获取旋转矩阵
        rotation_matrix = np.vstack(
            (vector_x_unit, vector_y_unit, vector_z_unit))

        # 将全局坐标转换为局部坐标 右上开始，顺指针输出坐标，
        # 局部坐标定义: 矩形2中心点为O，中心点到mid1,mid2分别为X、Y轴，两轴叉乘法向量为Z轴
        # 全局->局部：全局坐标先减去局部坐标中心点（矩形2中心）再与旋转矩阵转置做点积
        #! 点积注意顺序，无交换律
        local_coord = [
            np.dot((vertex - np.array(center2)), rotation_matrix.T)
            for vertex in rect1_vertices
        ]

        # 计算局部坐标系下矩形2的四个顶点坐标：计算长宽即可得到，x和y方向的长度
        local_rect2_vertices = (
            np.array([norm_x, norm_y]),
            np.array([norm_x, -norm_y]),
            np.array([-norm_x, -norm_y]),
            np.array([-norm_x, norm_y]),
        )

        # 局部坐标系下矩形2的xy轴取值范围
        rect2_local_xy_range = -norm_x, -norm_y, norm_x, norm_y

        # 判断点分布情况：13分布/22分布 -利用局部坐标系下的local_z的符号判断
        local_z = [vertex[2] for vertex in local_coord]

        # 获取分布情况
        # no: None; 22: positive_indices, negative_indices
        # 13: negative_indices; inside: zero_indices
        distribution = get_points_distribution(local_z)
        label = list(distribution.keys())[0]
        value = list(distribution.values())[0]

        if print_enable:
            print(f'相交情况：{label}')

        if label == 'no':
            # 一侧四点 无交点
            return None

        elif label == 'inside':
            # 矩形1顶点在矩形2的平面上
            if len(value) == 1:
                # 一个点在相同平面
                inside = point_in_rectangle(local_coord[value],
                                            rect2_local_xy_range)
                if inside:
                    # 该点在矩形内部
                    return local_coord[value]
                else:
                    # 该点在矩形外部
                    return None
            elif len(value) == 2:
                # 两个点在相同平面
                point1 = local_coord[value[0]]
                point2 = local_coord[value[1]]
                return line_rect_intersection(point1, point2,
                                              rect2_local_xy_range)
            else:
                #todo 两个矩形在相同平面，包含，相离，相交等尚未实现
                assert len(value) == 4

                return '相同平面'

        elif label == '22':
            # 22分布
            intersec1 = calculate_intersection_point(local_coord[value[0]],
                                                     local_coord[value[2]])
            intersec2 = calculate_intersection_point(local_coord[value[1]],
                                                     local_coord[value[3]])

        elif label == '13':
            # 13分布
            if value == 1 or value == 2:
                intersec1 = calculate_intersection_point(
                    local_coord[value], local_coord[value + 1])
                intersec2 = calculate_intersection_point(
                    local_coord[value], local_coord[value - 1])
            elif value == 0:
                intersec1 = calculate_intersection_point(
                    local_coord[0], local_coord[1])
                intersec2 = calculate_intersection_point(
                    local_coord[0], local_coord[3])
            else:
                assert value == 3
                intersec1 = calculate_intersection_point(
                    local_coord[3], local_coord[0])
                intersec2 = calculate_intersection_point(
                    local_coord[3], local_coord[2])

        # 交线与X-O-Y平面内的矩形的关系：一个交点，两个交点，无交点（相离，包含）
        local_intersect_line = line_rect_intersection(intersec1, intersec2,
                                                      local_rect2_vertices,
                                                      rect2_local_xy_range)

        # 判断交点是否在矩形内部
        p1_bool = point_in_rectangle(intersec1, rect2_local_xy_range)
        p2_bool = point_in_rectangle(intersec2, rect2_local_xy_range)


        # 判断局部坐标系下是否存在交点
        if local_intersect_line is None:
            #不存在交点
            return None
        # 存在交点
        elif len(local_intersect_line) == 1:
            # 交点为顶点，且线段端点均在2d矩形外部
            assert (p1_bool and p2_bool) is not True
            if p1_bool ==  True and p2_bool == False:
                local_intersect_line.append(intersec1)
            elif p1_bool ==  False and p2_bool == True:
                local_intersect_line.append(intersec2)
            
        # 添加z轴，设置为零
        z_coordinates = np.array([0])

        # 为二维坐标添加z值
        local_intersect_line_3d = [
            np.hstack((vertex, z_coordinates))
            for vertex in local_intersect_line
        ]

        # 局部->全局: 坐标p 点乘 旋转矩阵R 再加上局部坐标系原点坐标
        global_intersect_line = [
            np.dot(vertex, rotation_matrix) + np.array(center2)
            for vertex in local_intersect_line_3d
        ]
        return global_intersect_line


if __name__ == '__main__':
    # 输入矩形定义坐标

    # 创建3D图形对象
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # 读取坐标数据
    d = np.loadtxt('D:/Daily/2023.06.15 矩形相交算法/vertices.txt')

    # 读取demo相交索引数据
    demo_links = np.loadtxt('D:/Daily/2023.06.15 矩形相交算法/demo_links.txt',
                            dtype=int)

    # 读取计算相交索引数据
    cal_links = np.loadtxt('D:/Daily/2023.06.15 矩形相交算法/cal_links.txt',
                           dtype=int)

    # 定义矩形
    rect1 = d[int(demo_links[1023][0])]

    rect2 = d[int(demo_links[1023][1])]

    # 代码计算相交情况
    intersect = calculate_3d_rectangle_intersect(
        (rect1[0], rect1[1], rect1[2]), (rect1[3], rect1[4], rect1[5]),
        (rect1[6], rect1[7], rect1[8]), (rect2[0], rect2[1], rect2[2]),
        (rect2[3], rect2[4], rect2[5]), (rect2[6], rect2[7], rect2[8]))
    print(intersect)

    # 绘制两个矩形
    plot_rectangle(
        calculate_rectangle_vertices((rect1[0], rect1[1], rect1[2]),
                                     (rect1[3], rect1[4], rect1[5]),
                                     (rect1[6], rect1[7], rect1[8])), ax)
    plot_rectangle(
        calculate_rectangle_vertices((rect2[0], rect2[1], rect2[2]),
                                     (rect2[3], rect2[4], rect2[5]),
                                     (rect2[6], rect2[7], rect2[8])), ax)

    # 显示图形
    plt.show()