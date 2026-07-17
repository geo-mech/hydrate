# ** desc = '流体在毛管力驱动下的流动(渗吸的过程)'
#
# 物理问题描述：
#   本模型模拟二维平面区域中，在毛管压力（毛细管力）驱动下的气-水两相渗吸过程。
#   模型区域为 100m x 100m 的正方形，中心有一个半径为20m的圆形泥岩区，
#   四周被四种不同类型的砂岩（sand_J, sand_K, sand_P, sand_T）包围。
#   初始时刻，中心区域含气饱和（Gas=1），外围区域含水饱和（Water=1）。
#   在毛管压力梯度驱动下，气体逐渐向四周扩散（即渗吸过程），
#   五种岩石具有不同的毛管压力曲线，展示了岩性对渗吸行为的影响。
#
# 建模技术要点：
#   1. 使用 create_cube 生成二维平面网格（100x100）
#   2. 通过 get_idx 函数为每个单元分配毛管压力曲线ID（根据空间位置）
#   3. 使用 capillary.add_setting 为每种岩石类型设置毛管压力曲线
#   4. 通过 capillary.iterate 单独进行毛管平衡迭代（不包含渗流计算）
#   5. 毛管压力数据格式：第一列为Gas饱和度，第二列为Gas压力-Water压力（即毛管压力Pc）

from zmlx import *

# 毛管压力曲线数据
# 第一列，Gas的饱和度  第二列, Gas压力-Water压力 (即毛管压力Pc，单位Pa)
mud = """0.007698294	1930020.672
0.0441305	4270730.329
0.087590542	14003815.37
0.131146363	23172141.89
0.186770428	38537645.32
0.236863215	65745613.48
0.4	97799554.5"""

# 砂岩J的毛管压力曲线数据（J型砂岩，细粒）
# 第一列，Gas的饱和度  第二列, Gas压力-Water压力 (单位Pa)
sand_J = """0	757.5757576
0.011	1167.929293
0.0339	1849.747475
0.0806	2891.414141
0.2015	4595.959596
0.2934	7304.292929
0.3564	11691.91919
0.4365	18636.36364
0.5081	29008.83838
0.5789	46193.18182
0.6408	73257.57576
0.6923	117146.4646
0.7346	186887.6263
0.7477	290119.9495
0.7514	460871.2121
0.7541	732171.7172
0.7576	1154223.485
0.7634	1846483.586
0.7724	2888648.99
0.7867	4626369.949
0.8086	7346635.101
0.8561	12562297.98"""

# 砂岩K的毛管压力曲线数据（K型砂岩，中等粒度）
# 第一列，Gas的饱和度  第二列, Gas压力-Water压力 (单位Pa)
sand_K = """0	1167.929293
0.0088	1849.747475
0.0533	2891.414141
0.2083	4595.959596
0.4296	7304.292929
0.5022	11616.16162
0.5762	18503.78788
0.6374	28857.32323
0.7001	46407.82828
0.7584	73522.72727
0.8099	116420.4545
0.8134	186628.7879
0.814	292859.8485
0.8143	459627.5253
0.8165	732253.7879
0.8183	1155707.071
0.8217	1846590.909
0.8273	2887904.04
0.8364	4623099.747
0.8504	7345050.505
0.8774	12570795.45"""

# 砂岩P的毛管压力曲线数据（P型砂岩，粗粒）
# 第一列，Gas的饱和度  第二列, Gas压力-Water压力 (单位Pa)
sand_P = """0	130170.4545
0.3064	315587.1212
0.4867	508428.0303
0.5329	638825.7576
0.5637	744002.5253
0.5945	929103.5354
0.6363	1241477.273
0.6913	1880555.556"""

