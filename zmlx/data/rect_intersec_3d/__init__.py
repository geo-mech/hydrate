from zmlx.base.zml import *

# 读取生成的相交矩阵序号
demo_path = os.path.join(os.path.dirname(__file__), 'demo_links.txt')

# 读取矩形定义坐标
vertices_path = os.path.join(os.path.dirname(__file__), 'vertices.txt')

# 读取计算得到的相交矩阵序号

result_path = os.path.join(os.path.dirname(__file__), 'cal_links.txt')


def get_demo_rect_index():
    """
    读取生成的相交矩阵序号
    """
    return np.loadtxt(demo_path, dtype=int)


def get_demo_rect_vertices():
    """
    读取矩形定义坐标
    """
    return np.loadtxt(vertices_path)


def get_cal_rect_index():
    """
    读取计算得到的相交矩阵序号
    """
    return np.loadtxt(result_path, dtype=int)


if __name__ == '__main__':
    print(get_demo_rect_index())
