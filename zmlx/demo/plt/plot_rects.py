import matplotlib.pyplot as plt

from zmlx.geometry.rect_3d_intersection import calculate_rectangle_vertices, \
    calculate_3d_rectangle_intersect
from zmlx.data import rect_intersec_3d as rect

"""
单独绘制两个矩形，观察相交情况是否与计算一致、

by xutao

"""


def plot_rectangle(vertices, ax):
    """
    绘制矩形轮廓
    """
    # 提取顶点坐标的x、y、z分量
    x = [vertex[0] for vertex in vertices]
    y = [vertex[1] for vertex in vertices]
    z = [vertex[2] for vertex in vertices]

    # 连接矩形的四个顶点
    ax.plot([x[0], x[1]], [y[0], y[1]], [z[0], z[1]], 'b-')  # 右上到右下
    ax.plot([x[1], x[2]], [y[1], y[2]], [z[1], z[2]], 'b-')  # 右下到左下
    ax.plot([x[2], x[3]], [y[2], y[3]], [z[2], z[3]], 'b-')  # 左下到左上
    ax.plot([x[3], x[0]], [y[3], y[0]], [z[3], z[0]], 'b-')  # 左上到右上


if __name__ == '__main__':
    # 创建3D图形对象
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # 读取坐标数据
    d = rect.get_demo_rect_vertices()

    # 读取demo相交索引数据
    demo_links = rect.get_demo_rect_index()

    # 读取计算相交索引数据
    cal_links = rect.get_cal_rect_index()

    # 定义矩形
    rect1 = d[int(cal_links[0][0])]

    rect2 = d[int(cal_links[0][1])]

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
