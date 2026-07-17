# ** desc = '模拟两个Cell，在压力和惯性的作用下，反复震荡的过程'
#
# 本案例演示了渗流动力学（流动惯性）的核心概念：
# 使用两个单元格（Cell）通过一个面（Face）连接，模拟压力差驱动下流体的往复震荡。
# 模型考虑了流体的可压缩性（通过pore设置）和流动惯性（通过face的k、q、s属性），
# 展示了在没有外部持续驱动时，系统由于压力差和惯性效应产生的振荡行为。
# 这是理解和验证渗流动力学算法的基础测试案例，与传统的稳态渗流不同，
# 动力学模式能够捕捉到压力波传播和流体惯性的瞬态效应。

from zmlx import *


def set_cell(c: Seepage.Cell, p):
    """
    设置单元格的孔隙属性和流体体积。

    参数:
        c: Seepage.Cell对象，待设置的单元格
        p: float，初始压力值，用于通过压力-体积关系计算初始流体体积
    """
    c.set_pore(p=1, v=1, dp=1, dv=0.5)  # 设置孔隙参数：参考压力p=1，参考体积v=1，压力变化范围dp=1，体积变化量dv=0.5
    c.fluid_number = 1                    # 设置单元格内流体组分的数量为1（单相流体）
    c.get_fluid(0).vol = c.p2v(p)         # 根据初始压力p计算并设置流体的体积（调用压力-体积转换函数）
    print(c.pre)                           # 输出该单元格的初始孔隙压力值


def main():
    """
    主函数：创建两个单元格和一个连接面，模拟压力差驱动下的流体震荡过程。

    步骤说明:
        1. 创建两个具有不同初始压力的单元格，形成压力梯度
        2. 通过一个面连接两个单元格，设置导流系数和动力学参数
        3. 注册单元格和面的属性键，用于动力学迭代计算
        4. 循环迭代200个时间步，记录压力、流量随时间的变化
        5. 每10步更新一次绘图，展示流量和压力曲线
    """
    model = Seepage()                      # 创建渗流模型实例

    set_cell(model.add_cell(), 1)          # 添加第一个单元格，初始压力设为1
    set_cell(model.add_cell(), 2)          # 添加第二个单元格，初始压力设为2（与第一个形成压力差）
    f = model.add_face(0, 1)               # 添加连接单元格0和单元格1的面，使流体可以交换
    f.cond = 1                              # 设置面的导流系数（传导率），控制流动的难易程度

    ca_p = model.reg_cell_key('p')         # 注册单元格属性键：压力（用于iterate中的压力参数）
    fa_k = model.reg_face_key('k')         # 注册面属性键：弹性系数（动力学模式中控制弹性响应）
    fa_q = model.reg_face_key('q')         # 注册面属性键：流量（动力学模式中记录流过面的流体流量）
    fa_s = model.reg_face_key('s')         # 注册面属性键：惯性系数（动力学模式中控制惯性效应）

    f.set_attr(fa_k, 1)                    # 设置面的弹性系数为1
    f.set_attr(fa_q, 0)                    # 初始化面的流量为0
    f.set_attr(fa_s, 1)                    # 设置面的惯性系数为1（控制流体惯性的强度）

    c0 = model.get_cell(0)                 # 获取第一个单元格的引用（用于后续读取压力）
    c1 = model.get_cell(1)                 # 获取第二个单元格的引用
    f = model.get_face(0)                  # 获取连接面的引用

    vt = []                                 # 存储时间步序列（用于绘图横坐标）
    vq = []                                 # 存储流量数据的序列
    p0 = []                                 # 存储单元格0的压力序列
    p1 = []                                 # 存储单元格1的压力序列

    def show(fig):
        """
        绘图回调函数：在指定的matplotlib图形对象上绘制流量和压力的时间变化曲线。

        参数:
            fig: matplotlib的Figure对象，用于在其中创建子图并绘制曲线
        """
        xy1 = item('xy', vt, vq)                                            # 流量随时间变化的曲线
        xy2 = item('xy', vt, p0, label='p0')                                # 单元格0压力随时间变化曲线（带图例标签）
        xy3 = item('xy', vt, p1, label='p1')                                # 单元格1压力随时间变化曲线
        add_axes2(fig, add_items, xy1, nrows=2, ncols=1, index=1, xlabel='x', ylabel='q')                   # 子图1：流量图
        add_axes2(fig, add_items, xy2, xy3, item('legend'), nrows=2, ncols=1, index=2, xlabel='x', ylabel='p')  # 子图2：压力对比图（含图例）

    for step in range(200):                # 主循环：迭代200个时间步
        gui.break_point()                  # GUI断点检查，允许用户在图形界面中中断长时间计算
        r = model.iterate(dt=0.1, fa_s=fa_s, fa_q=fa_q, fa_k=fa_k, ca_p=ca_p)  # 执行一个时间步的动力学迭代（时间步长dt=0.1）
        vt.append(step)                    # 记录当前迭代步数
        vq.append(f.get_attr(fa_q))        # 获取并记录当前流过面的流量
        p0.append(c0.pre)                  # 获取并记录单元格0的当前压力
        p1.append(c1.pre)                  # 获取并记录单元格1的当前压力
        if step % 10 == 0:                 # 每10步更新一次可视化图形（减少绘图开销）
            plot(show, caption='当前状态', tight_layout=True)  # 调用绘图函数展示当前状态
            print(f'step = {step}, r = {r}')  # 输出当前迭代步数和残差值


if __name__ == '__main__':
    # 通过GUI执行主函数；disable_gui参数允许在命令行使用--no-gui标志禁用图形界面（适用于服务器或批处理运行）
    gui.execute(main, close_after_done=False)
