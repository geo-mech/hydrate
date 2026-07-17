# ** desc = '储层-井筒耦合计算模型示例'
#
# 物理问题描述：
#   本模型模拟圆柱坐标系下天然气水合物藏与井筒的耦合开采过程。
#   模型包含三个地层区域：下伏层、水合物层、上覆层。
#   水合物层深度范围约-360~-300 m（由hyd_bottom=-300, hyd_h=60确定），
#   下伏层厚度100 m。储层初始压力12 MPa（海底），随深度线性增加；
#   初始温度约276 K（海底），地温梯度0.04466 K/m。
#   垂直井筒位于模型中心（r=0），通过降压开采水合物。
#   水合物饱和度在深度方向上随机分布（0.1~0.5之间），
#   以模拟真实储层的非均匀性。
#
# 建模方法：
#   1. 网格构建：使用圆柱坐标网格（create_cylinder），径向30个网格，
#      轴向110个网格。井筒网格独立创建后合并到储层网格中，
#      在储层-井筒界面处通过add_face建立连接。
#   2. 初始条件：压力和温度使用LinearField随深度线性变化。
#      在水合物层底部检查热力学平衡（计算平衡温度和压力）。
#   3. 相对渗透率：使用Corey模型（srg=0.01, srw=0.4, ag=3.5, aw=4.5）。
#   4. 生产井：通过create_krf生成流入动态关系（IPR），
#      设置生产压力3 MPa（由p_prod参数控制）。
#   5. 求解过程使用共轭梯度求解器（ConjugateGradientSolver），
#      自动保存模型状态和cell数据。
#
# 关键参数说明：
#   模型范围：半径40 m，深度范围-400~0 m
#   水合物层：底部-300 m，厚度60 m（即-300~-240 m为水合物层主体）
#   海底温度：276.08 K（约2.93°C）
#   海底压力：12 MPa
#   地温梯度：0.04466 K/m
#   渗透率：储层1e-14 m^2，水合物层中心区域增大100倍
#   孔隙度：0.3，孔隙模量200 MPa
#   生产压力：3 MPa
#   模拟时间：20年（每天保存一次）

from zmlx import *


def create_cylinder(z, r, offset=None):
    """
    创建圆柱坐标系的网格，并可选择偏移网格位置。

    通过create_cylinder函数生成标准圆柱网格，然后对每个cell的
    坐标进行重排列和偏移，使圆柱轴线与指定方向对齐。

    参数:
        z (list/array): 轴向节点位置序列
        r (list/array): 径向节点位置序列
        offset (list, optional): 坐标偏移量 [dx, dy, dz]，默认为 [0, 0, 0]

    返回:
        SeepageMesh: 创建并偏移后的圆柱网格
    """
    from zmlx import create_cylinder as impl
    mesh = impl(x=z, r=r)
    if offset is None:
        offset = [0, 0, 0]
    # 重新排列坐标：将轴向(x)映射到z方向，径向(r)映射到x-y平面
    for cell in mesh.cells:
        x, y, z = cell.pos
        cell.pos = y + offset[0], z + offset[1], x + offset[2]
    return mesh


