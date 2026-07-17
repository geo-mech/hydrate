# ** desc = '基于井筒换热的地热开发模拟(存在尚未发现的bug)'
"""
井筒换热地热开发模拟（井筒-储层耦合换热）。

物理问题：
    模拟地热开发中，冷水通过井筒注入、在储层中加热后产出的全过程。
    系统由两个耦合模型组成：
    1. 井筒模型（1D）：水沿井筒流动，与周围储层发生热交换
    2. 储层模型（2D圆柱）：高温岩体（初始200摄氏度），热量通过导热向井筒传递

耦合方式：
    在一个主循环中交替求解两个模型：
    1. 将储层温度赋给井筒（作为边界条件）
    2. 求解井筒内的流动与换热，得到流体温度分布
    3. 将井筒流体温度赋给储层（作为换热边界）
    4. 求解储层热传导，计算热量提取量

监测指标：
    - 输出功率（Power）：储层显热随时间的变化率
    - 出口温度（Outlet Temperature）：产出流体的温度

注意：本代码存在尚未发现的bug，供开发者排查和验证模型使用。
"""

from zmlx import *
from zmlx.seepage_mesh import create_wellbore


def create_well(rate_inj=None, temp_inj=None, heat_cond=2.0, dist=0.1):
    """
    创建井筒模型。

    构建一条沿x方向（0~100m）的一维井筒，水从井口注入，
    沿井筒流动过程中与周围储层发生热交换。

    参数：
        rate_inj: 注入速率 [m^3/s]，默认 1.0e-6 m^3/s
        temp_inj: 注入水温 [K]，默认 273.15+50 = 323.15K (50摄氏度)
        heat_cond: 井筒与储层间的等效导热系数 [W/(m.K)]，默认 2.0
        dist: 换热距离 [m]，默认 0.1

    返回：
        Seepage对象：井筒流动与换热模型
    """
    # 创建一维井筒网格：从 (0,0,0) 到 (100,0,0)，长度1m单元，截面积0.01m^2
    mesh = create_wellbore(trajectory=[[0, 0, 0], [100, 0, 0]],
                           length=1, area=0.01)
    # 井筒的总体积
    mesh_vol = mesh.volume
    # 将最后一个单元格体积设为极大值，作为虚拟出口单元
    mesh.get_cell(-1).vol = 1e6

    if rate_inj is None:
        rate_inj = 1.0e-6

    assert 0 < rate_inj <= 1

    # 将导热系数封装为场函数（支持空间变化的物性）
    heat_cond = Field(heat_cond)

    # 定义流体属性：水，密度1000 kg/m^3，粘度0.001 Pa.s，比热4200 J/(kg.K)
    fludefs = [FluDef(name='h2o', den=1000, vis=0.001,
                      specific_heat=4200.0)]

    if temp_inj is None:
        temp_inj = 273.15 + 50  # 默认注入50摄氏度的水

    # 创建水的单相流动计算模型
    model = tfc.create(
        mesh=mesh,
        cfl=0.8,
        dt_max=3600 * 24.0,
        fludefs=fludefs,
        porosity=1,
        pore_modulus=200e6,
        heat_cond=heat_cond,
        p=1e6,
        s=1.0,
        denc=1e20,  # 设置得非常大，从而确保井筒固体骨架温度不变
        dist=dist,  # 换热的距离（控制流体与固体间的换热效率）
        temperature=temp_inj,  # 初始温度
        perm=1e-11 * rate_inj / 1e-6,
        # 渗透率与注入速率成正比（当rate增大时同步增大）
        gravity=[0, 0, 0],  # 由于虚拟单元的存在，最好将重力设置为0
        # 禁用不需要的物理过程：密度更新、粘度更新、热辐射
        tags=['disable_update_den', 'disable_update_vis',
              'disable_ther'],
        warnings_ignored={'gravity'},
    )

    # 从第一个单元格设注入边界条件
    cell = model.get_cell(0)
    flu = cell.get_fluid(0).get_copy()
    flu.set_attr(index=model.reg_flu_key('temperature'), value=temp_inj)
    model.add_injector(cell=cell,
                       value=rate_inj,
                       fluid_id='h2o',
                       flu=flu
                       )

    # 标记哪些单元格参与井-储换热交换（最后一个虚拟单元不参与）
    swap = [True for _ in range(model.cell_number)]
    swap[-1] = False
    model.set_text('swap', swap)

    # 配置求解选项：计算到流体置换一遍所需的时间
    tfc.set_solve(model, time_forward=mesh_vol / rate_inj)

    return model


