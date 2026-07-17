# ** desc = '创建三维的DFN(竖直的裂缝)并且基于plt来显示，测试绘图的效率'

# 本案例测试使用matplotlib（plt）对三维离散裂隙网络（DFN）进行大量重复绘图的效率。
# 物理问题：在三维空间中生成随机分布的竖直裂缝面，每个裂缝具有随机的位置和尺寸，
# 模拟天然裂缝性储层中的裂缝网络。
# 建模方法：使用dfn_v3模块创建DFN模型并转换为RC3三维几何格式，通过show_rc3函数
# 使用matplotlib进行批量渲染。重复100次绘图中，每次生成新的随机颜色和透明度，
# 以测试大规模三维裂缝网络绘制的性能表现。
# 与dfn_v3.py不同，本案例侧重性能测试，使用了更完整的可视化配置（颜色条、标题等）。

from zmlx import *


def test():
    """
    测试三维DFN在matplotlib下的绘图效率。

    循环100次，每次重新生成DFN并绘制，以评估三维裂缝网络可视化性能。
    每个裂缝面使用随机的颜色和透明度值，并在图形中添加颜色条（colorbar）和标题。

    通过多次重复绘图测试：
    - 绘图引擎的渲染性能
    - 大规模裂缝网络（约1500条裂缝）的显示效果
    - 颜色条和标题等附加功能的正确性
    """
    import random
    for i in range(100):
        print(f'i = {i}')
        # 创建DFN示例数据并转换为RC3几何格式
        rc3 = dfn_v3.to_rc3(dfn_v3.create_demo())
        color = []
        alpha = []
        # 为每个裂缝面生成随机颜色和透明度
        for _ in rc3:
            color.append(random.uniform(0, 1))       # 随机灰度颜色
            alpha.append(random.uniform(0.3, 1))     # 随机透明度（0.3~1之间）
        show_rc3(
            rc3, face_color=color, face_alpha=alpha, caption='dfn_v3',
            cbar=dict(label='Random Value', shrink=.7),  # 添加颜色条
            title='dfn_v3, Index = %d' % i,
        )


if __name__ == '__main__':
    gui.execute(test, close_after_done=False)