def create_mesh(radius, hyd_bottom, under_h, hyd_h):
    """
    创建储层-井筒耦合网格。

    网格由两部分组成：
    1. 储层网格：圆柱坐标系，包含下伏层、水合物层、上覆层
    2. 井筒网格：细长圆柱，沿z方向贯穿水合物层，偏移到y=-100处

    储层和井筒网格在界面处通过add_face建立连接。

    参数:
        radius (float): 储层径向范围（m）
        hyd_bottom (float): 水合物层底部的z坐标（m）
        under_h (float): 下伏层厚度（m）
        hyd_h (float): 水合物层厚度（m）

    返回:
        SeepageMesh: 创建完成的储层-井筒耦合网格
    """
    assert np is not None
    # 轴向节点：下伏层底部 -> 下伏层顶部 -> 水合物层顶部 -> 地表
    z = [hyd_bottom - under_h, hyd_bottom - 10, hyd_bottom + hyd_h + 10, 0]
    z1 = np.linspace(z[0], z[1], 10)   # 下伏层：10层网格
    z2 = np.linspace(z[1], z[2], 50)   # 水合物层及附近：50层网格（加密）
    z3 = np.linspace(z[2], z[3], 50)   # 上覆层：50层网格
    mesh = create_cylinder(
        z=np.concatenate((z1, z2[1:], z3[1:])),
        r=np.linspace(0, radius, 30))  # 径向：30个网格
    # 创建井筒网格（径向仅1个网格，r=[0,1]表示井筒半径1m）
    wel = create_cylinder(
        z=np.concatenate((z2, z3[1:])),
        r=[0, 1], offset=[0, -100, 0])

    # 将井筒的cell添加到储层网格中
    cell_n0 = mesh.cell_number
    for c0 in wel.cells:
        assert isinstance(c0, SeepageMesh.Cell)
        c1 = mesh.add_cell()
        c1.pos = c0.pos
        c1.vol = c0.vol

    # 将井筒内部的face添加到储层网格中
    face_n0 = mesh.face_number
    for f0 in wel.faces:
        assert isinstance(f0, SeepageMesh.Face)
        c0 = f0.get_cell(0)
        c1 = f0.get_cell(1)
        f1 = mesh.add_face(cell_n0 + c0.index, cell_n0 + c1.index)
        f1.area = f0.area
        f1.length = f0.length

    # 在储层-井筒界面建立连接face
    for idx in range(cell_n0, mesh.cell_number):
        c0 = mesh.get_cell(idx)
        x, y, z = c0.pos
        assert abs(y + 100) < 0.1  # 井筒在y=-100处
        c1 = mesh.get_nearest_cell(pos=[x, 0, z])  # 找到最近的储层cell
        face = mesh.add_face(c0, c1)
        face.area = 1
        face.length = 1

    # 验证face总数的正确性
    assert face_n0 + wel.face_number + wel.cell_number == mesh.face_number
    return mesh


