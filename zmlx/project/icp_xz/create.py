from icp_xz.ini import create_ini
from zml import Interp1, SeepageMesh
from zmlx.alg.has_cells import get_pos_range
from zmlx.config import seepage
from zmlx.config.icp.fludefs import create_fludefs
from zmlx.config.icp.reactions import create_reactions
from zmlx.kr.create_krf import create_krf
from zmlx.plt.plotxy import plotxy
from zmlx.ui import gui
from zmlx.utility.PressureController import PressureController
from zmlx.utility.SeepageCellMonitor import SeepageCellMonitor


def create(space: dict, mesh, injectors=None,
           p_prod=10e6, pos_prod=None, perm=None,
           gr=None, kr=None, gravity=None,
           dist=None,  # 决定了流体和固体换热的距离.
           operations=None,
           s=None,  # 初始饱和度.
           heat_cond=None,
           z_min=None, z_max=None, keys=None,
           temp_max=None,  # 液态水允许的最高的温度
           **kwargs):
    """
    建立模型工作区(space).
        包含了模型求解所有必须的数据.
    其中:
        z_min和z_max为储层的范围(区别于上下盖层).
    注意:
        在计算刚开始时: 1. 注入点开启. 2. 生产井关闭.
    """
    assert isinstance(mesh, SeepageMesh)

    if gr is None:
        # 根据孔隙度来计算渗透率
        x, y = create_krf(faic=0.02, n=3.0, k_max=100,
                          s_max=2.0, count=500)

        # 创建插值
        gr = Interp1(x=x, y=y)

        # 绘图
        if gui.exists():
            plotxy(x, y, caption='gr')

    # 生成关键词.
    #       不再对固体进行特殊处理 (当作普通的流体对待. )
    kw = dict(fludefs=create_fludefs(),
                     reactions=create_reactions(temp_max=temp_max),
                     gr=gr,
                     has_solid=False,  # 将固体视为特殊的流体
                     **kwargs)

    ini = create_ini(perm=perm, dist=dist, s=s,
                     heat_cond=heat_cond,
                     z_min=z_min, z_max=z_max)

    # 位置的范围
    z_btm, z_top = get_pos_range(mesh, 2)

    def get_denc(x, y, z):
        if abs(z - z_btm) < 0.1 or abs(z - z_top) < 0.1:
            return 1e20
        else:
            return 4e6

    # 原本没有设置上下的温度边界
    ini['denc'] = get_denc

    # 初始场
    kw.update(**ini)

    # 重力(默认为0)
    if gravity is None:
        gravity = [0, 0, -10]

    # 限定时间步长
    kw.update(dict(dt_max=3600.0 * 24.0 * 10.0,
                          gravity=gravity,
                          keys=keys  # 使用预定义的keys
                          ))

    # 创建模型
    model = seepage.create(mesh=mesh, **kw)

    if kr is None:
        x, y = create_krf(faic=0.05, n=2.0, count=300)
        kr = Interp1(x=x, y=y)
        # 绘图
        if gui.exists():
            plotxy(x, y, caption='kr')

    # 设置各种流体默认的相渗
    model.set_kr(kr=kr)

    # 找到模型的范围
    x_min, x_max = get_pos_range(mesh, 0)
    z_min, z_max = get_pos_range(mesh, 2)

    # 添加注热
    ca = seepage.cell_keys(model)

    # 注入点(injector为创建的参数)
    if injectors is not None:
        for injector in injectors:
            kw = dict(radi=3, ca_mc=ca.mc, ca_t=ca.temperature,
                             value=1.0e3
                             )  # 这些参数会被后续给定的injector参数update
            if injector is not None:
                kw.update(injector)  # 覆盖默认的参数
            pos = kw.get('pos', None)
            assert len(pos) == 3
            model.add_injector(**kw)

    # 降压生产的点的位置
    #       (在y大于0，即连接到裂缝介质一侧)
    if pos_prod is None:
        pos_prod = [x_min,
                    2.0,  # 默认的y坐标
                    (z_min + z_max) / 2]
    assert len(pos_prod) == 3

    # 用以生产的cell的id
    id_prod = model.get_nearest_cell(pos_prod).index
    assert id_prod < model.cell_number

    # 添加虚拟cell用于生产
    # 特别注意:
    #    这里的两个cell共享同一个坐标位置，因此，在后续绘图等处理的时候，
    #    需要将最后一个cell排除;
    assert 1e6 <= p_prod <= 50e6
    virtual_cell = seepage.add_cell(model, pos=pos_prod,
                                    porosity=1.0e5,
                                    pore_modulus=100e6,
                                    vol=1.0,
                                    temperature=350.0,
                                    p=p_prod,
                                    s={'ch4': 1},
                                    )

    # 虚拟的face (最后一个face)
    #       todo:
    #        注意，这里虽然添加了生产井，但是默认将它的面积设置为0，即初始没有打开
    seepage.add_face(model, virtual_cell,
                     model.get_cell(id_prod),
                     heat_cond=0,
                     perm=1.0e-14,
                     area=0.0,
                     length=1.0)

    # 创建压力控制
    pre_ctrl = PressureController(virtual_cell,
                                  t=[0, 1e10],
                                  p=[p_prod, p_prod])

    # 添加一个单元的监视，以输出生产曲线
    monitor = SeepageCellMonitor(get_t=lambda: seepage.get_time(model),
                                 cell=(virtual_cell, pre_ctrl))

    # 更新space
    space.update({'model': model, 'pre_ctrl': pre_ctrl,
                  'monitor': monitor})

    # 迭代的时候执行的额外的操作
    if operations is not None:
        space['operations'] = operations
