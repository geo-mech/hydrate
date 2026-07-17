# ** desc = '一维的模型，初始一端的压力比较高，计算此压力的传递和震荡过程'
#
# 本案例构建了一个一维（1D）渗流动力学模型：
# 沿一条直线排列30个单元格，左侧10个单元格初始压力较高（2.0），右侧20个单元格初始压力较低（1.0）。
# 模拟了在压力差驱动下，压力波从高压区间向低压区间传播和震荡的过程。
# 与传统的扩散方程不同，动力学模型考虑了惯性效应，因此压力传播过程中会出现震荡现象，
# 类似于弹性波在介质中的传播。这对于理解非稳态渗流、水击效应等物理现象具有重要意义。
# 通过绘制所有单元格的压力分布和所有面的流量分布，可以直观地观察压力波的传播和演化。

from zmlx import *


def set_cell(c: Seepage.Cell, p):
    """
    设置单元格的孔隙属性和流体体积。

    参数:
        c: Seepage.Cell对象，待设置的单元格
        p: float，初始压力值，用于计算初始流体体积
    """
    c.set_pore(p=1, v=1, dp=1, dv=0.5)  # 设置孔隙参数：参考压力1，参考体积1，压力变化范围1，体积变化量0.5
    c.fluid_number = 1                    # 设置单元格内流体组分的数量为1（单相流体）
    c.get_fluid(0).vol = c.p2v(p)         # 根据初始压力p计算并设置流体的体积


def main():
    """
    主函数：创建一维渗流模型，模拟压力波传播和震荡过程。

    步骤说明:
        1. 创建30个一字排列的单元格，前10个高压，后20个低压
        2. 相邻单元格之间创建连接面，形成一维链式结构
        3. 注册动力学迭代所需的属性键（压力、弹性系数、流量、惯性系数）
        4. 循环迭代2000个时间步，记录并绘制压力分布和流量分布
    """
    model = Seepage()                      # 创建渗流模型实例

    for idx in range(30):                  # 创建30个单元格，构成一维模型
        # 前10个单元格（idx<10）初始压力为2.0，后20个初始压力为1.0，形成左侧高压、右侧低压的初始条件
        set_cell(model.add_cell(), 2.0 if idx < 10 else 1.0)

    for idx in range(1, model.cell_number):  # 在相邻单元格之间创建连接面（形成一维链式结构）
        f = model.add_face(idx - 1, idx)
        f.cond = 0.1                         # 设置面的导流系数为0.1

    ca_p = model.reg_cell_key('p')         # 注册单元格属性键：压力
    fa_k = model.reg_face_key('k')         # 注册面属性键：弹性系数（动力学模式）
    fa_q = model.reg_face_key('q')         # 注册面属性键：流量
    fa_s = model.reg_face_key('s')         # 注册面属性键：惯性系数

    for f in model.faces:                  # 遍历所有面，初始化动力学参数
        f.set_attr(fa_k, 1)                # 设置面的弹性系数为1
        f.set_attr(fa_q, 0)                # 初始化面的流量为0
        f.set_attr(fa_s, 1)                # 设置面的惯性系数为1

    def add_curves(fig):
        """
        绘图回调函数：在指定图形中绘制压力分布和流量分布的曲线。

        参数:
            fig: matplotlib的Figure对象，用于创建子图
        """
        # 子图1：绘制所有单元格的压力分布（横坐标为单元格索引，纵坐标为压力值）
        add_axes2(fig, add_curve2, list(range(model.cell_number)), as_numpy(model).cells.pre, nrows=2, ncols=1,
                  index=1, xlabel='x', ylabel='pressure', title='pressure')
        # 子图2：绘制所有面的流量分布（横坐标为面索引，纵坐标为流量值）
        add_axes2(fig, add_curve2, list(range(model.face_number)), as_numpy(model).faces.get_attr(fa_q), nrows=2,
                  ncols=1, index=2, xlabel='x', ylabel='flow rate', title='flow rate')

    for step in range(2000):               # 主循环：迭代2000个时间步（一维模型需要更多步数以观察波传播）
        gui.break_point()                  # GUI断点检查，允许用户在图形界面中中断计算
        r = model.iterate(dt=0.1, fa_s=fa_s, fa_q=fa_q, fa_k=fa_k, ca_p=ca_p)  # 执行一个时间步的动力学迭代
        if step % 10 == 0:                 # 每10步更新一次可视化图形
            plot(add_curves, caption='当前状态', tight_layout=True)
        print(f'step = {step}, r = {r}')   # 输出当前迭代步数和残差值


if __name__ == '__main__':
    # 通过GUI执行主函数；--no-gui参数可在无图形界面环境下运行（如远程服务器）
    gui.execute(main, close_after_done=False)
