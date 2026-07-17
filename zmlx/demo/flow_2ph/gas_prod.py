# ** desc = '天然气藏的降压开发过程模拟'
#
# 物理问题描述：
#   本模型模拟天然气藏通过降压开采（生产井）的开发过程。
#   模型为二维垂直剖面，区域范围：水平方向-50~50m（起伏地形），
#   垂直方向-15~15m（含地形起伏）。
#   初始时，上半部分（z>0）为纯气饱和，下半部分（z<0）为纯水饱和，
#   模拟气藏的气-水两相分布特征。
#   模型在构造高部位设置一口生产井，井底压力为3MPa（低于气藏初始压力10MPa），
#   通过压差驱动气体向井筒流动。模拟1年的开采过程。
#
# 建模技术要点：
#   1. 使用 create_cube 生成网格后，通过余弦函数对z坐标施加地形起伏
#      （模拟背斜构造），使气体聚集于构造高部位
#   2. 生产井设置在构造最高部位（中心附近）
#   3. 使用 NearestNDInterpolator 建立各向异性渗透率场：
#      - 水平方向（x方向）渗透率：1e-14 m2
#      - 垂直方向（z方向）渗透率：1e-15 m2（低一个数量级，模拟层理效应）
#   4. 生产井区域采用大孔隙度（1e6）和低压（3MPa）实现定压生产边界
#   5. 左右边界（|x|>49）设为大孔隙度，模拟定压补给边界
#   6. 设置 dt_min=1s 和 cfl=0.1 控制时间步长自适应调整

import math

from scipy.interpolate import NearestNDInterpolator

from zmlx import *


def create(jx, jz):
    """
    创建天然气藏降压开采模型。

    Args:
        jx: 水平方向（x）的网格单元数量
        jz: 垂直方向（z）的网格单元数量

    Returns:
        model: 渗流模型对象，包含地形起伏、各向异性渗透率、生产井等
    """
    assert np is not None, "numpy is not installed"
    # 生成初始矩形网格：水平-50~50m，垂直-15~15m
    mesh = create_cube(
        x=np.linspace(-50, 50, jx + 1),
        y=[-0.5, 0.5],
        z=np.linspace(-15, 15, jz + 1)
    )

    # 计算每个面的渗透率（各向异性）：
    # 水平面（x方向变化）渗透率为1e-14 m2
    # 垂直面（z方向变化）渗透率为1e-15 m2（低一个数量级，模拟层理效应）
    perms = []
    for face in mesh.faces:
        assert isinstance(face, SeepageMesh.Face)
        x0, y0, z0 = face.get_cell(0).pos
        x1, y1, z1 = face.get_cell(1).pos
        if abs(x0 - x1) < 1.0e-3:
            # 面法线方向为x方向（即垂直渗透率）
            perms.append(1.0e-15)
        else:
            # 面法线方向为z方向（即水平渗透率）
            perms.append(1.0e-14)

    # 对网格施加地形起伏：z方向按余弦函数变化，模拟背斜构造
    for cell in mesh.cells:
        assert isinstance(cell, SeepageMesh.Cell)
        x, y, z = cell.pos
        dz = math.cos(x * math.pi / 50) * 15  # 余弦函数产生起伏地形
        cell.pos = [x, y, z + dz]

    # 使用最近邻插值建立渗透率函数
    points = np.array([face.pos for face in mesh.faces])
    interp = NearestNDInterpolator(points, perms)

    def get_perm(*pos):
        """返回给定位置的各向异性渗透率（通过插值）。"""
        return interp(pos)

    # 在构造高部位（中心附近）设置生产井
    center = mesh.get_nearest_cell(pos=[0, 0, 20]).pos

    def is_prod(*pos):
        """判断给定位置是否为生产井区域（距井中心<0.1m）。"""
        return point_distance(pos, center) < 0.1

    def porosity(*pos):
        """
        定义孔隙度分布：
        生产井区域和左右边界（|x|>49）设为1e6（大孔隙度作为定压边界），
        其他区域为0.3。
        """
        return 1e6 if is_prod(*pos) or abs(pos[0]) > 49 else 0.3

    def pressure(*pos):
        """
        定义初始压力分布：
        生产井区域为3MPa（低于地层压力，形成压降漏斗），
        其他区域为10MPa（原始地层压力）。
        """
        return 3e6 if is_prod(*pos) else 10e6

    # 定义流体：gas（使用NIST物性的CH4）和 water（定密度1000 kg/m3）
    gas = create_ch4(name='gas')
    wat = FluDef(den=1000.0, vis=1.0e-3, specific_heat=4200, name='wat')

    fludefs = [gas, wat]

    def get_s(*pos):
        """定义初始饱和度：上半部（z>0）为纯气，下半部（z<0）为纯水。"""
        if pos[2] > 0:
            return {'gas': 1}
        else:
            return {'wat': 1}

    # 创建渗流模型
    model = tfc.create(
        mesh=mesh,
        fludefs=fludefs,
        porosity=porosity,
        pore_modulus=100e6,
        denc=5e6,
        temperature=285.0,
        p=pressure,
        s=get_s,
        perm=get_perm,
        dt_min=1, dt_max=24 * 3600 * 5, cfl=0.1,  # 时间步长自适应控制
    )
    return model


def show(model: Seepage, jx, jz, folder=None):
    """
    在界面上显示模型状态，包括压力云图和水饱和度云图。

    Args:
        model: 渗流模型对象
        jx: 水平方向网格单元数量
        jz: 垂直方向网格单元数量
        folder: 保存图片的文件夹路径（若不为None，则保存图片）
    """
    def on_figure(figure):
        figure.suptitle(f'Model when time = {tfc.get_time(model, as_str=True)}')
        layout = AutoFigLayout(figure, 2, 1.3, xlabel='x/m', ylabel='z/m', aspect='equal')
        shape = [jx, jz]
        x = tfc.get_x(model, shape=shape)
        y = tfc.get_z(model, shape=shape)
        p = tfc.get_p(model, shape=shape) / 1e6  # 压力转换为MPa显示
        v = tfc.get_v(model, shape=shape)
        s = tfc.get_v(model, shape=shape, fid=1) / v  # 水饱和度
        args = [add_contourf, x, y]
        layout.add_axes2(*args, p, title='压力 (MPa)', cbar=dict(label='Pressure', shrink=0.5))
        layout.add_axes2(*args, s, title='水饱和度', cbar=dict(label='Saturation', shrink=0.5))

    fname = make_fname(time=tfc.get_time(model) / (3600 * 24), folder=folder, ext='jpg', unit='d')
    plot(on_figure, caption=f'Seepage({model.handle_str})', clear=True, fname=fname, tight_layout=True)


def main(folder=None):
    """
    主函数：创建100x30网格的气藏模型，求解1年的降压开采过程。

    Args:
        folder: 输出文件夹路径（若不为None，则保存过程图片）
    """
    fig_folder = os.path.join(folder, 'all_figures') if folder is not None else None
    jx, jz = 100, 30
    model = create(jx, jz)
    tfc.solve(
        model,
        folder=folder,
        time_unit='d',
        extra_plot=lambda: show(model, jx, jz, fig_folder),
        time_forward=3600 * 24 * 365  # 模拟1年
    )


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
