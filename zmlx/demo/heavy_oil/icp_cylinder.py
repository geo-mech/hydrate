# ** desc = '原位转化-竖直井-在一个圆柱形状的区域内'
#
# 本案例模拟油页岩或重油的原位转化（In-situ Conversion Process, ICP）过程：
# 在圆柱形区域内，通过竖直井进行电加热，使干酪根（kerogen）热解转化为油气。
# 模型采用柱坐标网格（径向r和竖直z），储层范围为z方向[-15,15]m，r方向[0,50]m。
# 初始条件下，储层内包含干酪根（kg）、重油（ho）、轻油（lo）、甲烷（ch4）、水（h2o）等组分。
# 加热井位于圆柱中心（r=0），在z方向[-10,10]m范围内均匀加热，功率50kW。
# 通过tfc（热-流-化学）耦合框架模拟热传导、流体流动和化学反应（干酪根热解）的耦合过程。
# 展示了温度场、压力场和各组分饱和度随时间的演化。

from zmlx import *


def create(years_heating=10.0, years_max=10.0, power=50e3):
    """
    创建原位转化圆柱模型。

    参数:
        years_heating: float，加热时长（年）。控制加热器的工作时间
        years_max: float，总计算时长（年）。整个模拟的时间跨度
        power: float，加热功率（瓦特）。电加热器的总功率
    返回:
        Seepage对象，配置完成的渗流-热-化学耦合模型
    """
    from zmlx.seepage_mesh.cylinder import create_vertical_cylinder

    # 在半径方向的网格节点（从井中心向外逐渐变疏，节省计算量）
    vr = [0.0]
    dr = 1.0
    while vr[-1] < 50.0:                   # 半径范围0~50m
        vr.append(vr[-1] + dr)
        dr += 0.1                           # 网格间距逐渐增大（近井区域分辨率更高）
    vr = sorted(vr)

    # 在竖直方向的网格节点（储层内部均匀，外部逐渐变疏）
    vz = np.linspace(-15, 15, 31).tolist()  # 储层范围内（-15~15m）均匀划分31个节点
    dz = 1.0
    while max(vz) < 40.0:                   # 向上延伸至40m
        vz.append(max(vz) + dz)
        dz += 0.2
    dz = 1.0
    while min(vz) > -40.0:                  # 向下延伸至-40m
        vz.append(min(vz) - dz)
        dz += 0.2
    vz = sorted(vz)

    # 显示网格节点信息
    print(f"vr = {vr}")
    print(f"vz = {vz}")

    # 创建竖直圆柱网格
    mesh = create_vertical_cylinder(z=vz, r=vr)
    print(f"mesh = {mesh}")

    z_min, z_max = get_pos_range(mesh, 2)  # 获取网格在z方向的范围
    print(f"z_min = {z_min}, z_max = {z_max}")

    def get_perm(x, y, z):                 # 渗透率分布函数：仅储层范围（-15~15m）有渗透率
        return 1.0e-15 if -15 <= z <= 15 else 0

    def get_s(x, y, z):                    # 初始饱和度分布函数
        # 储层内且y<5的区域：包含多种组分（干酪根为主）
        if -15 <= z <= 15 and y < 5:
            return {'ch4': 0.08, 'h2o': 0.04, 'lo': 0.08,
                    'ho': 0.2, 'kg': 0.6}
        else:
            return {'ch4': 1}              # 储层外：纯甲烷

    def get_denc(x, y, z):                 # 体积热容（密度*比热）分布函数
        if abs(z - z_min) < 0.1 or abs(z - z_max) < 0.1:  # 上下边界处设极大值模拟恒温边界
            return 1e20
        else:
            return 4e6                      # 储层正常体积热容

    def get_porosity(x, y, z):             # 孔隙度分布函数
        return 0.3 if -15 <= z <= 15 else 0.01  # 储层内0.3，储层外仅0.01

    # 渗透率曲线（用于计算相对渗透率随饱和度的变化）
    gr = create_krf(faic=0.02, n=3.0, k_max=100, s_max=2.0,
                    count=500, as_interp=True)

    # 默认的相对渗透率曲线（用于未明确指定的流体组合）
    default_kr = create_krf(faic=0.05, n=2.0, count=300,
                            as_interp=True)

    # 设置竖直井加热的范围（z方向-10~10m），找到涉及的单元格
    heating_cell_ids = []
    for z in np.linspace(-10, 10, 100):    # 沿加热段均匀取100个点
        c = mesh.get_nearest_cell(pos=[0, 0, z])  # 找到距井轴最近的单元格
        if c.index not in heating_cell_ids:
            heating_cell_ids.append(c.index)

    print(f"heating_cell_ids = {heating_cell_ids}")
    v_pos = [mesh.get_cell(i).pos for i in heating_cell_ids]  # 获取加热单元格的位置

    ca = tfc.cell_keys()                    # 获取tfc框架的单元格键定义
    # 定义加热器（以注入器的形式向单元格添加热量）
    injectors = [
        {'pos': pos, 'radi': 3, 'ca_mc': ca.mc,  # 位置、影响半径、质量/能量键
         'ca_t': ca.temperature,                   # 温度键
         'value': power / len(v_pos),              # 每个加热单元格分配的功率
         'opers': [[years_heating * 3600.0 * 24.0 * 365.0,  # 加热时长转换为秒
                    '0']],                                  # 加热结束后功率归零
         } for pos in v_pos]

    # 用于求解器（solve）的选项
    solve = {
        'time_max': 3600.0 * 24.0 * 365.0 * years_max,  # 总模拟时间（秒）
    }

    # 创建模型
    model = tfc.create(
        mesh=mesh,
        keys=ca.get_keys(),                   # 使用tfc框架定义的属性键
        fludefs=icp.create_fludefs(),         # 定义流体组分（干酪根、油、气、水等）
        reactions=icp.create_reactions(temp_max=1000),  # 定义化学反应（干酪根热解反应）
        porosity=get_porosity,                 # 孔隙度（空间分布函数）
        pore_modulus=100e6,                    # 孔隙体积模量（100MPa）
        p=20e6,                                # 初始压力20MPa
        temperature=350.0,                     # 初始温度350K
        denc=get_denc,                         # 体积热容（空间分布函数）
        s=get_s,                               # 初始饱和度（空间分布函数）
        perm=get_perm,                         # 渗透率（空间分布函数）
        heat_cond=2.0,                         # 热传导系数2.0 W/(mK)
        dist=0.2,                              # 热扩散率
        has_solid=False,                       # 不单独考虑固体相
        dt_max=3600.0 * 24.0 * 5.0,            # 最大时间步长5天
        gravity=[0, 0, -10],                   # 重力加速度（z方向-10 m/s^2）
        gr=gr,                                 # 渗透率曲线
        default_kr=default_kr,                 # 默认相对渗透率曲线
        injectors=injectors,                   # 加热器定义
        texts={'solve': solve},                # 传递给求解器的额外文本参数
    )
    # 返回模型
    return model


