# ** desc = '水平二维EGS换热计算'
"""
水平方向二维的干热岩换热计算模型（双竖直井注采计算）。

物理问题：
    模拟 Enhanced Geothermal System (EGS，增强型地热系统) 的基本过程：
    在高温干热岩体中注入冷水，通过裂隙网络循环加热后产出热水。

    计算区域：二维水平模型（x-y平面，z方向仅一层），默认100m x 100m
    注入井：区域左下角 (x_min, y_min)
    生产井：区域右上角 (x_max, y_max)

关键技术：
    1. 离散裂隙网络 (DFN, Discrete Fracture Network)：
       - 随机生成天然裂缝（控制长度、密度、方向）
       - 可添加连接注入井和生产井的人工裂缝（水力压裂模拟）
       - 裂缝具有高渗透率，是流体流动的主要通道

    2. 流动-热耦合：
       - 冷水从注入井进入，沿裂缝网络流向生产井
       - 途经高温岩体时被加热，热量通过对流和传导传递
       - 加热距离 (heating_dist) 控制流-固换热效率

    3. 生产控制：
       - 注入速率由 vol_day 控制（每天注入体积）
       - 生产井保持恒压（p_prod），通过虚拟单元实现

外部执行方式：
    from zmlx.demo import egs2
    egs2.execute()
"""

from zmlx import *


