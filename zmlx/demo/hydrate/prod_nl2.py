# ** desc = '竖直方向二维的水合物开发过程 (流体非线性)'
"""
实现流动非线性的思路：
    在模型中存储大小不同的相对渗透率曲线，并且根据各个Face位置压力梯度的大小来选择不同的相对渗透率曲线，从而
    模拟不同的流动阻力.
"""

from zmlx import *
from zmlx.seepage_mesh.hydrate import create_xz


def create():
    """
    创建模型
    """
    # 创建一个位于xz平面内，且沿着y轴方向的厚度为1的二维网格
    mesh = create_xz(x_max=50,  # x的最大值(x的最小值为0)
                     z_min=-100, z_max=0,  # z坐标的范围
                     dx=1, dz=1,  # 网格的大小
                     upper=30,  # 上覆层的厚度
                     lower=30  # 下伏层的厚度
                     )

    # 添加虚拟的cell和face用于生产
    add_cell_face(mesh,
                  pos=[0, 0, -50],  # 在此处找到一个Cell与虚拟的Cell相连
                  offset=[0, 10, 0],  # 在pos的基础上，加上此向量，得到虚拟的Cell的位置
                  vol=1000,  # 虚拟的Cell的体积
                  area=5,  # 虚拟Face的面积
                  length=1  # 虚拟Face的长度 （流体流经此Face的时候流过的距离）
                  )

    # 找到上下范围，用以在后续定位顶底的Cell
    z_min, z_max = mesh.get_pos_range(2)

    def is_upper(x, y, z):
        """
        判断点是否位于模型的上边界
        参数：
            x：点的x坐标
            y：点的y坐标
            z：点的z坐标
        返回值：
            如果点位于上边界，则返回True；否则返回False
        """
        return abs(z - z_max) < 0.01

    def is_lower(x, y, z):
        """
        判断点是否位于模型的下边界
        参数：
            x：点的x坐标
            y：点的y坐标
            z：点的z坐标
        返回值：
            如果点位于下边界，则返回True；否则返回False
        """
        return abs(z - z_min) < 0.01

    def is_prod(x, y, z):
        """
        判断点是否是用于接收产出流体的虚拟的Cell
        参数：
            x：点的x坐标
            y：点的y坐标
            z：点的z坐标
        返回值：
            如果是用于接收产出流体的虚拟的Cell，则返回True；否则返回False
        """
        return abs(y - 10) < 0.1

    def get_s(x, y, z):
        """
        获取某一点的初始的饱和度

        参数：
            x：点的x坐标
            y：点的y坐标
            z：点的z坐标
        """
        if is_prod(x, y, z) or z > -30 or z < -70:
            return {'h2o': 1}
        else:
            return {'h2o': 0.6, 'ch4_hydrate': 0.4}

    def get_k(x, y, z):
        """
        获取某一点的渗透率张量 (注意：根据需要，可以设置为各向异性的)

        参数：
            x：点的x坐标
            y：点的y坐标
            z：点的z坐标
        """
        if z > -30 or z < -70:
            return Tensor3(xx=1.0e-15, yy=1.0e-15, zz=1.0e-15)
        else:
            return Tensor3(xx=1.0e-14, yy=1.0e-14, zz=1.0e-14)

    def get_p(x, y, z):
        """
        获取某一点的初始流体压力 （静水压力） [Pa]

        参数：
            x：点的x坐标
            y：点的y坐标
            z：点的z坐标
        """
        return 10e6 - z * 1e4

    def get_t(x, y, z):
        """
        获取某一点的初始温度 [K]

        参数：
            x：点的x坐标
            y：点的y坐标
            z：点的z坐标
        """
        return 285 - z * 0.04

    def denc(*pos):
        """
        获取某一点的密度和比热的乘积。此值越大，则温度约难以发生改变.

        参数：
            pos：点的位置坐标
        返回值：
            如果点位于模型的上边界或下边界，则返回1e20；
            否则，返回5e6。
        """
        return 1e20 if is_upper(*pos) or is_lower(*pos) else 5e6

    def get_fai(x, y, z):
        """
        获取某一点的孔隙度

        参数：
            x：点的x坐标
            y：点的y坐标
            z：点的z坐标
        返回值：
            如果点位于模型的上边界，则返回1.0e10 (用以固定流体压力)；
            否则，返回0.3。
        """
        if is_upper(x, y, z):  # 顶部固定压力
            return 1.0e10
        else:
            return 0.3

    def heat_cond(x, y, z):  # 确保不会有热量通过用于生产的虚拟的cell传递过来.
        """
        获取某一点的热导率 (确保热量不会从用于生产的虚拟的cell传递过来)

        参数：
            x：点的x坐标
            y：点的y坐标
            z：点的z坐标
        """
        return 1.0 if abs(y) < 2 else 0.0

    # 创建后续建立计算模型的关键词
    kw = hydrate.create_kwargs(gravity=[0, 0, -10],  # 重力
                               dt_min=1,  # 最小时间步长
                               dt_max=24 * 3600,  # 最大时间步长
                               dv_relative=0.1,  # 每个dt内，流体流过的网格数(用以控制dt)
                               mesh=mesh,
                               porosity=get_fai,  # 孔隙度
                               pore_modulus=100e6,  # 孔隙刚度
                               denc=denc,  # 密度和比热的乘积
                               temperature=get_t,  # 温度
                               p=get_p,  # 初始的流体压力
                               s=get_s,  # 初始的饱和度
                               perm=get_k,  # 渗透率
                               heat_cond=heat_cond,  # 热导率
                               prods=[{'index': mesh.cell_number - 1,
                                       't': [0, 1e20],
                                       # 使用t和p两个list定义一条曲线，来控制“井底流压”
                                       'p': [3e6, 3e6]  # 此处，流体压力固定为3MPa
                                       }]  # 用于接收产出的虚拟的Cell
                               )

    # 根据上述关键词建立模型
    model = seepage.create(**kw)

    # 从index = 10开始，逐步添加90个kr，每一个缩减1%，这样，在后续可以在各个face的位置，根据
    # 阻力的大小，选择合适的kr
    for idx in range(90):
        # kr缩减的比例
        ratio = 1.0 - 0.01 * idx
        x, y = model.get_kr(index=1).get_data()
        assert isinstance(x, Vector) and isinstance(y, Vector)
        for i in range(len(y)):
            y[i] = y[i] * ratio
        model.set_kr(index=idx + 10, kr=Interp1(x=x, y=y))

    # 在各个face位置，对于水，初始先择第10个kr，即缩减的比例为0
    for face in model.faces:
        assert isinstance(face, Seepage.Face)
        face.set_ikr(index=1, value=10)

    # 告诉模型，在后续solve的过程中，需要每隔5步来调用一次update_ikr函数
    step_iteration.add_setting(model,
                               step=5,
                               name='update_ikr',
                               args=['@model'])

    # 用于solve的选项
    model.set_text(key='solve',
                   text={'monitor': {'cell_ids': [model.cell_number - 1]},
                         # 在计算的过程中，如何绘图. 这里给出的，是zmlx.seepage.show_cells函数所需要的参数
                         'show_cells': {'dim0': 0,
                                        'dim1': 2,
                                        'mask': seepage.get_cell_mask(
                                            model=model, yr=[-1, 1])},
                         # 求解的时间长度 (此处求解3年)
                         'time_max': 3 * 365 * 24 * 3600,
                         }
                   )
    # 返回模型 (所有的细节，但是并不包括update_ikr函数的定义)
    return model


