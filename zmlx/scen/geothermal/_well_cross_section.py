"""水平井一个横截面附近的**取热建模**（``create`` / ``solve``）.

网格在 ``_mesh.py``（``mesh_xz``）、流体在 ``_fludefs.py``（``create_fludefs``）、
绘图在 ``_show.py``（``show``），建模与求解在本文件 —— 算例（``cases/case_02.py``）
只负责把它们串起来。

计算域是一张 **x–z 剖面**（y 方向只有一层），井是其中一个单元：把该单元与相邻
单元的导流面积按井径收缩，井里取热，周围岩石向它传热。

模型要点见 :func:`create` 的文档与 ``cases/case_02.py`` 文件头的说明。
"""

import math
import os

from zmlx import Seepage, SeepageMesh, point_distance, tfc
from zmlx.scen.geothermal._fludefs import create_fludefs
from zmlx.scen.geothermal._mesh import equivalent_area, get_average_area, mesh_xz
from zmlx.system import warn

def _clamp_heat_cond(value):
    """把岩石热导率**截断**到 ``[0.01, 100]`` W/(m·K).

    Args:
        value: 岩石热导率（W/(m·K)）。传场时请用 :func:`_wrap_heat_cond`。

    Returns:
        float: 截断后的值 —— 越界取边界值，**不报错**。

    Raises:
        ValueError: ``value`` 无法转成数值（不是「越界」——越界是截断）。

    Note:
        区间取的依据：常见岩石 / 土的热导率大致在 ``0.1``（干砂、泥岩）到
        ``5``（石英岩、花岗岩）之间，少数高导热材料可到几十；
        而 ``1e-3`` 量级以下（接近真空隔热）在地热取热问题里没有物理意义。
        太小的值会让「岩石 → 井」的换热几乎停滞（温度看似不变），
        太大的值会让时间步剧烈收缩 —— 两者都更像「单位填错了」而不是真实工况，
        所以给一个宽但有限的区间，主要挡住 0、负数、以及量纲写错这类误填。
    """
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            '岩石热导率必须是数值或 f(x, y, z) 形式的场，当前为 {0!r}'.format(value)) from None
    return min(max(v, 0.01), 100.0)


def _wrap_heat_cond(field):
    """把「热导率场」包一层，使**每次求值**都截断到允许范围内.

    Args:
        field: 场 ``f(x, y, z) -> 数值``。

    Returns:
        callable: 新的场，返回值已截断到 ``[0.01, 100]``。

    Note:
        传场时无法在建模前枚举全部坐标，所以把截断放进回调里 —— 开销是一次比较，
        但保证了不管场在哪个位置返回什么，进入模型的热导率都在合法区间内。
    """
    def wrapped(x, y, z):
        """按坐标求值热导率，并把结果截断到允许范围内."""
        return _clamp_heat_cond(field(x, y, z))

    return wrapped


