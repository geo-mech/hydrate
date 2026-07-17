# ** desc = '两相流，流体注入驱替。这里，创建多个模型，并行地执行'
#
# 本示例在两相流驱替的基础上演示并行计算功能。
# 创建5个具有不同随机参数的两相流模型（网格尺寸、流体粘度、注入井位置各异），
# 使用线程池（ThreadPool）对多个模型同时进行时间步进迭代，大幅提升计算效率。
# 每个时间点迭代完成后，分别显示各模型的压力场和饱和度场。
# 该示例展示了zmlx在多模型蒙特卡洛模拟或参数敏感性分析中的应用。

from zmlx import *
from zmlx.demo.others.liq_inj import show_model, create  # 复用liq_inj.py中的模型创建和可视化函数


def main():
    """
    主函数：并行求解多个随机两相流模型。

    创建5个具有不同随机参数的模型（网格尺寸、流体粘度、注入井位置不同），
    使用线程池进行并行时间步进迭代。在0到1年之间等间隔选取5个时间点，
    在每个时间点先并行推进所有模型，然后逐个显示各模型的当前状态。

    并行计算原理：将多个模型提交到线程池，每个线程负责一个模型的
    时间步进计算，利用多核CPU加速批处理模拟。

    Returns:
        无返回值。各模型的求解结果保存在各自的迭代过程中。
    """
    models = [create() for _ in range(5)]  # 创建5个具有不同随机参数的两相流模型

    pool = ThreadPool()  # 创建线程池，用于并行计算

    # 在0~1年之间等间隔选取5个时间点进行迭代
    for time in np.linspace(0, 3600 * 24 * 365, 5):
        print(f'target time = {time2str(time)}')
        tfc.iterate_until(*models, target_time=time, pool=pool)  # 使用线程池并行推进所有模型
        for model in models:
            show_model(model)  # 每个时间点显示各模型的当前状态


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