def solve_well(model, folder=None, gui_iter=None,
               **kwargs):
    """
    求解井筒模型。

    在求解过程中实时绘制井筒沿程的压力和流体温度分布。

    参数：
        model: Seepage对象（井筒模型）
        folder: 数据保存目录
        gui_iter: GUI迭代器
        **kwargs: 传递给 tfc.solve 的其他参数
    """
    swap = eval(model.get_text('swap'))

    def plot():
        """
        绘制井筒沿程压力和温度的实时曲线。
        """
        if gui.exists():
            title = f'time = {tfc.get_time(model, as_str=True)}'
            x = as_numpy(model).cells.x[swap]
            p = as_numpy(model).cells.pre[swap]
            plot_xy(x, p, caption='well_p', title=title)

            t = as_numpy(model).fluids(0).get(
                index=model.reg_flu_key('temperature'))[swap]
            plot_xy(x, t, caption='well_T', title=title)

    tfc.solve(model, extra_plot=plot,
              folder=folder, gui_iter=gui_iter, state_hint='well',
              **kwargs)


def create_res(well: Seepage, heat_cond=2.0):
    """
    创建储层模型（二维圆柱坐标系）。

    将井筒位置映射到圆柱坐标系中（x坐标映射为轴向，r为径向），
    并为每个井筒单元创建一个虚拟对应单元用于热交换。

    参数：
        well: Seepage对象（井筒模型，用于获取井筒轨迹和导热能力）
        heat_cond: 储层导热系数 [W/(m.K)]，默认 2.0

    返回：
        Seepage对象：二维储层热传导模型
    """
    # 创建圆柱网格：x方向0~100m分100段，径向0~50m分50段
    mesh = create_cylinder(
        x=np.linspace(0, 100, 100),
        r=np.linspace(0, 50, 50))

    # 获取井筒轨迹坐标和导热能力
    swap = eval(well.get_text('swap'))
    vx = as_numpy(well).cells.x[swap]
    vy = as_numpy(well).cells.y[swap]
    vz = as_numpy(well).cells.z[swap]
    # 获取井筒各单元格的导热能力（g_heat）
    vg = as_numpy(well).cells.get(index=well.reg_cell_key('g_heat'))[
        swap]

    i_swap = [False for _ in range(mesh.cell_number)]
    o_index = []
    # 将导热系数封装为场函数
    heat_cond = Field(heat_cond)

    # 为每个井筒单元在储层网格中创建虚拟对应单元
    for idx in range(len(vx)):
        x, y, z = vx[idx], vy[idx], vz[idx]

        c = mesh.add_cell()
        c.pos = [1e6, 0, 0]  # 设置虚拟位置（极远处），绘图时自动排除
        c.vol = 1e6  # 设置极大体积，确保其温度几乎不变

        # 建立虚拟单元与储层网格单元的连接（热交换通道）
        c2 = mesh.get_nearest_cell(pos=[x, y, z])
        f = mesh.add_face(c, c2)
        f.area = 0  # 面积暂设为0，后续通过设置g_heat来指定导热能力
        f.length = 1

        # 标记参与热交换的单元
        i_swap.append(True)  # 这些虚拟单元用于井-储热交换
        o_index.append(c2.index)

    # 创建储层热传导模型
    model = tfc.create(
        mesh=mesh,
        temperature=273.15 + 200.0,  # 初始温度200摄氏度 [K]
        denc=5.0e6,   # 体积热容 [J/(m^3.K)]
        heat_cond=heat_cond,
        cfl=0.5,
        dt_max=3600 * 24 * 10,  # 最大时间步长10天
    )

    # 设置井-储连接面的导热能力（从井筒模型继承）
    face_n0 = model.face_number - len(vx)
    for idx in range(len(vx)):
        model.get_face(face_n0 + idx).set_attr(model.reg_face_key('g_heat'),
                                               vg[idx])

    model.set_text('i_swap', i_swap)
    model.set_text('o_index', o_index)

    # 配置求解选项：只显示有效区域（mask排除虚拟单元）
    mask = tfc.get_cell_mask(model,
                             xr=[-1000, 1000])
    tfc.set_solve(model,
                  show_cells={'dim0': 0, 'dim1': 1,
                              'show_p': False,
                              'mask': mask},
                  time_forward=60 * 24 * 3600  # 默认前推60天
                  )
    return model


def get_res_heat(model: Seepage):
    """
    计算储层中的总显热。

    显热 = sum(温度 * 热容)，排除虚拟单元（仅统计真实储层部分）。

    参数：
        model: Seepage对象（储层模型）

    返回：
        float: 储层总显热 [J]
    """
    o_index = eval(model.get_text('o_index'))  # 虚拟单元索引，不统计其热量
    assert len(o_index) > 0
    temp = as_numpy(model).cells.get(model.reg_cell_key('temperature'))
    mc = as_numpy(model).cells.get(model.reg_cell_key('mc'))
    heat = temp * mc  # 每个单元格的显热
    # 排除最后几个虚拟单元（仅统计真实储层）
    heat = heat[0: model.cell_number - len(o_index)]
    return np.sum(heat)