def create(
    *,
    jx=100,
    jz=100,
    xr=None,
    zr=None,
    well_pos=None,
    well_d=None,
    rock_density=None,
    rock_heat_capacity=None,
    rock_heat_cond=None,
    perm=None,
    porosity=None,
    reservoir_temp=None,
    well_temp=None,
    dt_max=None,
):
    """
    创建井截面取热模型。

    Args:
        jx: x 方向的网格数量。
        jz: z 方向的网格数量。
        xr: **x 方向的计算域范围** ``(x_min, x_max)``（米），默认 ``(-50, 50)``。
            传更长的序列则当作网格节点位置（交由 :func:`mesh_xz` 处理，
            可用于井附近的局部加密）。
        zr: **z 方向的计算域范围** ``(z_min, z_max)``（米），默认 ``(-50, 50)``。
            规则同 ``xr``。
        well_pos: 井在 x–z 平面上的位置 ``(x, z)``，默认 ``(0.0, 0.0)``；
            会取离它最近的单元作为井单元。
        well_d: 井筒直径（m），默认 ``0.2``。井单元的每条相邻面会按它收缩导流面积
            （先用 :func:`equivalent_area` 求井筒截面与该面之间的等效面积，
            再用 :func:`get_average_area` 与两侧各半段长度合成）。
        rock_density: 岩石密度（kg/m³），默认 ``2650``（花岗岩典型值）。
            **可以是场**：传 ``f(x, y, z) -> float`` 则逐单元按坐标取值。
        rock_heat_capacity: 岩石比热（J/(kg·K)），默认 ``790``（花岗岩典型值）。
            **可以是场**：传 ``f(x, y, z) -> float`` 则逐单元按坐标取值。
        rock_heat_cond: 岩石热导率（W/(m·K)），默认 ``3.0``（花岗岩典型值）。
            **可以是场**：传 ``f(x, y, z) -> float``。⚠️ 与另两个物性参数不同，
            它**按面**取值（每个面调用一次），传场时可用来表达各向异性的分层导热。
            ⚠️ 取值会被**截断**到 ``[0.01, 100]`` W/(m·K)：超出即取边界值、
            不报错 —— 理由见下面那条 ⚠️。
        perm: 渗透率（m²），默认 ``1e-12``（约 1 Darcy）。
            **可以是场**：传 ``f(x, y, z) -> float``。⚠️ **按面**取值（每个面调用一次），
            坐标是该面的位置 —— 想让「裂隙」只出现在某些面附近时正是这样写的。
        porosity: 孔隙度（无量纲，``0 < porosity < 1``），默认 ``0.2``。
            它决定单元里流体所占的孔隙体积，从而影响热容与流动的响应速度。
            **可以是场**：传 ``f(x, y, z) -> float`` 则逐单元按坐标取值。
        reservoir_temp: **原始储层温度**（K），默认 ``320``。即井以外整个岩石区域的
            初始温度 —— 说「地热储层有多热」用的就是它。
        well_temp: **井底温度**（K），默认 ``280``。井单元（井筒所在的那一个单元）的
            初始温度；它低于储层温度，于是热量从岩石持续流向井，形成取热过程。
        dt_max: 最大时间步长（s）。给定时调 ``tfc.set_dt_max(model, dt_max)``；
            默认 ``None`` 表示不改动。

    Note:
        **「标量或场」的通用写法**：上表中标注「可以是场」的 5 个参数，既接受一个数
        （``rock_density=2650``），也接受一个函数 ``f(x, y, z) -> 数值``。
        于是「上软下硬」「井附近渗透率更高」这类非均质情形不必改函数签名::

            # 随深度变密、变致密的花岗岩
            create(rock_density=lambda x, y, z: 2400 - 0.5 * z)

        ⚠️ **按单元 vs 按面**：``denc`` / ``porosity`` / ``temperature`` 一类
        是**逐单元**求值（每单元一次），而 ``perm`` / ``heat_cond`` 是**逐面**求值
        （每面一次，坐标为该面位置）—— 由 ``tfc.create`` 内部决定，不是本函数的约定。
        写场时别假设它一定按单元调用。

    Returns:
        Seepage: 配好的渗流-热耦合模型。井单元上同时设了：

            - 井单元初始温度 ``well_temp``（其余区域 ``reservoir_temp``）；
            - 体积热容放大 ``1e6`` 倍（当作恒温储热体）；
            - 文本 ``well_cell_id`` 记下井单元的下标，供 :func:`update_power` 使用。

    ⚠️ **``well_pos`` 要落在 ``xr`` / ``zr`` 范围内**：井单元是按「离 ``well_pos``
        最近的单元」找的，位置在域外时会挑到边界上那个单元（不报错），
        结果与直觉不符。默认的 ``(-50, 50)`` 与 ``(0, 0)`` 是配好的。

    ⚠️ 本函数的 ``xr`` / ``zr`` 默认值（``(-50, 50)``）与 :func:`mesh_xz` 的默认值
        （``(-0.6, 0.6)`` / ``(-1, 1)``）**不同** —— 后者只是通用默认，
        井截面算例用前者。

    ⚠️ **热导率越界是「截断」不是「报错」**：``rock_heat_cond`` 超出
        ``[0.01, 100]`` W/(m·K) 时会被改成边界值（传场时**逐次求值**都截断）。
        理由是越界几乎都是单位填错（0、负数），截断能让求解继续跑完，
        比中途抛异常更省事；代价是**不告诉你改过** —— 若取值可疑，请自己先核对。

    ⚠️ ``dist`` 传的是**函数**：井单元 ``0.01``、其余单元 ``0.2``（流体与固体之间的
        换热距离，不是热扩散率）—— 单位/语义请以 ``tfc.create`` 的 ``dist`` 文档为准，
        取值理由见 ``dist`` 自己的说明。
    """
    if xr is None:
        xr = (-50, 50)

    if zr is None:
        zr = (-50, 50)

    yr = (-0.5, 0.5)  # 后续为1
    mesh: SeepageMesh = mesh_xz(jx=jx, jz=jz, xr=xr, yr=yr, zr=zr)

    if well_pos is None:
        well_pos = (0.0, 0.0)

    # 井在x-z平面的坐标
    well_x, well_z = well_pos[0], well_pos[1]

    # 找到最为接近的Cell，后续，让这个Cell来接收产出的热量
    cell = mesh.get_nearest_cell(pos=[well_x, (yr[0] + yr[1]) / 2, well_z])
    if cell is None:
        raise RuntimeError(f"在 pos = {well_pos} 没有找到Cell")

    if well_d is None:
        well_d = 0.2

    # 根据井筒的直径，修改这个cell和周边cell的联系
    for f in cell.faces:
        s1 = equivalent_area(0.25 * math.pi * well_d * 1.0, f.area)
        f.area = get_average_area(s1, 0.5, f.area, 0.5)

    well_cell_pos = cell.pos

    def is_well_cell(x, y, z):
        """判断给定位置是否就是井所在的单元（按坐标与井单元中心的距离判等）。

        ``tfc`` 的温度 / 热容回调只给坐标、不给单元下标，所以用「离井单元中心
        足够近」来认它；阈值 ``1e-5`` 远小于单元尺寸，不会误认到相邻单元。
        """
        return point_distance(well_cell_pos, [x, y, z]) < 1.0e-5

    # 需要检查这些取值的合理性
    if rock_density is None:
        rock_density = 2650

    if rock_heat_capacity is None:
        rock_heat_capacity = 790

    if rock_heat_cond is None:
        rock_heat_cond = 3.0

    # 热导率截断到 [0.01, 100] W/(m·K)：
    # 越界多半是「单位填错了」（0、负数、或把 W/(m·K) 写成了别的量纲），
    # 截断比报错省事，同时也不至于让离谱的值把求解拖成怪结果。
    if callable(rock_heat_cond):
        # 场：包一层，让**每次求值**都截断（开销是一次比较）
        rock_heat_cond = _wrap_heat_cond(rock_heat_cond)
    else:
        rock_heat_cond = _clamp_heat_cond(rock_heat_cond)

    if reservoir_temp is None:
        reservoir_temp = 320.0

    if well_temp is None:
        well_temp = 280.0

    def eval_field(value, x, y, z):
        """把「标量或场」统一成当前坐标下的**数值**.

        Args:
            value: 标量（``2650``），或场（``f(x, y, z) -> 数值``）。
            x, y, z: 当前单元 / 面的坐标。

        Returns:
            float: 该坐标下的取值。
        """
        return value(x, y, z) if callable(value) else value

    def get_denc(x, y, z):
        """获取体积热容（密度乘以比热），单位 J/(m³·K).

        ⚠️ 必须写成函数、且**在函数体内**才把两个场相乘：``rock_density`` /
        ``rock_heat_capacity`` 都可以是 ``f(x, y, z)``，若在 ``create`` 的函数体里
        先做 ``rock_density * rock_heat_capacity``，传函数进来就会直接
        ``TypeError: unsupported operand type(s) for *``。
        """
        v = eval_field(rock_density, x, y, z) * eval_field(rock_heat_capacity, x, y, z)
        # 井单元的体积热容放大 1e6 倍，当作恒温储热体
        return v * 1e6 if is_well_cell(x, y, z) else v

    def get_temp(x, y, z):
        """获取初始温度分布：井单元取 ``well_temp``，其余区域取 ``reservoir_temp``.

        ⚠️ 两者都是**数值**（K），不支持传场 —— 要空间变化的初始温度，
        请直接改这里，而不要试图把函数传给这两个参数。
        """
        if is_well_cell(x, y, z):
            return well_temp
        else:
            return reservoir_temp

    def dist(x, y, z):
        """流体和固体之间的换热距离（m），**按单元给不同值**.

        - 井单元：``0.01`` —— 井筒尺寸远小于网格，取更小的距离让「岩石 → 井」
          这一跳的换热更强，等价于给井筒附近更高的换热系数；
        - 其余单元：``0.2``。

        ⚠️ 它的语义是**换热距离**，不是热扩散率 —— 见 ``create`` 文档里那条说明。
        """
        if is_well_cell(x, y, z):
            return 0.01
        else:
            return 0.2

    if perm is None:
        perm = 1e-12

    if porosity is None:
        porosity = 0.2

    # 使用tfc（热-流-化学耦合）框架创建模型
    model: Seepage = tfc.create(
        mesh=mesh,
        cfl=0.5,  # 决定dt
        fludefs=create_fludefs(),
        porosity=porosity,  # 孔隙度
        p=5e6,  # 初始压力 5 MPa
        s=1.0,  # 初始饱和度为 1（完全饱和水）
        perm=perm,
        temperature=get_temp,
        denc=get_denc,  # 体积热容（密度×比热）；用函数形式以支持空间变化
        gravity=[0, 0, -10],  # 重力加速度，沿z轴负方向（竖直向下），大小为10 m/s^2
        dist=dist,  # 流体与固体之间的换热距离（**不是**热扩散率）
        heat_cond=rock_heat_cond,  # 岩石热导率
    )

    tfc.set_fa(
        model, 0, "z0", tfc.get_z(model)
    )  # 设置辅助变量z0为单元格的z坐标，用于追踪流体运动轨迹

    # 每一步，都调用update_power
    tfc.step_iteration.add_setting(model, name="update_power", args=["@model"])

    # 将作为well的cell的ID存储，方便后续使用
    well_cell = None
    for cell in model.cells:
        if is_well_cell(*cell.pos):
            well_cell = cell
            break
    assert well_cell is not None
    model.set_text(key="well_cell_id", text=f"{well_cell.index}")

    if dt_max is not None:
        tfc.set_dt_max(model, dt_max)

    return model


