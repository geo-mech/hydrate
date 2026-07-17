# ** desc = '油水两相的产油产水过程模拟。模拟的是垂直于水平井的一个剖面。'
#
# 物理问题描述：
#   本模型模拟垂直于水平井剖面的油-水两相渗流及产油产水过程。
#   模型为二维垂直剖面，水平方向0~20m，垂直方向-5~5m。
#   左侧（x=0, y=0处）设置水平井，通过人工添加的大体积单元
#   模拟井筒，井底压力为2MPa（低于油藏压力12MPa），形成生产压差。
#   初始时，模型内部油饱和度0.6、水饱和度0.4。
#   右侧（x=20m）设为定压边界。
#   模型同时考虑：
#     - 温度场非均匀分布（近井加热区150度+高温蒸汽驱）
#     - 各向异性渗透率（水平2e-14 m2，垂直2e-15 m2）
#     - 重力作用（gravity=-9.81 m/s2）
#     - 原油粘度随温度的动态变化（从oil_data.txt读取物性数据）
#
# 建模技术要点：
#   1. 使用 create_cube 生成网格后，通过 add_cell 和 add_face 添加井筒单元
#   2. 原油物性（密度、粘度随温压变化）从外部文件 oil_data.txt 读取
#   3. 温度场：近井区150度+高温（模拟注热或地热），远井区60度
#   4. 各向异性渗透率：水平方向2e-14，垂直方向2e-15（各向异性比10:1）
#   5. 上下边界设置高 denc 模拟封闭条件
#   6. 使用 mask 过滤掉井筒区域（y>5）再显示结果

from zmlx import *


def create_oil(t_min=274, t_max=423, p_min=2.0e6, p_max=99.0e6, name=None):
    """
    从数据文件创建原油的物性定义（密度、粘度随温度和压力变化）。

    Args:
        t_min: 最低温度 (K)，默认274K (1度)
        t_max: 最高温度 (K)，默认423K (150度)
        p_min: 最低压力 (Pa)，默认2.0MPa
        p_max: 最高压力 (Pa)，默认99.0MPa
        name: 流体名称

    Returns:
        FluDef: 原油物性定义对象
    """
    return from_file(
        fname=join_paths(os.path.dirname(__file__), 'oil_data.txt'),
        t_min=t_min, t_max=t_max, p_min=p_min, p_max=p_max,
        name=name, specific_heat=2000)


def create(jx=40, jz=20, s=None):
    """
    创建油-水两相水平井开采模型。

    Args:
        jx: 水平方向（x）的网格单元数量，默认40
        jz: 垂直方向（z）的网格单元数量，默认20
        s: 初始饱和度，默认为 (oil=0.6, water=0.4)

    Returns:
        model: 渗流模型对象
    """
    if s is None:
        s = (0.6, 0.4)

    # 生成二维垂直剖面网格：水平0~20m，垂直-5~5m
    mesh = create_cube(
        x=linspace(0, 20, jx + 1),
        y=[-0.5, 0.5],
        z=linspace(-5, 5, jz + 1)
    )

    # 添加井筒单元（位于左侧外部 y=10m 处，大体积作为定压井筒）
    new_cell = mesh.add_cell(pos=[0, 10, 0], vol=1.0e10)
    # 将井筒单元与左侧中心单元连接（创建流体通道）
    cell = mesh.get_nearest_cell(pos=[0, 0, 0])
    mesh.add_face(cell, new_cell, dist=1.0,
                  area=0.1  # 矫正产能：通过面积调节控制产量
                  )
    x0, x1 = mesh.get_pos_range(0)
    # 右侧（x=20m）设为大体积单元，模拟定压边界
    for cell in mesh.cells:
        x, y, z = cell.pos
        if abs(x - x1) < 0.1:
            cell.vol = 1.0e8  # 右侧恒定压力

    # 定义流体：oil（从数据文件读取物性）和 water（定密度1000 kg/m3）
    fludefs = [
        create_oil(name='oil'),
        FluDef(den=1000, vis=1.0e-3, name='water')
    ]

    def get_p(x, y, z):
        """
        定义初始压力分布：
          - 井筒区域（y>5）：井底流压2MPa（低压，形成生产压差）
          - 储层区域（y<=5）：原始地层压力12MPa
        均考虑静水压力梯度1e4 Pa/m。
        """
        if y > 5:
            print("Outlet Pressure:", 2e6)
            return 2e6 - z * 1.0e4
        else:
            return 12e6 - z * 1.0e4

    def get_t(x, y, z):
        """
        定义温度场分布：
          - 近井区（x<10, |z|<3）：150度+273=423K（模拟注热或地热加热）
          - 远井区：60度+273=333K
        温度影响原油粘度，从而影响产能。
        """
        if abs(z) < 3 and x < 10:
            return 150 + 273
        else:
            return 60 + 273

    z0, z1 = mesh.get_pos_range(2)

    def denc(x, y, z):
        """
        定义存储系数：上下边界设为极大值模拟封闭条件，
        内部区域为正常值1e6。
        与gas_prod.py中的denc=5e6不同，这里上下边界使用不同的高值（5e7 vs 1e6）。
        """
        if abs(z - z0) < 0.01 or abs(z - z1) < 0.01:
            return 50000.0 * 1000.0
        else:
            return 1000.0 * 1000.0

    # 创建渗流模型：
    #   孔隙度0.2，孔隙模量100MPa
    #   各向异性渗透率：水平2e-14 m2，垂直2e-15 m2（各向异性比10:1）
    #   考虑重力加速度 -9.81 m/s2
    model = tfc.create(
        mesh, porosity=0.2, pore_modulus=100e6,
        p=get_p, temperature=get_t,
        s=s,
        denc=denc,
        perm=Tensor3(xx=2e-14, yy=2e-14, zz=2.0e-15),
        disable_update_den=True,
        fludefs=fludefs,
        gravity=[0, 0, -9.81],
    )
    # 设置最大时间步长为1周
    tfc.set_dt_max(model, 3600 * 24 * 7)
    return model


