# ** desc = '创建一个三维的DFN(竖直的裂缝)并且基于pg来显示'

# 本案例演示三维离散裂隙网络（DFN）的创建和可视化。
# 物理问题：在三维空间中生成一组随机分布的竖直裂缝面，模拟天然裂缝性储层
# 中的裂缝网络结构。每个裂缝具有随机的位置、尺寸和方向。
# 建模方法：使用dfn_v3模块创建DFN模型，通过to_rc3函数将DFN转换为
# RC3格式（一种三维几何表示），然后使用pg（绘图引擎）进行三维可视化，
# 并对每个裂缝面赋予随机的颜色和透明度值以区分显示。

from zmlx import *
from zmlx.pg.show_rc3 import show_rc3


def test():
    """
    测试三维DFN的创建和可视化。

    生成一个DFN样例模型，将裂缝网络转换为RC3三维几何格式，
    并为每个裂缝面赋予随机的颜色和透明度，使用pg引擎进行三维显示。

    通过随机颜色和透明度可以直观地区分不同的裂缝面，观察裂缝网络的
    空间分布特征（裂缝密度、走向、连通性等）。
    """
    import random
    # 创建DFN示例数据并转换为RC3几何格式
    rc3 = dfn_v3.to_rc3(dfn_v3.create_demo())
    color = []
    alpha = []
    # 为每个裂缝面生成随机颜色和透明度
    for _ in rc3:
        color.append(random.uniform(0, 1))      # 随机灰度颜色
        alpha.append(random.uniform(0, 1) ** 3)  # 随机透明度（立方映射使更多面偏透明）
    show_rc3(rc3, color=color, alpha=alpha, caption='dfn_v3')


if __name__ == '__main__':
    gui.execute(test, close_after_done=False)