def update_power(model: Seepage):
    """求解的**每一步**调用一次：算出井单元的取热功率并累积到 ``time2pow``.

    由 ``tfc.step_iteration`` 的 ``update_power`` 槽在每次迭代时调起（见 :func:`create`），
    也作为 ``tfc.solve`` 的 ``slots`` 注册。

    能量按「井单元的温度 × 该单元的热容属性 ``mc``」估计：``e = T × mc``。
    与上一次记下的 ``well_e`` / ``well_t`` 做差，

    .. code-block:: text

        power = (e_now - e_prev) / (t_now - t_prev)

    ⚠️ **首次调用只存值、不计算功率**（那时还没有 ``well_t`` / ``well_e``）。

    ⚠️ 时间与能量用 :func:`repr` 存进模型文本（``well_t`` / ``well_e`` / ``time2pow``）：
    它保证 ``float(s)`` 与原值**逐位相同**，下一次读回来做差不会引入额外误差。
    不要改回 ``f"{x:.10f}"`` —— 那是定点格式，很小的数会被写成 ``0.0000000000``。

    ⚠️ 已知边界：若 ``t_now == t_prev``（时间没前进），会抛 ``ZeroDivisionError``。

    Args:
        model: 要统计的模型（其文本键中带有 ``well_cell_id``）。
    """
    idx = int(model.get_text(key="well_cell_id"))
    cell: Seepage.Cell = model.get_cell(idx)
    ca_t = model.get_cell_key(key="temperature")
    ca_mc = model.get_cell_key(key="mc")

    t1 = tfc.get_time(model)
    e1 = cell.get_attr(ca_t) * cell.get_attr(ca_mc)

    # 存储的井单元的时间、和对应时间的能量
    t0 = model.get_text(key="well_t")
    e0 = model.get_text(key="well_e")

    # 存储能量和时间.
    # ⚠️ 用 repr 而不是 f"{x:.10f}"：后者是**定点**格式，只保留小数点后 10 位 ——
    #    很小的数（如 1.2e-12）会被写成 "0.0000000000"，精度整个丢掉；
    #    大数也会丢掉末位。repr 是 Python 保证「float(s) == 原值」的最短表示，
    #    既能无损往返（下一次读回来算 power 不会引入额外误差），又不会写出多余的尾数。
    model.set_text(key="well_t", text=repr(t1))
    model.set_text(key="well_e", text=repr(e1))

    if len(t0) > 0 and len(e0) > 0:
        t0 = float(t0)
        e0 = float(e0)
        power = (e1 - e0) / (t1 - t0)

        time2pow = model.get_text(key="time2pow")
        if len(time2pow) > 0:
            time2pow = eval(time2pow)
            assert isinstance(time2pow, list)
        else:
            time2pow = []
        time2pow.append([t1, power])
        model.set_text(key="time2pow", text=repr(time2pow))