def show(model, jx, jz):
    """
    在界面上显示模型状态（压力、温度、油饱和度、油粘度）。

    Args:
        model: 渗流模型对象
        jx: 水平方向网格单元数量
        jz: 垂直方向网格单元数量
    """
    from zmlx.fig import contourf, axes2, plt_show, suptitle, tight_layout, auto_layout

    # 使用mask过滤掉井筒区域（y>5），只显示储层区域
    mask = tfc.get_y(model) < 5

    x = tfc.get_x(model, shape=(jx, jz), mask=mask)
    z = tfc.get_z(model, shape=(jx, jz), mask=mask)
    p = tfc.get_p(model, shape=(jx, jz), mask=mask)
    t = tfc.get_t(model, shape=(jx, jz), mask=mask)
    s = tfc.get_v(model, 0, shape=(jx, jz), mask=mask) / tfc.get_v(model, None, shape=(jx, jz), mask=mask)
    vis = tfc.as_numpy(model).fluids(0).vis[mask].reshape([jx, jz])

    # 四列并排显示：压力、温度、油饱和度、油粘度（对数坐标）
    opts = dict(aspect='equal', xlabel='x/m', ylabel='z/m')
    obj = auto_layout(
        axes2(
            contourf(x, z, p, cbar=dict(label='Pressure', shrink=0.7)),
            index=1,
            title='Pressure', **opts
        ),
        axes2(
            contourf(x, z, t, cbar=dict(label='Temperature', shrink=0.7, cmap='coolwarm')),
            index=2,
            title='Temperature', **opts
        ),
        axes2(
            contourf(x, z, s, cbar=dict(label='Saturation', shrink=0.7), cmap='coolwarm'),
            index=3,
            title='oil saturation', **opts
        ),
        axes2(
            contourf(x, z, np.log10(vis), cbar=dict(label='Viscosity', shrink=0.7), cmap='coolwarm'),
            index=4,
            title='oil viscosity', **opts
        ),
        suptitle(f'时间: {tfc.get_time(model, as_str=True)}'),
        tight_layout(),
        aspect_ratio=1,
    )
    plt_show(obj, caption='模型状态')


def main():
    """
    主函数：创建80x40网格的水平井开采模型（初始油饱和度0.6），
    模拟1000天的产油产水过程。
    """
    jx, jz = 40 * 2, 20 * 2
    model = create(jx, jz, s=(0.6, 0.4))
    tfc.solve(model, extra_plot=lambda: show(model, jx, jz), time_forward=1000 * 24 * 3600)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
