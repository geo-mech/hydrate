# ** desc = 'matplotlib绘图示例'
#
# 本案例演示在循环计算过程中实时更新折线图。模拟一个长时间计算任务
# （heavy_work），在每次迭代中更新sin(x)曲线并刷新图形窗口。同时展示
# gui.progress进度条和gui.break_point中断点的使用，用于在GUI模式中
# 提供交互反馈和控制。这是tfc求解器外部循环绘图的标准模式。

from zmlx import *


def heavy_work(count=1000):
    """
    模拟长时间计算任务，实时更新sin(x)曲线

    循环执行指定次数，每次迭代中：
      1. 更新进度条
      2. 调用break_point检查是否需要中断
      3. 移动x数据并计算新的sin(x)
      4. 更新绘图窗口

    Args:
        count: 迭代总次数（默认1000）
    """
    from time import sleep
    # 初始化x坐标（0到15之间取100个点）
    x = np.linspace(0, 15, 100)
    for idx in range(count):
        # 显示进度条
        gui.progress(label='执行进度', val_range=[0, count], value=idx,
                     visible=True)
        # 检查是否触发中断（用户点击停止时退出循环）
        gui.break_point()
        sleep(0.02)
        print(f'step = {idx}/{count}')

        # 向右平移数据并计算正弦值
        x += 1
        y = np.sin(x)

        def on_figure(fig):
            """在figure上绘制sin(x)折线图"""
            ax = fig.add_subplot()
            ax.plot(x, y)

        # 清除之前图形并绘制新曲线
        plot(on_figure, clear=True, caption='sin(x)')
    # 隐藏进度条
    gui.progress(visible=False)


if __name__ == '__main__':
    gui.execute(heavy_work, close_after_done=False)