def _power_ylim(x, y):
    """按数据算纵轴范围，但**忽略最开始 10 天**的数据点.

    Args:
        x: 时间序列（年）。
        y: 对应的采热功率序列（瓦）。

    Returns:
        tuple: ``(0, ymax)``；``ymax`` 取「10 天之后」那段的最大值。
        若所有点都还在前 10 天内（或为空），则退化为全部数据的最大值；
        全为空或最大值非正时返回 ``None``（表示交给 matplotlib 自动缩放）。

    Note:
        ⚠️ **为什么要跳过前 10 天**：求解刚开始时井单元与周围岩石的温差最大，
        采热功率会出现一个很高的**起始瞬态尖峰**（可达稳态的数倍）。
        把那个尖峰算进 ``ylim`` 会把后面整个稳态段压成一条贴底的线，
        曲线反而看不出变化。

        ⚠️ 数据点仍**全部画出**（包括尖峰）：只是纵轴按「10 天之后」定标，
        尖峰会超出画面顶部 —— 这是刻意的取舍，因为关心的是长期取热能力。
    """
    # 10 天换算成年
    after = 10.0 / 365.0
    values = [p for t, p in zip(x, y) if t >= after]
    if len(values) == 0:
        # 全都还在前 10 天内（例如只跑了几天的短算例）：只能按全部数据定标
        values = list(y)
    if len(values) == 0:
        return None
    ymax = max(values)
    if not ymax > 0:
        return None
    return 0, ymax


