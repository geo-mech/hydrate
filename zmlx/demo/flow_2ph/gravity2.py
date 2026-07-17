# ** desc = '重力驱动下的气水分层（非均匀初始条件）'
#
# 物理问题描述：
#   本模型与 gravity.py 类似，模拟重力作用下的气-水重力分异过程，
#   但初始饱和度在水平方向上有非均匀分布：
#     - 左半部分（x<=150m）：CH4占80%，H2O占20%（气富集区）
#     - 右半部分（x>150m）：CH4占20%，H2O占80%（水富集区）
#   通过这种非均匀初始分布，可以观察在重力分异和横向压力梯度
#   共同作用下，气水如何重新分布并最终达到重力-毛管平衡状态。
#
# 建模技术要点：
#   1. 复用 gravity.py 中的 create 和 show 函数
#   2. 自定义初始饱和度函数 get_s 实现水平方向非均匀分布
#   3. 其他参数与 gravity.py 保持一致

from zmlx import *


def main():
    """
    主函数：创建非均匀初始饱和度的重力分异模型。
    左半部气多水少，右半部水多气少，模拟100年的重力分异过程。
    """
    from zmlx.demo.flow_2ph.gravity import show, create
    def get_s(x, y, z):
        """定义非均匀初始饱和度：左侧CH4-rich，右侧H2O-rich。"""
        if x > 150:
            return {'ch4': 0.2, 'h2o': 0.8}  # 右侧：少数CH4，多数H2O
        else:
            return {'ch4': 0.8, 'h2o': 0.2}  # 左侧：多数CH4，少数H2O

    jx, jz = 30, 100
    model = create(jx, jz, s=get_s)
    show(model, jx, jz, caption='初始状态')
    tfc.solve(model, extra_plot=lambda: show(model, jx, jz, caption='当前状态'),
              time_forward=3600 * 24 * 365 * 100  # 模拟100年
              )


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