def create_ini(
        mesh, hyd_bottom, hyd_h, t_seabed, p_seabed, grad_t,
        perm, porosity, pore_modulus, reset_sh=False):
    """
    创建初始场（包含各种物理属性的空间分布函数）。

    初始场包括：孔隙度、孔隙模量、压力、温度、密度*比热、
    饱和度、渗透率、热导率、网格间距等。

    参数:
        mesh: 渗流网格
        hyd_bottom (float): 水合物层底部的z坐标（m）
        hyd_h (float): 水合物层厚度（m）
        t_seabed (float): 海底温度（K）
        p_seabed (float): 海底压力（Pa）
        grad_t (float): 地温梯度（K/m，每下降1m温度升高量）
        perm (float): 渗透率（m^2）
        porosity (float): 孔隙度
        pore_modulus (float): 孔隙模量（Pa）
        reset_sh (bool): 是否重新生成随机的饱和度分布

    返回:
        dict: 包含各物理属性函数的字典，可直接作为hydrate.create_kwargs的输入
    """
    # 尝试从文件读取已有的水合物饱和度数据
    fname = opath('res_well', 'res_well_z2s.txt')
    if not path.isfile(fname):
        reset_sh = True
    if reset_sh:
        # 生成随机的饱和度分布（0.1~0.5）
        from zmlx.alg.base import join_cols
        vz = np.linspace(
            hyd_bottom - 20, hyd_bottom + hyd_h + 20, 100)
        vs = np.random.uniform(low=0.1, high=0.5, size=vz.size)
        dat = join_cols(vz, vs)
        np.savetxt(fname, dat, fmt='%.3f')
    else:
        # 读取已有的饱和度数据文件
        dat = np.loadtxt(fname)
        vz, vs = dat[:, 0], dat[:, 1]

    # 使用scipy插值构建深度-饱和度映射函数
    from scipy.interpolate import interp1d
    z2s = interp1d(vz, vs)

    def get_s(x, y, z):
        """
        初始饱和度函数。
        井筒区域（y < -1）：仅含水（气相0，水相1.0，水合物0）
        水合物层（hyd_bottom <= z <= hyd_bottom + hyd_h）：含水+水合物
        其他区域（上/下伏层）：仅含水
        返回格式：(气相饱和度, 水相饱和度, (水合物饱和度, 水合物密度索引))
        """
        if y < -1:
            return 0, 1.0, (0.0, 0)
        if hyd_bottom <= z <= hyd_bottom + hyd_h:
            s = clamp(z2s(z), 0.0, 0.5)
            return 0, 1 - s, (s, 0)
        else:
            return 0, 1.0, (0.0, 0)

    z_min, z_max = mesh.get_pos_range(2)

    def get_denc(x, y, z):
        """
        储层土体的密度乘以比热容。
        井筒区域：3e6 J/(m^3·K)
        储层区域（非顶底边界）：3e6 J/(m^3·K)
        顶部和底部边界：1e20 J/(m^3·K)（极大值以固定温度边界条件）
        """
        if y < -1:
            return 3e6
        else:
            return 3e6 if z_min + 0.1 < z < z_max - 0.1 else 1e20

    def get_fai(x, y, z):
        """
        孔隙度函数。
        顶部边界（z接近z_max）：设为极大值1e9以固定压力边界条件
        其他区域：使用给定的孔隙度值
        """
        if z > z_max - 0.1:  # 顶部固定压力
            return 1.0e9
        else:
            return porosity

    # 创建线性的温度场和压力场（随深度变化）
    t_ini = LinearField(v0=t_seabed, z0=0, dz=-grad_t)  # 温度随深度线性增加
    p_ini = LinearField(v0=p_seabed, z0=0, dz=-0.01e6)   # 压力随深度线性增加

    # 在水合物层底部检查热力学平衡条件
    t0 = t_ini(0, 0, hyd_bottom)
    p0 = p_ini(0, 0, hyd_bottom)

    from zmlx.react import ch4_hydrate

    # 计算平衡温度和压力，判断初始条件是否在水合物稳定区
    teq = ch4_hydrate.get_t(p0)      # 在当前压力下的平衡温度
    peq = ch4_hydrate.get_p(t0)      # 在当前温度下的平衡压力
    print(f'At bottom of hydrate layer: '
          f't = {t0 - 273.15}, p = {p0 / 1e6} MPa, teq = {teq - 273.15}, '
          f'peq = {peq / 1e6} MPa')

    def get_p(x, y, z):
        """
        设置初始压力。
        井筒顶部区域（y < -1 且 z > z_max - 0.1）：3 MPa（生产压降影响）
        其他区域：使用线性压力场
        """
        if y < -1 and z > z_max - 0.1:
            return 3e6
        else:
            return p_ini(x, y, z)

    def get_k(x, y, z):
        """
        设置渗透率。
        井筒内部（y < -99）：1e-8 m^2（高渗）
        上覆层以上（y > -1）：给定渗透率perm
        水合物层中部（hyd_bottom+10 ~ hyd_bottom+hyd_h-10）：perm * 100（高渗通道）
        其他区域：0（隔层）
        """
        if y < -99:
            return 1.0e-8
        if y > -1:
            return perm
        if hyd_bottom + 10 < z < hyd_bottom + hyd_h - 10:
            return perm * 100
        else:
            return 0

    def get_dist(x, y, z):
        """
        设置网格特征间距。
        储层区域（y > -1）：0.1 m
        井筒区域（y <= -1）：0.01 m
        """
        if y > -1:
            return 0.1
        else:
            return 0.01

    # 返回所有物理属性函数的字典
    return {'porosity': get_fai, 'pore_modulus': pore_modulus,
            'p': get_p, 'temperature': t_ini,
            'denc': get_denc, 's': get_s, 'perm': get_k,
            'heat_cond': 2, 'dist': get_dist}