def create_model(dx=100.0, dy=100.0, dz=100.0, temp=500.0, pre=10.0e6,
                 perm=1.0e-14, porosity=0.1, denc=3e6,
                 heat_cond=2.0, vol_day=100.0, p_prod=5e6, t_inj=300.0,
                 fl_min=10.0, fl_max=40.0,
                 angles=None, p21=0.2, f_perm=1.0e-12, has_hf=True,
                 heating_dist=1.0):
    """
    创建EGS换热计算模型。

    构建二维水平储层（x-y平面），包含基质和裂缝系统，
    设置注入井和生产井的边界条件。

    参数：
        dx, dy, dz: 模型尺寸 [m]（x和y方向网格大小为1m，z方向仅用1个网格）
        temp: 储层初始温度 [K]，默认 500K
        pre: 储层初始压力 [Pa]，默认 10 MPa
        perm: 基质渗透率 [m^2]，默认 1e-14
        porosity: 基质孔隙度 [-]，默认 0.1
        denc: 体积热容 [J/(m^3.K)] = rho * c，默认 3e6
        heat_cond: 导热系数 [W/(m.K)]，默认 2.0
        vol_day: 每天注入冷水的体积 [m^3/day]，默认 100
        p_prod: 生产井压力 [Pa]，默认 5 MPa
        t_inj: 注入冷水温度 [K]，默认 300K
        fl_min, fl_max: 天然裂缝长度的最小值和最大值 [m]
        angles: 天然裂缝方向角度（默认None表示完全随机）
        p21: 天然裂缝的密度（单位面积裂缝总长度）[-]，默认 0.2
        f_perm: 裂缝渗透率 [m^2]，默认 1e-12
        has_hf: 是否添加连接注采井的人工裂缝（水力压裂），默认 True
        heating_dist: 换热距离 [m]（控制流体与固体间换热效率），默认 1.0

    返回：
        Seepage对象：初始化完成的EGS计算模型
    """
    # 参数范围校验
    assert 15.0 <= dx <= 200.0 and 15.0 <= dy <= 200.0 and 15.0 <= dz <= 200.0
    assert 300.0 <= temp <= 700.0
    assert 1e6 <= pre <= 30e6
    assert 1.0e-16 <= perm <= 1.0e-12
    assert 0.1 <= porosity <= 0.6

    # 创建网格（1m分辨率，z方向单层）
    jx = round(dx / 1.0)
    jy = round(dy / 1.0)
    x = np.linspace(0, dx, jx)
    y = np.linspace(0, dy, jy)
    z = [-dz / 2, dz / 2]
    mesh = create_cube(x, y, z)

    x_min, x_max = mesh.get_pos_range(0)
    y_min, y_max = mesh.get_pos_range(1)

    # 创建渗流传热耦合模型
    model = tfc.create(
        mesh=mesh, dt_min=1.0, dt_max=3600 * 24, cfl=0.5,
        # 流体采用水的物性（密度1000 kg/m^3，粘度1e-3 Pa.s）
        fludefs=[h2o.create(name='h2o', density=1000.0, viscosity=1.0e-3)],
        porosity=porosity, pore_modulus=200e6, p=pre, temperature=temp,
        denc=denc, s=1.0, perm=perm,
        heat_cond=heat_cond, gravity=[0, 0, 0], dist=heating_dist
    )

    # 设置随机数种子，确保每次生成的DFN结构可重复
    set_srand(0)

    # ===== 生成离散裂隙网络 (DFN) =====
    dfn = Dfn2()
    dfn.range = [x_min, y_min, x_max, y_max]

    # 添加随机天然裂缝
    dfn.add_frac(
        angles=np.linspace(0.0, 3.1415 * 2, 100) if angles is None else angles,
        lengths=np.linspace(fl_min, fl_max, 100), p21=p21)

    # 添加连接注采井的人工裂缝（模拟水力压裂）
    if has_hf:
        dfn.add_frac(x0=x_min, y0=y_min, x1=x_max, y1=y_max)

    # 显示DFN裂缝分布图
    fractures = dfn.get_fractures()
    show_dfn2(fractures, caption='裂缝')

    # ===== 将裂缝导入计算网格 =====
    for x0, y0, x1, y1 in dfn.get_fractures():
        print(f'add fracture: {[x0, y0, x1, y1]}. ', end='')
        cell_beg = model.get_nearest_cell(pos=[x0, y0, 0])
        cell_end = model.get_nearest_cell(pos=[x1, y1, 0])

        def get_dist(cell_pos):
            """
            计算单元到裂缝终点和裂缝线的加权距离，
            用于裂缝路径追踪的启发式函数。
            """
            return seg_point_distance([[x0, y0], [x1, y1]],
                                      cell_pos[0: 2]) + point_distance(cell_pos,
                                                                       cell_end.pos)

        # 沿裂缝方向逐单元建立高渗透率连接
        count = 0
        while cell_beg.index != cell_end.index:
            # 寻找当前单元所有邻接单元中，距离裂缝最近的作为下一跳
            dist = [get_dist(c.pos) for c in cell_beg.cells]
            idx = 0
            for i in range(1, len(dist)):
                if dist[i] < dist[idx]:
                    idx = i
            cell = cell_beg.get_cell(idx)
            # 创建面并设置高渗透率（模拟裂缝的高导流能力）
            face = model.add_face(cell_beg, cell)
            tfc.set_face(face=face, perm=f_perm)
            count += 1
            cell_beg = cell
        print(f'count of face modified: {count}')

    # ===== 设置注入井 =====
    assert 0 <= vol_day
    pos = [x_min, y_min, 0]
    cell = model.get_nearest_cell(pos)
    flu = cell.get_fluid(0).get_copy()
    flu.set_attr(model.reg_flu_key('temperature'), t_inj)  # 设置注入冷水温度
    model.add_injector(
        cell=cell, fluid_id=0, flu=flu, pos=pos, radi=2,
        value=vol_day / (3600 * 24))  # 将日注入量转为 m^3/s

    # ===== 设置生产井（通过虚拟单元实现恒压边界） =====
    # 虚拟单元置于计算区域上方远处（z=1000m），体积巨大以保持压力稳定
    virtual_cell = tfc.add_cell(
        model, pos=[x_max, y_max, 1000.0], porosity=1.0, pore_modulus=100e6,
        vol=1.0e6,
        temperature=temp, p=p_prod, s=1.0)
    cell = model.get_nearest_cell([x_max, y_max, 0])
    tfc.add_face(
        model, virtual_cell, cell, heat_cond=0, perm=max(perm, f_perm),
        area=1.0, length=1.0)

    return model


