# ** desc = 'matplotlib绘图示例'
#
# 本案例演示使用matplotlib的voxels函数绘制三维体素图，构建NumPy标志。
# 通过定义3D布尔数组确定体素填充位置，使用explode函数在体素间创建间隙，
# 模拟"像素风"三维字母效果。体素图在三维地质建模中可用于显示岩性分布、
# 矿体形状、孔隙结构等离散属性体。

from zmlx import *


def on_figure(fig):
    """
    在figure上绘制NumPy标志的三维体素图

    使用4x3x4的体素网格构建"N"字母形状，通过explode函数放大网格并
    在体素间插入空隙，形成三维像素风格效果。体素的前景和背景使用
    不同的颜色和边缘色。

    Args:
        fig: matplotlib.figure.Figure对象
    """

    def explode(data):
        """
        放大体素数据：每个维度扩展为原来的2倍，在体素间创建间隙

        原始数据中每个体素在扩展后占据(2,2,2)区域中的(0,0,0)位置，
        其余位置留空形成间隙。

        Args:
            data: 任意维度的numpy数组
        Returns:
            data_e: 尺寸为2*shape-1的扩展数组
        """
        size = np.array(data.shape) * 2
        data_e = np.zeros(size - 1, dtype=data.dtype)
        data_e[::2, ::2, ::2] = data
        return data_e

    # 构建NumPy标志的体素表示（N字母形状）
    n_voxels = np.zeros((4, 3, 4), dtype=bool)
    n_voxels[0, 0, :] = True       # N的左侧竖线
    n_voxels[-1, 0, :] = True      # N的右侧竖线
    n_voxels[1, 0, 2] = True       # N的斜线部分
    n_voxels[2, 0, 1] = True       # N的斜线部分
    # 设置前景和背景颜色（含透明度）
    facecolors = np.where(n_voxels, '#FFD65DC0', '#7A88CCC0')
    edgecolors = np.where(n_voxels, '#BFAB6E', '#7D84A6')
    filled = np.ones(n_voxels.shape)

    # 放大体素数据，在体素间创建间隙
    filled_2 = explode(filled)
    fcolors_2 = explode(facecolors)
    ecolors_2 = explode(edgecolors)

    # 调整间隙大小：每个放大后的体素在原始位置偏移形成可视间隙
    x, y, z = np.indices(np.array(filled_2.shape) + 1).astype(float) // 2
    x[0::2, :, :] += 0.05
    y[:, 0::2, :] += 0.05
    z[:, :, 0::2] += 0.05
    x[1::2, :, :] += 0.95
    y[:, 1::2, :] += 0.95
    z[:, :, 1::2] += 0.95

    # 创建三维坐标轴并绘制体素图
    ax = fig.add_subplot(projection='3d')
    ax.voxels(x, y, z, filled_2, facecolors=fcolors_2, edgecolors=ecolors_2)
    ax.set_aspect('equal')    # 保持各轴比例一致


if __name__ == '__main__':
    plot(on_figure, gui_mode=True)
