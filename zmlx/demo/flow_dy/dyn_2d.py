# ** desc = '二维的模型，初始左下角位置的压力比较高，模拟这个压力波扩散-震荡的过程'
#
# 本案例构建了一个二维（2D）渗流动力学模型：
# 在单位正方形区域（[0,1]x[0,1]）内创建50x50的均匀网格，中心偏左下位置（0.4,0.4）附近
# 半径为0.2的圆形区域内初始压力较高（2.0），其余区域初始压力较低（1.0）。
# 模拟了高压区向低压区的压力波扩散和震荡过程。
# 与一维模型相比，二维模型能够展示压力波在空间中的各向同性传播，
# 呈现出以高压区为中心的环状波前扩散特征。
# 通过等值线图实时展示压力场的空间分布，可以直观地观察压力波的传播、反射和震荡。

from zmlx import *


def set_cell(c: Seepage.Cell, p):
    """
    设置单元格的孔隙属性和流体体积。

    参数:
        c: Seepage.Cell对象，待设置的单元格
        p: float，初始压力值，用于计算初始流体体积
    返回:
        Seepage.Cell对象，方便链式调用
    """
    c.set_pore(p=1, v=1, dp=1, dv=0.5)  # 设置孔隙参数：参考压力1，参考体积1，压力变化范围1，体积变化量0.5
    c.fluid_number = 1                    # 设置单元格内流体组分的数量为1（单相流体）
    c.get_fluid(0).vol = c.p2v(p)         # 根据初始压力p计算并设置流体的体积
    return c                               # 返回单元格对象，便于链式调用


def main(jx, jy):
    """
    主函数：创建二维渗流模型，模拟压力波扩散和震荡过程。

    参数:
        jx: int，x方向的网格数量（决定了空间分辨率）
        jy: int，y方向的网格数量
    """
    model = Seepage()                      # 创建渗流模型实例
    # 创建矩形网格：x和y方向从0到1均匀划分，z方向很薄（[-0.5, 0.5]），实际为二维问题
    mesh = create_cube(
        x=linspace(0, 1, jx + 1), y=linspace(0, 1, jy + 1), z=(-0.5, 0.5)
    )
    for c in mesh.cells:                   # 遍历网格中的所有单元格
        x, y, z = c.pos                    # 获取单元格的中心坐标
        cell = model.add_cell()            # 在渗流模型中添加一个新的单元格
        # 在点(0.4,0.4)附近半径0.2的圆形区域内设高压（2.0），其余区域设低压（1.0）
        set_cell(cell, 2 if point_distance([x, y], [0.4, 0.4]) < 0.2 else 1)
        cell.pos = [x, y, z]               # 设置单元格的位置坐标

    for f in mesh.faces:                   # 遍历网格中的所有面（连接关系）
        model.add_face(f.cell_i0, f.cell_i1).cond = 0.1  # 在渗流模型中添加连接面，设置导流系数为0.1

    ca_p = model.reg_cell_key('p')         # 注册单元格属性键：压力
    fa_k = model.reg_face_key('k')         # 注册面属性键：弹性系数（动力学模式）
    fa_q = model.reg_face_key('q')         # 注册面属性键：流量
    fa_s = model.reg_face_key('s')         # 注册面属性键：惯性系数

    for f in model.faces:                  # 遍历所有面，初始化动力学参数
        f.set_attr(fa_k, 1)                # 设置面的弹性系数为1
        f.set_attr(fa_q, 0)                # 初始化面的流量为0
        f.set_attr(fa_s, 1)                # 设置面的惯性系数为1

    # 获取网格节点的x坐标矩阵和y坐标矩阵（用于绘图时的坐标映射）
    x = tfc.get_x(model, shape=[jx, jy])
    y = tfc.get_y(model, shape=[jx, jy])

    for step in range(200):                # 主循环：迭代200个时间步
        r = model.iterate(dt=0.1, fa_s=fa_s, fa_q=fa_q, fa_k=fa_k, ca_p=ca_p)  # 执行一个时间步的动力学迭代
        print(f'step = {step}, r = {r}')   # 输出当前迭代步数和残差值
        gui.break_point()                  # GUI断点检查
        if step % 5 == 0:                  # 每5步更新一次可视化图形
            # 绘制压力场的填充等值线图，展示压力波在二维空间中的扩散情况
            plot(add_axes2, add_contourf, x, y, tfc.get_p(model, shape=[jx, jy]), xlabel='x', ylabel='y',
                 cbar=dict(label='Pressure', shrink=0.8), aspect='equal', tight_layout=True, caption='流体压力'
                 )


if __name__ == '__main__':
    # 通过GUI执行主函数，传入参数[50, 50]表示采用50x50的网格
    gui.execute(main, close_after_done=False, args=[50, 50])
