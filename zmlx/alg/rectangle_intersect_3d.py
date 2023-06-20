import numpy as np
import matplotlib.pyplot as plt


# 根据中心点和两条邻边中点坐标获取四个顶点坐标：右上开始，顺指针输出坐标
def calculate_rectangle_vertices(center, midpoint1, midpoint2):
    C = np.array(center)
    M1 = np.array(midpoint1)
    M2 = np.array(midpoint2)

    V1 = M1 - C
    V2 = M2 - C
    # 向量方法计算
    P1 = C + V1 + V2
    P2 = C + V1 - V2
    P3 = C - V1 - V2
    P4 = C - V1 + V2
    vertices = [P1, P2, P3, P4]
    return vertices


# 如果距离大于两个矩形对角线长度的和的一半，那么可以判定两个矩形一定不会相交
def calculate_max_centers_distance(vertices1, vertices2):
    # 矩形1对角线长度
    length1 = np.linalg.norm(vertices1[0] - vertices1[2])

    # 矩形2对角线长度
    length2 = np.linalg.norm(vertices2[0] - vertices2[2])

    return (length1 + length2) / 2


# 判断矩形1的四个点是否在矩形2平面的同一侧
def judge_same_side(vertices1, vertices2):
    # 获取平面内一个点
    point_on_plane = vertices2[0]

    # 计算平面法向量
    vector1 = vertices2[0] - vertices2[1]
    vector2 = vertices2[0] - vertices2[2]
    normal_vector = np.cross(vector1, vector2)

    # 判断是否同一侧
    same_side = True
    for point in vertices1:
        vector = point - point_on_plane
        dot_product = np.dot(vector, normal_vector)
        if dot_product < 0:
            same_side = False
            break

    return same_side


# 计算变换矩阵和逆变换矩阵
def calculate_transform_matrix(vertices):
    # 获取矩形2的中心点和邻边中点坐标
    center2 = (vertices[0] + vertices[2]) / 2
    mid1 = (vertices[1] - vertices[2]) / 2
    mid2 = (vertices[3] - vertices[2]) / 2
    # 获取矩形2局部坐标系的xyz单位向量
    vector_x = mid1 - center2
    vector_y = mid2 - center2
    vector_z = np.cross(vector_x, vector_y)
    vector_x_unit = vector_x / np.linalg.norm(vector_x)
    vector_y_unit = vector_y / np.linalg.norm(vector_y)
    vector_z_unit = vector_z / np.linalg.norm(vector_z)

    # 得到变换矩阵
    transform_matrix = np.vstack((vector_x_unit, vector_y_unit, vector_z_unit))

    # 计算逆变换矩阵
    inverse_transform_matrix = np.linalg.inv(transform_matrix)

    return transform_matrix, inverse_transform_matrix


# 找出不同符号的数的索引
def find_different_sign_index(arr):
    signs = np.sign(arr)
    unique_signs = np.unique(signs)

    if len(unique_signs) == 1:
        return None

    different_sign = unique_signs[0] if np.count_nonzero(
        signs == unique_signs[0]) == 1 else unique_signs[1]
    different_sign_index = np.where(signs == different_sign)[0][0]

    return different_sign_index


# 获得矩形1顶点的在矩形2的两侧分布情况
def get_points_distribution(local_z):
    #获得四个z坐标的，检查四个数的符号
    product = np.prod(local_z)
    if product > 0:
        print("两侧两点")
        return None
    else:
        # 找出不同符号的数的索引
        negative_index = find_different_sign_index(local_z)
        print(f"一侧一点，一侧三点，一点索引为{negative_index}")
        return negative_index


# 计算线段与局部坐标系X-O-Y的交点
def calculate_intersection_point(line_begin, line_end):
    # z = 0, 利用向量共线计算交点x,y坐标
    x = (line_begin[0] * line_end[2] -
         line_begin[2] * line_end[0]) / (line_end[2] - line_begin[2])
    y = (line_begin[1] * line_end[2] -
         line_begin[2] * line_end[1]) / (line_end[2] - line_begin[2])
    return np.array([x, y])


# 判断点是否在矩形内部
def point_in_rectangle(point, rectangle):
    x, y = point
    x_min, y_min, x_max, y_max = rectangle

    if x_min <= x <= x_max and y_min <= y <= y_max:
        return True
    else:
        return False


# 计算线段与矩形的位置情况
def line_rect_intersection(p1, p2, rect):
    # 矩形的四个顶点
    r1, r2, r3, r4 = rect
    x_min = -r1[0]
    x_max = r1[0]
    y_min = -r1[1]
    y_max = r1[1]
    rectangle = x_min, y_min, x_max, y_max
    # 矩形的四条边
    edges = [(r1, r2), (r2, r3), (r3, r4), (r4, r1)]
    intersections = []
    for edge in edges:
        intersection = line_line_intersection(p1, p2, edge[0], edge[1])
        if intersection is not None:
            intersections.append(intersection)
    # 判断交点情况
    if len(intersections) == 0:
        # 线段与矩形边无交点
        if point_in_rectangle(p1, rectangle) and point_in_rectangle(
                p2, rectangle):
            # 包含
            return p1, p2
        else:
            # 相离
            return None
    elif len(intersections) == 1:
        # 一个交点
        return intersections[0]
    elif len(intersections) == 2:
        # 两个交点
        return intersections


# 计算两条线之间的位置情况
def line_line_intersection(p1, p2, p3, p4):
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