def _show_power_curve(x, y):
    """画「采热功率 ~ 时间」曲线，纵轴按数据定标（跳过起始 10 天）.

    Args:
        x: 时间（年）。
        y: 对应的采热功率（瓦）。

    Note:
        ``ylim`` 经 ``show_xy(x, y, ylim=...)`` 传下去，调用链是
        ``show_xy`` → ``plot_on_axes`` → ``plot_on_figure`` → ``add_subplot``；
        后者把 ``ylim`` 从 ``**kwargs`` 里**显式取出来**执行 ``ax.set_ylim(ylim)``
        （见 ``zmlx/plt/on_figure/_subplot.py`` 的 ``add_subplot`` 签名与函数体），
        所以它不会被当成 ``ax.plot`` 的参数。
    """
    from zmlx.plt import show_xy

    ylim = _power_ylim(x, y)
    opts = dict(caption='采热功率', xlabel='时间 / 年', ylabel='功率 / 瓦')
    if ylim is not None:
        opts['ylim'] = ylim
    show_xy(x, y, **opts)


def _is_inside_package(path):
    """判断 ``path`` 是否落在 **zmlx 包目录内部**（含包目录本身）.

    用于 :func:`solve` 的 ``folder``：**不往源码目录里写计算结果**。
    一次求解会写出成百上千个 ``.seepage`` / ``.txt`` 快照，
    留在包里既污染发布内容、也会被误提交进版本库。

    Args:
        path: 待判断的路径，可以是相对路径（按当前工作目录解释）。

    Returns:
        bool: 在包内返回 ``True``。

    Note:
        用 ``os.path.realpath`` + ``os.path.commonpath`` 比较，而不是字符串
        ``startswith``：后者会把 ``zmlx/../zmlx/sub`` 这类带 ``..`` 的路径、
        以及同名前缀目录（``zmlx_evil``）判错。``realpath`` 还会解析符号链接，
        于是「指向包内的软链接」同样被拦住。
    """
    try:
        import zmlx

        root = os.path.realpath(os.path.dirname(zmlx.__file__))
        target = os.path.realpath(path)
        return os.path.normcase(os.path.commonpath([target, root])) == os.path.normcase(
            root
        )
    except (ValueError, OSError):
        # commonpath 在不同盘符时抛 ValueError；取不到路径时**按包外处理**
        # （宁可放行也不误拦用户真正的输出目录）
        return False