# 砂岩T的毛管压力曲线数据（T型砂岩，过渡带）
# 第一列，Gas的饱和度  第二列, Gas压力-Water压力 (单位Pa)
sand_T = """0	10580.80808
0.0001	12689.39394
0.0003	18945.70707
0.0043	32752.52525
0.0063	65959.59596
0.0173	93686.86869
0.0586	127279.0404
0.2346	329785.3535
0.3088	504513.8889
0.3418	626376.2626
0.3721	758901.5152
0.4051	953219.697
0.4463	1248484.848
0.5068	1895265.152"""


def get_idx(x, y, z):
    """
    定义在不同区域所使用的毛管压力曲线的ID（从0开始编号）。
    根据单元中心坐标(x, y, z)判断其所属的岩石类型区域：
        - 中心半径20m以内：泥岩（ID=0），毛管压力最高
        - 第二象限 (x<0, y>0)：sand_K（ID=2）
        - 第三象限 (x<0, y<0)：sand_J（ID=1）
        - 第四象限 (x>0, y<0)：sand_P（ID=3）
        - 第一象限 (x>0, y>0)：sand_T（ID=4）

    Args:
        x: 单元中心的x坐标 (m)
        y: 单元中心的y坐标 (m)
        z: 单元中心的z坐标 (m)

    Returns:
        毛管压力曲线ID（0~4的整数）
    """
    if point_distance((x, y, z), (0, 0, 0)) < 20:
        return 0  # 中心圆形泥岩区
    if x < 0:
        if y < 0:
            return 1  # 左下：sand_J区域
        else:
            return 2  # 左上：sand_K区域
    else:
        if y < 0:
            return 3  # 右下：sand_P区域
        else:
            return 4  # 右上：sand_T区域


def get_s(x, y, z):
    """
    返回初始时刻的饱和度分布。
    在中间（中心偏右10m处）有一块半径为20m的圆形区域，初始为气体饱和（Gas=1）；
    其余区域初始为水饱和（Water=1）。
    这种初始条件模拟了气体在泥岩中聚集，然后向四周砂岩渗吸扩散的物理过程。

    Args:
        x: 单元中心的x坐标 (m)
        y: 单元中心的y坐标 (m)
        z: 单元中心的z坐标 (m)

    Returns:
        dict: 包含初始饱和度的字典，如 {'gas': 1} 或 {'water': 1}
    """
    if point_distance((x, y, z), (10, 0, 0)) < 20:
        return {'gas': 1}
    else:
        return {'water': 1}


def create(jx, jy):
    """
    创建并返回给定网格精度的渗流模型。
    使用二维平面网格（范围：x方向 -50~50m，y方向 -50~50m），包含五种岩石类型。

    Args:
        jx: x方向上的网格单元数量
        jy: y方向上的网格单元数量

    Returns:
        Seepage: 渗流模型对象，包含网格、流体定义、毛管压力设置等
    """
    # 定义两种流体：gas（轻质，密度50 kg/m3，粘度1e-4 Pa·s）和 water（密度1000 kg/m3，粘度1e-3 Pa·s）
    fludefs = [FluDef(den=50, vis=1.0e-4, name='gas'),
               FluDef(den=1000, vis=1.0e-3, name='water')
               ]

    # 生成二维平面网格，z方向厚度为1m（-0.5~0.5）
    mesh = create_cube(
        linspace(-50, 50, jx + 1),
        linspace(-50, 50, jy + 1),
        (-0.5, 0.5))

    # 创建渗流模型：孔隙度0.2，孔隙模量100MPa，初始压力1MPa，温度280K，渗透率1e-14 m2
    model = tfc.create(
        mesh=mesh, porosity=0.2, pore_modulus=100e6,
        p=1e6, temperature=280, perm=1e-14, s=get_s, fludefs=fludefs
    )

    # 设置相对渗透率为线性关系（饱和度从0~1对应kr从0~1）
    model.set_kr(saturation=[0, 1], kr=[0, 1])

    # 添加毛管压力设置：为每种岩石类型（mud/sand_J/sand_K/sand_P/sand_T）指定毛管压力曲线
    capillary.add_setting(
        model, fid0='gas', fid1='water', get_idx=get_idx,
        data=[mud, sand_J, sand_K, sand_P, sand_T]
    )
    return model