# 绘制矩形轮廓
def plot_rectangle(vertices):
    # 创建3D图形对象
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # 提取顶点坐标的x、y、z分量
    x = [vertex[0] for vertex in vertices]
    y = [vertex[1] for vertex in vertices]
    z = [vertex[2] for vertex in vertices]

    # 连接矩形的四个顶点
    ax.plot([x[0], x[1]], [y[0], y[1]], [z[0], z[1]], 'b-')  # 右上到右下
    ax.plot([x[1], x[2]], [y[1], y[2]], [z[1], z[2]], 'b-')  # 右下到左下
    ax.plot([x[2], x[3]], [y[2], y[3]], [z[2], z[3]], 'b-')  # 左下到左上
    ax.plot([x[3], x[0]], [y[3], y[0]], [z[3], z[0]], 'b-')  # 左上到右上

    # 设置坐标轴标签
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    # 显示图形
    plt.show()



def calculate_3d_rectangle_intersect(center1, edge1_center1, edge2_center1,
                                     center2, edge1_center2, edge2_center2):
    """
    判断三维空间中的两个矩形的相交情况，并计算交线
    """
    # 获取矩形的四个顶点坐标
    rect1_vertices = calculate_rectangle_vertices(center1, edge1_center1,
                                                  edge2_center1)
    rect2_vertices = calculate_rectangle_vertices(center2, edge1_center2,
                                                  edge2_center2)

    # 获取矩形相交情况下，中心点最大距离
    max_distance = calculate_max_centers_distance(rect1_vertices,
                                                  rect2_vertices)

    # 矩形中心点距离
    distance = np.linalg.norm(np.array(center1) - np.array(center2))

    # 定义距离精度
    e_dist = 0.1

    # 判断是否可能相交
    if distance - max_distance > e_dist:
        print("两个矩形不可能相交")
        return None
    else:

        # 判断其中一个矩形四个顶点是否在另外一个矩形的同一侧
        if judge_same_side(rect1_vertices, rect2_vertices):
            print("四个点均在同侧，不可能相交")
            return None
        else:
            #! 一个点或者两个点在不同侧，计算交线
            # 获取变换矩阵及逆变换矩阵 注意：1x2的列表，[变换矩阵,逆变换矩阵]
            tranform_matrix = calculate_transform_matrix(rect2_vertices)

            # 将全局坐标转换为局部坐标 右上开始，顺指针输出坐标，
            # 局部坐标定: 矩形2中心点为O，中心点到邻边中心点分别为XY轴，两轴叉乘法向量为Z轴
            local_coord = [
                np.dot(tranform_matrix[0], vertex) for vertex in rect1_vertices
            ]

            # 计算局部坐标系下矩形2的四个顶点坐标：计算长宽即可得到
            width = np.linalg.norm(
                np.array(rect2_vertices[0]) - np.array(rect2_vertices[1]))
            length = np.linalg.norm(
                np.array(rect2_vertices[1]) - np.array(rect2_vertices[2]))
            local_rect2_vertices = (
                np.array([length / 2, width / 2]),
                np.array([length / 2, -width / 2]),
                np.array([-length / 2, -width / 2]),
                np.array([-length / 2, width / 2]),
            )

            # 判断点分布情况：13分布/22分布 -利用局部坐标系下的local_z的符号判断
            local_z = [vertex[2] for vertex in local_coord]
            distribution = get_points_distribution(local_z)

            if distribution == None:
                # 22分布
                intersec1 = calculate_intersection_point(
                    local_coord[0], local_coord[1])
                intersec2 = calculate_intersection_point(
                    local_coord[2], local_coord[3])
                print(intersec1, intersec2)
            else:
                # 13分布 此时distribution为单独一侧点的索引
                intersec1 = calculate_intersection_point(
                    local_coord[distribution], local_coord[distribution + 1])
                intersec2 = calculate_intersection_point(
                    local_coord[distribution], local_coord[distribution - 1])

            # 交线与X-O-Y平面内的矩形的关系：一个交点，两个交点，无交点（相离，包含）
            local_intersect_line = line_rect_intersection(
                intersec1, intersec2, local_rect2_vertices)

            # 判断局部坐标系下是否存在交点
            if local_intersect_line == None:
                #不存在交点
                return None

            else:  # 存在交点
                # 添加z轴，设置为零
                z_coordinates = np.array([0])

                # 为二维坐标添加z值
                local_intersect_line_3d = [
                    np.hstack((vertex, z_coordinates))
                    for vertex in local_intersect_line
                ]

                # 变换回全局坐标
                global_intersect_line = [
                    np.dot(tranform_matrix[1], vertex)
                    for vertex in local_intersect_line_3d
                ]
                return global_intersect_line


if __name__ == '__main__':
    # 输入矩形定义坐标

    # test1
    # center1 = (0, 0, 0)
    # edge1_center1 = (1, 0, 0)
    # edge2_center1 = (0, 1, 0)

    # center2 = (0, 0, 0)
    # edge1_center2 = (1, 0, 0)
    # edge2_center2 = (0, 1, 1)

    # test2
    center1 = (0, 0, 0)
    edge1_center1 = (0.2, 0, 0)
    edge2_center1 = (0, 1, 1)

    center2 = (0, 0, 0)
    edge1_center2 = (1, 0, 0)
    edge2_center2 = (0, 1, 0)

    intersect = calculate_3d_rectangle_intersect(center1, edge1_center1,
                                                 edge2_center1, center2,
                                                 edge1_center2, edge2_center2)
    print(intersect)