def create_model(
        radius=40., hyd_bottom=-300., under_h=100., hyd_h=60.,
        t_seabed=276.0826483615683, p_seabed=12e6, grad_t=0.04466,
        perm=1.0e-14, porosity=0.3, pore_modulus=200e6, p_prod=3e6
):
    """
    创建储层-井筒耦合的完整计算模型。

    整合网格创建、初始场设置、相渗曲线、生产井定义等所有组件。

    参数:
        radius (float): 储层径向范围，默认40 m
        hyd_bottom (float): 水合物层底部z坐标，默认-300 m
        under_h (float): 下伏层厚度，默认100 m
        hyd_h (float): 水合物层厚度，默认60 m
        t_seabed (float): 海底温度，默认276.08 K
        p_seabed (float): 海底压力，默认12 MPa
        grad_t (float): 地温梯度，默认0.04466 K/m
        perm (float): 渗透率，默认1e-14 m^2
        porosity (float): 孔隙度，默认0.3
        pore_modulus (float): 孔隙模量，默认200 MPa
        p_prod (float): 生产压力，默认3 MPa

    返回:
        Seepage: 创建完成的储层-井筒耦合渗流模型
    """
    # 创建储层-井筒耦合网格
    mesh = create_mesh(
        radius=radius, hyd_bottom=hyd_bottom,
        under_h=under_h, hyd_h=hyd_h
    )
    # 创建初始场（各种物理属性的空间分布函数）
    ini = create_ini(
        mesh=mesh, hyd_bottom=hyd_bottom,
        hyd_h=hyd_h, t_seabed=t_seabed,
        p_seabed=p_seabed, grad_t=grad_t,
        perm=perm, porosity=porosity,
        pore_modulus=pore_modulus
    )
    # 创建生产井的流入动态关系（IPR曲线）
    gr = create_krf(
        0.1, 2,
        as_interp=True,
        k_max=1, s_max=1, count=200
    )
    kw = hydrate.create_kwargs(gr=gr)
    kw.update(ini)
    kw.update(dict(
        gravity=(0, 0, -10),              # z方向重力加速度
        dt_ini=1.0, dt_min=1.0,            # 最小时间步长1秒
        dt_max=24 * 3600 * 7,              # 最大时间步长7天
        cfl=0.1                    # 相对体积变化限制
    ))

    # 创建模型
    model = tfc.create(mesh=mesh, **kw)

    # 设置相对渗透率曲线（Corey模型）
    vs, kg, kw = create_kr(srg=0.01, srw=0.4, ag=3.5, aw=4.5)
    i_gas = model.find_fludef('gas')   # 查找气相流体的索引
    i_liq = model.find_fludef('liq')   # 查找液相流体的索引
    assert len(i_gas) == 1 and len(i_liq) == 1
    i_gas = i_gas[0]
    i_liq = i_liq[0]
    # 设置气相的相对渗透率曲线
    model.set_kr(i_gas, vs, kg)
    # 设置液相的相对渗透率曲线
    model.set_kr(i_liq, vs, kw)

    return model


def plot_cells(model: Seepage, monitor=None, folder=None):
    """
    在界面上绘制计算结果，并可选择保存图片到指定文件夹。

    绘制内容包括：
    - 井筒内的压力、温度、水合物饱和度随深度分布曲线
    - 储层区域的压力、温度、CH4、水合物饱和度的二维云图
    - 生产曲线（累计产量和产气速率）

    参数:
        model (Seepage): 需要绘制的渗流模型
        monitor: 生产监测器（包含生产数据），用于绘制生产曲线
        folder (str, optional): 图片保存文件夹路径
    """
    if not gui.exists():
        return

    time = time2str(tfc.get_time(model))        # 当前模拟时间（可读格式）
    year = tfc.get_time(model) / (3600 * 24 * 365)  # 当前模拟时间（年）

    # 提取网格坐标和压力数据
    x = as_numpy(model).cells.x
    y = as_numpy(model).cells.y
    z = as_numpy(model).cells.z
    p = as_numpy(model).cells.pre

    # 绘制井筒压力随深度分布（y < -1的区域为井筒）
    plot_xy(y=z[y < -1], x=p[y < -1], caption='well_pre',
            xlabel='pre', ylabel='depth',
            title=f'time = {time}')

    # 绘制井筒温度随深度分布
    t = as_numpy(model).fluids(1).get(model.get_flu_key('temperature'))
    plot_xy(y=z[y < -1], x=t[y < -1], caption='well_T',
            xlabel='temperature', ylabel='depth',
            title=f'time = {time}')

    # 绘制井筒水合物饱和度随深度分布
    fv_all = as_numpy(model).cells.fluid_vol
    s = as_numpy(model).fluids(2, 0).vol / fv_all
    plot_xy(y=z[y < -1], x=s[y < -1], caption='well_sh',
            xlabel='sh', ylabel='depth',
            title=f'time = {time}')

    # 筛选储层区域的cell（y > -1）
    is_ok1 = y > -1
    x = x[is_ok1]
    z = z[is_ok1]

    def show_ca(idx, name):
        """绘制储层区域标量场的二维云图"""
        p = as_numpy(model).cells.get(idx)
        p = p[is_ok1]
        tricontourf(
            x, z, p, caption=name, title=f'time = {time}',
            fname=make_fname(
                year, path.join(folder, name), '.jpg',
                'y'))
        return p

    # 绘制储层压力和温度云图
    show_ca(-12, 'pressure')
    show_ca(model.get_cell_key('temperature'), 'temperature')

    fv_all = fv_all[is_ok1]

    def show_m(idx, name):
        """绘制储层区域某流体组分饱和度的二维云图"""
        v = as_numpy(model).fluids(*idx).vol
        v = v[is_ok1]
        tricontourf(
            x, z, v / fv_all, caption=name,
            title=f'time = {time}',
            fname=make_fname(
                year, path.join(folder, name), '.jpg',
                'y'))

    # 绘制CH4气相和水合物饱和度云图
    show_m([0], 'ch4')
    show_m([2, 0], 'ch4_hyd')

    # 显示生产曲线（累计产量和产气速率）
    if monitor is not None:
        monitor.plot_prod(
            index=0, caption='ch4_prod',
            fname=make_fname(
                year, path.join(folder, 'ch4_prod'),
                '.jpg', 'y'))
        monitor.plot_rate(
            index=0, caption='ch4_rate',
            fname=make_fname(
                year, path.join(folder, 'ch4_rate'),
                '.jpg', 'y'))