def show(model: Seepage):
    """
    显示模型的当前状态：温度、压力和各组分饱和度的空间分布。

    参数:
        model: Seepage对象，要显示的模型
    """
    def on_figure(figure):
        """
        绘图回调函数：在指定图形中绘制8个子图。
        """
        from zmlx.plt import calculate_subplot_layout
        n_rows, n_cols = calculate_subplot_layout(8, subplot_aspect_ratio=0.5, fig=figure)  # 自动计算布局
        opts = dict(ncols=n_cols, nrows=n_rows, xlabel='x', ylabel='z', aspect='equal')
        mask = get_cell_mask(model=model, xr=[0, 30], zr=[-20, 20])  # 选取显示范围（r方向0~30m，z方向-20~20m）
        x = tfc.get_x(model, mask=mask)        # 获取选取单元格的x坐标
        z = tfc.get_z(model, mask=mask)        # 获取选取单元格的z坐标
        args = ['tricontourf', x, z, ]          # 使用三角网格填充等值线图

        # 子图1：温度分布
        t = tfc.get_t(model, mask=mask)
        add_axes2(figure, add_items, item(*args, t, cbar=dict(label='温度', shrink=0.6), cmap='coolwarm'),
                  title='温度', index=1, **opts)
        # 子图2：压力分布
        p = tfc.get_p(model, mask=mask)
        add_axes2(figure, add_items, item(*args, p, cbar=dict(label='压力', shrink=0.6), cmap='jet'),
                  title='压力', index=2, **opts)
        # 子图3-8：各组分饱和度分布
        v = tfc.get_v(model, mask=mask)       # 总流体体积
        index = 3
        for fid in ['kg', 'ho', 'lo', 'ch4', 'h2o', 'steam', ]:
            s = tfc.get_v(model, mask=mask, fid=fid) / v  # 计算各组分的饱和度
            add_axes2(figure, add_items, item(*args, s, cbar=dict(label=f'{fid}饱和度', shrink=0.6)),
                      title=f'{fid}饱和度', index=index, **opts)
            index += 1

    # 执行绘图
    plot(on_figure, caption=f'model({model.handle})', clear=True, tight_layout=True,
         suptitle=f'time = {tfc.get_time(model, as_str=True)}'
         )


def main():
    """
    主函数：创建ICP圆柱模型并执行求解。
    默认参数：加热10年，总时长10年，加热功率50kW。
    """
    model = create()                          # 创建模型
    tfc.solve(model=model, extra_plot=lambda: show(model))  # 求解并实时显示结果


if __name__ == '__main__':
    # 通过GUI执行主函数；--no-gui参数用于无图形界面运行
    gui.execute(main, close_after_done=False)