def get_cell_t(model: Seepage):
    """
    获取储层中参与热交换的单元格温度。

    支持两种模式：
        - 储层模型：通过 o_index 获取与井筒直接连接的储层单元温度
        - 井筒模型：通过 swap 获取所有参与交换的单元格温度

    参数：
        model: Seepage对象

    返回：
        ndarray: 温度数组 [K]
    """
    buf = as_numpy(model).cells.get(index=model.reg_cell_key('temperature'))
    text = model.get_text('o_index')
    if len(text) > 0:
        # 储层模式：获取与井筒换热的储层单元温度
        o_index = eval(text)
        temp = [buf[i] for i in o_index]
        return np.array(temp)
    else:
        # 井筒模式：获取所有参与交换的单元温度
        swap = eval(model.get_text('swap'))
        return buf[swap]


def set_cell_t(model: Seepage, vt):
    """
    设置模型中参与热交换的单元格温度。

    用于将井筒温度赋给储层，或将储层温度赋给井筒。

    参数：
        model: Seepage对象
        vt: 温度数组 [K]，长度应与参与交换的单元格数一致
    """
    text = model.get_text('i_swap')
    if len(text) > 0:
        # 储层模式：使用 i_swap 标记（仅在储层模型中存在）
        swap = eval(text)
    else:
        # 井筒模式：使用 swap 标记
        swap = eval(model.get_text('swap'))
    buf = as_numpy(model).cells.get(index=model.reg_cell_key('temperature'))
    buf[swap] = vt
    as_numpy(model).cells.set(index=model.reg_cell_key('temperature'),
                              buf=buf)


def get_flu_t(model: Seepage):
    """
    获取井筒中流体的温度。

    参数：
        model: Seepage对象（井筒模型）

    返回：
        ndarray: 井筒流体温度数组 [K]
    """
    swap = eval(model.get_text('swap'))
    buf = as_numpy(model).fluids(0).get(index=model.reg_flu_key('temperature'))
    return buf[swap]


def test_1():
    """
    测试1：仅运行井筒模型。
    """
    solve_well(create_well(), time_max=1e10)


def test_2():
    """
    测试2：运行井筒-储层耦合模型（简化版）。
    """
    heat_cond = 2
    well = create_well(heat_cond=heat_cond, rate_inj=1.0e-6)
    res = create_res(well=well, heat_cond=heat_cond)
    swap = eval(res.get_text('swap'))
    vt = [300 for x in swap if x]
    set_cell_t(res, vt)
    tfc.set_solve(res,
                  time_forward=6000 * 24 * 3600
                  )
    tfc.solve(res)


def main(folder=None):
    """
    主函数：执行完整的井筒-储层耦合地热开发模拟。

    通过循环交替求解井筒和储层模型，模拟长达50年的地热开发过程。
    在每次迭代中：
        1. 同步时间
        2. 将储层温度赋给井筒
        3. 求解井筒流动换热
        4. 将井筒流体温度赋给储层
        5. 求解储层热传导
        6. 计算功率和出口温度
        7. 更新实时曲线

    参数：
        folder: 数据保存目录（可选）
    """
    def solve():
        heat_cond = 1
        well = create_well(heat_cond=heat_cond, rate_inj=20e-5, dist=0.01)
        res = create_res(well=well, heat_cond=heat_cond)

        gui_iter = GuiIterator()

        # 记录时间、功率和出口温度随时间的变化
        vtime, vpower, vtemp = [], [], []

        # 模拟50年
        while tfc.get_time(res) < 50 * 365 * 24 * 3600:
            tfc.set_time(well, tfc.get_time(res))  # 同步井筒和储层的时间

            # Step 1: 将储层温度赋给井筒
            set_cell_t(well, get_cell_t(res))
            # Step 2: 求解井筒内的流动与换热
            solve_well(well, folder=join_paths(folder, 'well'),
                       gui_iter=gui_iter)
            # Step 3: 将井筒流体温度赋给储层（热交换边界）
            set_cell_t(res, get_flu_t(well))

            # Step 4: 求解储层热传导
            energy0 = get_res_heat(model=res)
            time0 = tfc.get_time(res)
            tfc.solve(res, folder=join_paths(folder, 'res'),
                      gui_iter=gui_iter, state_hint='res')
            energy1 = get_res_heat(model=res)
            time1 = tfc.get_time(res)

            # 计算此时间段内储层释放热量的平均功率
            power = (energy0 - energy1) / (time1 - time0)
            vtime.append(time1 / (3600 * 24 * 365))  # 转换为年
            vpower.append(power)

            # 记录出口流体温度（井筒最后一个交换单元的温度）
            vtemp.append(get_flu_t(well)[-1])

            # 实时更新功率曲线和出口温度曲线
            plot_xy(vtime, vpower, caption='time2power', title='Power',
                    xlabel='Time/ year', ylabel='Power / W')
            plot_xy(vtime, vtemp, caption='time2temp',
                    title='Outlet Temperature',
                    xlabel='Time/ year',
                    ylabel='Temperature / K')

    gui.execute(func=solve)


if __name__ == '__main__':
    main()