def plot_cells(model, folder=None):
    """
    绘制储层状态图（压力、岩石温度、流体温度）。

    当有GUI时实时显示；给定folder时将图片保存到文件。

    参数：
        model: Seepage对象
        folder: 图片保存目录（可选）
    """
    if not gui.exists():
        return
    from zmlx.plt import show_tricontourf
    assert isinstance(model, Seepage)

    time = time2str(tfc.get_time(model))
    year = tfc.get_time(model) / (3600 * 24 * 365)

    # 获取所有单元格坐标，排除最后一个虚拟单元
    x = as_numpy(model).cells.x
    y = as_numpy(model).cells.y
    x = x[: -1]
    y = y[: -1]

    def show_ca(idx, name):
        """
        绘制指定属性的三角网格填充等值线图。
        """
        p = as_numpy(model).cells.get(idx)
        p = p[: -1]
        show_tricontourf(
            x, y, p, caption=name, title=f'time = {time}',
            fname=make_fname(year, path.join(folder, name), '.jpg', 'y'))

    # 绘制流体压力和岩石温度分布
    show_ca(-12, 'pressure')
    show_ca(model.get_cell_key('temperature'), 'rock_temp')

    # 绘制流体温度分布
    t = as_numpy(model).fluids(0).get(index=model.reg_flu_key('temperature'))
    t = t[: -1]
    show_tricontourf(
        x, y, t, caption='flu_temp', title=f'time = {time}',
        fname=make_fname(year, path.join(folder, 'flu_temp'), '.jpg', 'y'))


def solve(model: Seepage, time_max=3600 * 24 * 365 * 30, folder=None,
          day_save=30.0):
    """
    求解EGS换热模型。

    使用共轭梯度法迭代求解流动-热耦合问题，
    通过压力控制器维持生产井定压，并可定期保存模型状态。

    参数：
        model:     Seepage对象（由create_model创建）
        time_max:  求解总时间 [s]，默认30年
        folder：   数据保存目录（可选）
        day_save： 每隔多少天保存一次模型状态，默认30天
    """
    if folder is not None:
        print_tag(folder)
        print(f'Solve. folder = {folder}')
        if gui.exists():
            gui.title(f'Data folder = {folder}')

    # 设置共轭梯度求解器（高精度）
    solver = ConjugateGradientSolver(tolerance=1.0e-14)
    iterate = GuiIterator(
        tfc.iterate,
        lambda: plot_cells(model, folder=path.join(folder, 'figures')))

    # 创建压力控制器：维持生产井（最后一个虚拟单元）压力恒定
    virtual_cell = model.get_cell(model.cell_number - 1)
    p = virtual_cell.pre
    print(f'The production pressure is: {p / 1e6} MPa')
    p_ctrl = PressureController(
        cell=virtual_cell, t=[-1e20, 1e20], p=[p, p], modify_pore=True)

    # 创建模型状态保存管理器（可选）
    if folder is not None:
        save = SaveManager(
            folder=path.join(folder, 'models'), dtime=day_save,
            get_time=lambda: tfc.get_time(model) / (24 * 3600),
            save=model.save, ext='.seepage', time_unit='d')
    else:
        save = None

    # 迭代求解到指定时间
    while tfc.get_time(model) < time_max:
        iterate(model, solver=solver)
        p_ctrl.update(t=tfc.get_time(model), modify_pore=True)  # 保持生产井压力
        if save is not None:
            save()  # 按设定频率保存模型
        step = tfc.get_step(model)
        if step % 10 == 0:
            time = time2str(tfc.get_time(model))
            dt = time2str(tfc.get_dt(model))
            print(
                f'step = {step}, dt = {dt}, time = {time}, p_out = {virtual_cell.pre / 1e6} MPa')


def execute(folder=None, time_max=3600 * 24 * 365 * 10, day_save=30.0,
            **kwargs):
    """
    执行EGS建模和计算的全过程。

    将 **kwargs 全部传递给 create_model 函数进行建模，
    然后调用 solve 函数进行求解。

    参数：
        folder: 数据保存目录（可选）
        time_max: 求解总时间 [s]，默认10年
        day_save: 每隔多少天保存一次数据，默认30天
        **kwargs: 传递给 create_model 的建模参数
    """
    model = create_model(**kwargs)
    print(model)
    solve(model, folder=folder, time_max=time_max, day_save=day_save)


def _test3():
    """
    执行默认参数的EGS求解过程，并保存数据到默认目录。
    """
    execute(folder=opath('egs2'))


if __name__ == '__main__':
    gui.execute(_test3, close_after_done=False, disable_gui=False)