def solve(model, time_forward=3600.0 * 24.0 * 365.0 * 10, folder=None,
          day_save=30.0):
    """
    求解给定的渗流模型，并在求解过程中自动保存数据和绘制结果。

    求解过程使用共轭梯度法（ConjugateGradientSolver）求解线性方程组，
    通过GuiIterator控制迭代步进，同时自动保存模型快照和cell数据。

    参数:
        model (Seepage): 需要求解的渗流模型
        time_forward (float): 向前求解的时间长度，默认10年（单位：秒）
        folder (str, optional): 数据保存根文件夹，None表示不保存
        day_save (float): 数据保存的时间间隔，默认30天
    """
    assert isinstance(model, Seepage)
    if folder is not None:
        print_tag(folder)
        print(f'Solve. folder = {folder}')
        if gui.exists():
            gui.title(f'Data folder = {folder}')

    # 执行迭代：通过GuiIterator封装迭代和绘图
    iterate = GuiIterator(
        tfc.iterate,
        lambda: plot_cells(
            model, folder=path.join(folder, 'figures')))

    # 线性求解器（共轭梯度法，精度1e-15）
    solver = ConjugateGradientSolver(tolerance=1.0e-15)

    # 自动保存模型状态（按天数的间隔）
    save_model = SaveManager(
        folder=path.join(folder, 'models'),
        dtime=day_save,
        get_time=lambda: tfc.get_time(model) / (24 * 3600),
        save=model.save, ext='.seepage', time_unit='d',
        always_save=False)

    # 自动保存cell数据（按天数的间隔）
    save_cells = SaveManager(
        folder=path.join(folder, 'cells'),
        dtime=day_save,
        get_time=lambda: tfc.get_time(model) / (24 * 3600),
        save=lambda name: tfc.print_cells(name, model),
        ext='.txt', time_unit='d', always_save=False)

    # 最终停止时的模拟时间
    time_max = time_forward + tfc.get_time(model)

    # 主迭代循环
    while tfc.get_time(model) < time_max:
        iterate(model, solver=solver)  # 执行一步迭代
        save_model()                    # 保存模型（按需）
        save_cells()                    # 保存cell数据（按需）
        step = tfc.get_step(model)
        if step % 10 == 0:
            time = time2str(tfc.get_time(model))
            dt = time2str(tfc.get_dt(model))
            print(f'step = {step}, dt = {dt}, time = {time}')


def execute(folder=None, time_forward=3600 * 24 * 365 * 20, **kwargs):
    """
    执行完整的建模和计算流程（创建模型 + 求解计算）。

    参数:
        folder (str, optional): 数据保存文件夹
        time_forward (int): 模拟时间长度，默认20年（单位：秒）
        **kwargs: 传递给create_model的其他参数
    """
    model = create_model(**kwargs)
    print(model)
    solve(model=model, time_forward=time_forward, folder=folder, day_save=1.0)


def _test3():
    """
    测试用例3：执行case_1的建模和计算。
    结果保存到 'res_well/case_1' 文件夹。
    """
    gui.execute(lambda: execute(folder=opath('res_well', 'case_1')),
                close_after_done=False)


def case_2():
    """
    示例case_2：执行另一组参数的建模和计算。
    结果保存到 'res_well/case_2' 文件夹。
    """
    gui.execute(lambda: execute(folder=opath('res_well', 'case_2')),
                close_after_done=False)


if __name__ == '__main__':
    _test3()