def show(x, y, z, jx, jy, caption=None, cmap=None, label=None, title=None):
    """
    在图形界面中显示模型的状态（使用plot2d绘制）。
    显示内容包括：云图（contourf）、岩石分区边界、区域标签等。

    Args:
        x: x坐标数组 (已展平)
        y: y坐标数组 (已展平)
        z: 待显示的物理量数组 (已展平)
        jx: x方向网格数量
        jy: y方向网格数量
        caption: 窗口标题
        cmap: 颜色映射方案
        label: 颜色条标签
        title: 子图标题
    """
    if not gui:
        return
    angles = np.linspace(0, 2 * np.pi, 100)
    items = [
        item('contourf', np.reshape(x, [jx, jy]),
             np.reshape(y, [jx, jy]),
             np.reshape(z, [jx, jy]),
             cmap=cmap, cbar=dict(label=label)
             ),
        # 绘制中心泥岩区的圆形边界（半径20m）
        item('xy', 20 * np.cos(angles), 20 * np.sin(angles), 'r--'),
        # 绘制四个象限的分隔线（将外围分为四个砂岩区域）
        item('xy', [0, 0], [20, 50], 'r--'),
        item('xy', [0, 0], [-20, -50], 'r--'),
        item('xy', [20, 50], [0, 0], 'r--'),
        item('xy', [-20, -50], [0, 0], 'r--'),
        # 标注各区域岩石类型
        item('text', 0, 0, 'mud'),
        item('text', -30, -30, 'sand_J'),
        item('text', -30, 30, 'sand_K'),
        item('text', 30, -30, 'sand_P'),
        item('text', 30, 30, 'sand_T'),
    ]
    plot2d(*items, aspect='equal',
           xlabel='x', ylabel='y', caption=caption, tight_layout=True, title=title
           )


def solve(model: Seepage, jx, jy):
    """
    求解给定的模型。这里仅演示毛管压力平衡过程（capillary.iterate），不包含渗流计算。
    若需要完整的渗流+化学耦合计算，应调用 seepage.iterate 或 tfc.solve。

    Args:
        model: 渗流模型对象
        jx: x方向网格单元数量
        jy: y方向网格单元数量
    """
    x = tfc.get_x(model)  # 获取所有单元中心的x坐标
    y = tfc.get_y(model)  # 获取所有单元中心的y坐标
    z = tfc.get_z(model)  # 获取所有单元中心的z坐标

    # 显示各单元的岩石类型ID分布
    show(x, y, [get_idx(x[i], y[i], z[i]) for i in range(len(x))],
         jx, jy, caption='岩石ID', cmap='jet')

    v = tfc.get_v(model)  # 获取总孔隙体积

    def show_s(caption, title=None):
        """
        显示Gas饱和度云图的内嵌函数。
        """
        show(x, y, tfc.get_v(model, 0) / v, jx, jy,
             caption=caption, cmap='coolwarm',
             label='饱和度(Gas)', title=title
             )

    show_s('初始饱和度', title='饱和度(红色为Gas)')

    # 进行500步毛管压力平衡迭代，每一步时间步长1e5秒
    for step in range(500):
        gui.break_point()  # GUI断点，允许用户暂停/继续
        capillary.iterate(model, dt=1e5)  # 执行一步毛管压力平衡迭代
        if step % 20 == 0:
            print(f'step = {step}')
            show_s('实时饱和度', title=f'饱和度(红色为Gas), step = {step}')


def main():
    """
    主函数：创建模型并启动求解（使用GUI方式）。
    网格精度为100x100，关闭--no-gui参数可跳过GUI显示。
    """
    jx, jy = 100, 100
    model = create(jx, jy)
    gui.execute(solve, args=(model, jx, jy), close_after_done=False)


if __name__ == '__main__':
    main()