def solve(model, jx, jz, time_max=3600 * 24 * 365 * 10, folder=None):
    """求解井截面取热模型，并在求解过程中实时绘图.

    绘图回调（``extra_plot``）每步做两件事：

    1. :func:`zmlx.scen.geothermal._show.show` 画当前状态（叠加以井单元为中心、
       半径 2 m 的黑色参考圆）；
    2. 若已有 ``time2pow`` 记录，用 :func:`_show_power_curve` 画「采热功率」随时间的
       曲线（横轴由秒换算成年）；纵轴按数据定标，但**算最大值时跳过最开始 10 天**，
       以免起始瞬态的高尖峰把稳态段压成一条贴底的线。

    Args:
        model: :func:`create` 建好的模型。
        jx: x 方向网格数量（与 :func:`create` 传入的一致，用于把单元数据重塑成
            ``[jx, jz]`` 矩阵作图）。
        jz: z 方向网格数量。
        time_max: 最大求解时间（秒），默认 ``3600*24*365*10``（约 10 年）。
        folder: 结果保存目录，原样传给 ``tfc.solve(folder=...)``。给定时会把
            模型快照与单元数据存到该目录下（``models/`` / ``cells/`` 等）。
            ``None``（默认）表示不保存，只在内存里算。

    ⚠️ **``folder`` 若落在 zmlx 包目录内部，会被强制当成 ``None``**（不保存）：
        求解会写出大量快照，不该混进源码 / 发布目录。判定见 :func:`_is_inside_package`。
        这条限制只在 `folder` 指向包内时生效，包外路径照常保存。

    Note:
        功率的收集由 ``slots={"update_power": update_power}`` 完成 ——
        与 :func:`create` 里注册的 ``tfc.step_iteration`` 槽是同一件事的两处登记。
    """
    from zmlx.scen.geothermal._show import show

    if folder is not None and _is_inside_package(folder):
        # ⚠️ 明确告警而不是静默改写：用户以为在保存、实际没保存，是最难查的那类问题。
        warn(
            "结果保存目录 {0!r} 位于 zmlx 包目录内部，已改为不保存（folder=None）——"
            "计算数据不该写进代码/发布目录。请改到包外的目录。".format(folder),
            stacklevel=2,
        )
        folder = None

    def show_all():
        """每步的绘图回调：先画状态图，再画采热功率曲线."""
        idx = int(model.get_text(key="well_cell_id"))
        cell: Seepage.Cell = model.get_cell(idx)

        show(
            model,
            jx,
            jz,
            caption="实时状态",
            # 以井单元为中心、半径 2 m 的黑色参考圆
            circles=[(cell.pos[0], cell.pos[2], 2.0, "k-")],
        )
        time2pow = model.get_text(key="time2pow")
        if len(time2pow) > 0:
            time2pow = eval(time2pow)
            assert isinstance(time2pow, list)
            x = [t / (3600 * 24 * 365) for t, p in time2pow]
            y = [p for t, p in time2pow]
            _show_power_curve(x, y)

    tfc.solve(
        model,
        folder=folder,
        time_max=time_max,
        extra_plot=show_all,
        slots={"update_power": update_power},
    )


if __name__ == "__main__":
    print(create(jx=100, jz=100))