def get_ikr(ratio):
    """
    给定需要矫正的比例，返回所需要选择的kr的index
    """
    return clamp(round((1.0 - ratio) / 0.01 + 10), 10, 99)


def get_ratio(grad):
    """
    给定梯度，返回需要修正的比例. 此函数应该返回0到1之间的一个数值.
    这里所谓的比例，就是考虑上非线性效应之后，与原本线性的流体相比，流动的速率会折减的比例.
    """
    return clamp(grad / 2e5, 0, 1)


def update_ikr(model: Seepage):
    """
    根据各个face两侧的压力差，更新对于face需要选择的kr
    """
    for face in model.faces:
        c0, c1 = face.get_cell(0), face.get_cell(1)
        p0, p1 = c0.pre, c1.pre
        z0, z1 = c0.z, c1.z
        dist = point_distance(c0.pos, c1.pos)
        grad = abs(p0 + 10 * z0 - p1 - 10 * z1) / dist
        # 下面，根据梯度，计算需要修正的比例
        ratio = get_ratio(grad)
        i0 = face.get_ikr(index=1)
        i1 = get_ikr(ratio)
        # 下面，我们不直接赋值(而是去缓慢地调整)，主要是不希望数据发生过于剧烈的变化
        if i1 > i0:
            face.set_ikr(index=1, value=clamp(i0 + 1, 10, 99))
            continue
        if i1 < i0:
            face.set_ikr(index=1, value=clamp(i0 - 1, 10, 99))
            continue


def main():
    """
    主函数
    """
    model = create()
    seepage.solve(model, close_after_done=True,
                  slots={'update_ikr': update_ikr}
                  # 将update_ikr通过参数传递给solve函数，从而可以在求解的过程中被调用
                  )


if __name__ == '__main__':
    main()
