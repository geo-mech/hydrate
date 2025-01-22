# ** desc = '竖直方向二维的水合物开发过程 (用于设置不同的相渗。未完成 for bianhang)'


from zml import Interp1, Seepage, Tensor3
from zmlx.config import seepage, hydrate, step_iteration
from zmlx.seepage_mesh.add_cell_face import add_cell_face
from zmlx.seepage_mesh.hydrate import create_xz

krw01 = """1	1
0.948115	0.6634376
0.898034	0.4459535
0.848014	0.3315954
0.797899	0.1862604
0.743246	0.1262724
0.69316	0.08364846
0.643143	0.03521198
0.593114	0.01394593
0.543001	0.007142146
0.492961	0.001797932
0.442953	0.000806228
0.392949	2.55E-04
0.342888	1.19E-04
0.29288	5.32E-05
0.242879	2.39E-05
0.192586	8.07E-06
0.142565	1.34E-06
0.118837	1.94E-07
0	0
"""

krg01 = """0	0
0.051885	0
0.101966	0.01252946
0.151986	0.01300567
0.202101	0.01405806
0.256754	0.03530633
0.30684	0.04718272
0.356857	0.1297792
0.406886	0.1614739
0.456999	0.2330844
0.507039	0.2975328
0.557047	0.3786376
0.607051	0.4820467
0.657112	0.5747387
0.70712	0.7071236
0.757121	0.8217595
0.807414	0.9113193
0.857435	0.9721493
0.881163	0.9874771
1	1
"""

krw02 = """1	1
0.948321	0.6593811
0.898134	0.5063068
0.84791	0.2862477
0.796006	0.2386066
0.745889	0.1668577
0.692127	0.08377795
0.636642	0.0602542
0.586642	0.0241721
0.534895	0.007862161
0.484666	0.004816484
0.434342	0.002582099
0.384335	7.64E-04
0.332285	2.20E-04
0.282279	7.81E-05
0.232277	2.89E-05
0.182209	1.08E-05
0.132204	2.54E-06
0.096375	7.27E-08
0	0"""

krg02 = """0	0
0.051679	0
0.101866	0
0.15209	0
0.203994	0.05514999 
0.254111	0.12727080 
0.307873	0.13999820 
0.363358	0.16275290 
0.413358	0.25876200 
0.465105	0.32230320 
0.515334	0.36756480 
0.565658	0.46840960 
0.615665	0.54481460 
0.667715	0.63280700 
0.717721	0.70085550 
0.767723	0.80179390 
0.817791	0.87301090 
0.867796	0.95190040 
0.903625	0.99306470 
1	1
"""


def parse_coordinates(input_str):
    """
    将输入字符串解析为两个列表，分别包含x和y坐标，并将x坐标从小到大排序。

    参数:
    input_str (str): 包含坐标数据的字符串

    返回:
    tuple: 包含两个列表的元组，第一个列表包含排序后的x坐标，第二个列表包含对应的y坐标
    """
    lines = input_str.strip().split('\n')
    coordinates = []

    for line in lines:
        x, y = map(float, line.split())
        coordinates.append((x, y))

    # 根据x坐标对坐标列表进行排序
    coordinates.sort(key=lambda coord: coord[0])

    x_values = [coord[0] for coord in coordinates]
    y_values = [coord[1] for coord in coordinates]

    return x_values, y_values




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
                                       't': [0, 1e20],  # 使用t和p两个list定义一条曲线，来控制“井底流压”
                                       'p': [3e6, 3e6]  # 此处，流体压力固定为3MPa
                                       }]  # 用于接收产出的虚拟的Cell
                               )

    # 根据上述关键词建立模型
    model = seepage.create(**kw)

    # 放入相渗 --------
    x, y = parse_coordinates(krw01)
    model.set_kr(index=11, kr=Interp1(x=x, y=y))

    x, y = parse_coordinates(krw02)
    model.set_kr(index=12, kr=Interp1(x=x, y=y))

    x, y = parse_coordinates(krg01)
    model.set_kr(index=21, kr=Interp1(x=x, y=y))

    x, y = parse_coordinates(krg02)
    model.set_kr(index=22, kr=Interp1(x=x, y=y))

    # 设置初始值，初始选择
    update_ikr(model)

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
                                        'mask': seepage.get_cell_mask(model=model, yr=[-1, 1])},
                         # 求解的时间长度 (此处求解3年)
                         'time_max': 3 * 365 * 24 * 3600,
                         }
                   )
    # 返回模型 (所有的细节，但是并不包括update_ikr函数的定义)
    return model


def get_sh(face):
    c0, c1 = face.get_cell(0), face.get_cell(1)
    assert isinstance(c0, Seepage.Cell)
    assert isinstance(c1, Seepage.Cell)
    return (c0.get_fluid_vol_fraction(2) + c1.get_fluid_vol_fraction(2)) / 2


def get_ikr_w(sh):
    return 11


def get_ikr_g(sh):
    return 21


def update_ikr(model: Seepage):
    for face in model.faces:
        assert isinstance(face, Seepage.Face)
        sh = get_sh(face)
        face.set_ikr(index=0, value=get_ikr_g(sh))
        face.set_ikr(index=1, value=get_ikr_w(sh))


def main():
    """
    主函数
    """
    model = create()
    seepage.solve(model, close_after_done=True,
                  slots={'update_ikr': update_ikr}  # 将update_ikr通过参数传递给solve函数，从而可以在求解的过程中被调用
                  )


if __name__ == '__main__':
    main()
