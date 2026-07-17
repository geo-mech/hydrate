# ** desc = '水平井注采。向水合物储层注入co2，并在另外一口水平井降压开发水合物'
"""
物理问题描述：本模型模拟一个双水平井系统——一口井注入CO2，另一口井降压开采CH4。
系统包含三个地质层：上覆层（overburden）、水合物储层（reservoir）、下伏层（underburden），
各层具有不同的渗透率属性。CO2从右侧井注入，通过置换反应促进CH4水合物分解；
左侧生产井通过降压（3MPa）开采释放的CH4气体。
建模方法：基于co2.py中的create和solve函数构建双井注采模型。
使用add_cell_face添加虚拟网格用于生产边界设定。模型考虑：
（1）不同地层的非均质渗透率（各向异性，水平/垂向渗透率比4:1）；
（2）初始水合物饱和度0.4的储层区域；
（3）热传导系数的空间变化（避免虚拟生产单元传热）；
（4）定时操作管理生产井的开启和关闭。
关键参数：co2_mass_rate（CO2注入速率，单位kg/s）、year_prod（生产年限，单位年）、
well_dist（井间距，单位m）、res_depth（储层深度，单位m）、
res_perm（储层渗透率，单位m²）、bound_perm（盖层/底层渗透率，单位m²）。
生产井以3MPa的恒定压力进行降压开采。
"""

from zmlx import tfc, Tensor3, Seepage
from zmlx.demo.hydrate.co2 import create, solve
from zmlx.io import opath
from zmlx.seepage_mesh import add_cell_face
from zmlx.seepage_mesh.xz_half import create_xz_half
from zmlx.tfc import timer
from zmlx.utility import GuiIterator


def execute(
        folder=None, co2_mass_rate=10.0 / (3600.0 * 24.0), year_prod=10.0, year_beg_inj=2.0, well_dist=60.0,
        res_depth=125.0, co2_temp=290.0, p_seabed=10e6, res_perm=20e-15, bound_perm=1.0e-15, dx=2.0, dz=2.0,
        **other_opts
):
    """
    执行双水平井CO2注入与CH4降压开采的联合模拟。

    本函数构建一个包含三口井（虚拟生产井+CO2注入井+CH4生产井）的二维注采模型。
    右侧注入CO2，左侧通过降压（3MPa恒定压力）开采甲烷水合物储层中的CH4。
    储层高度50m（res_depth±25m范围），上下分别为上覆层和下伏层，
    各层渗透率不同，且水合物层具有各向异性（水平/垂向渗透率比4:1）。
    CO2注入速率随时间变化（前2年不注入，然后开始注入，生产结束停止），
    生产井在指定时间后自动关闭。

    参数:
        folder (str, optional): 结果保存目录，默认None。
        co2_mass_rate (float): CO2注入质量速率，单位kg/s。默认值约0.000116 kg/s。
        year_prod (float): 总生产时间，单位年。默认值: 10.0年。
        year_beg_inj (float): 注入开始时间（从模拟开始），单位年。默认值: 2.0年。
        well_dist (float): 注采井间距（水平距离），单位m。默认值: 60.0m。
        res_depth (float): 储层中心深度，单位m。默认值: 125.0m。
        co2_temp (float): 注入CO2的温度，单位K。默认值: 290.0 K。
        p_seabed (float): 海底压力，单位Pa。默认值: 10e6 Pa。
        res_perm (float): 储层渗透率，单位m²。默认值: 20e-15 m²。
        bound_perm (float): 上覆层/下伏层渗透率，单位m²。默认值: 1.0e-15 m²。
        dx (float): 网格水平尺寸，单位m。默认值: 2.0m。
        dz (float): 网格垂向尺寸，单位m。默认值: 2.0m。
        **other_opts: 其他传递给create()的可选参数。
    """
    mesh_depth = res_depth + 75  # 在下面，有25米的储层，以及50米的下伏层
    # 创建mesh
    mesh = create_xz_half(
        x_max=well_dist, depth=mesh_depth, height=100.0,
        dx=dx, dz=dz,
        hc=res_depth + 25,  # 储层底部深度
        rc=100,  # 加密区域半径
        ratio=1.02,  # 网格渐变比
        dx_max=dx, dz_max=dz * 1.5  # 最大网格尺寸
    )

    # 添加虚拟的cell和face用于生产（模拟生产井）
    add_cell_face(
        mesh, pos=[0, 0, -res_depth], offset=[0, 10, 0], vol=10000,
        area=1, length=1
    )

    # 初始的体积饱和度
    def s_ini(x, y, z):
        if abs(y) > 1:  # 用于记录生产的虚拟边界（不存在水合物）
            return {'h2o': 1 - 0.0315 / 2.165,
                    'inh': 0.0315 / 2.165}
        if -(res_depth + 25) <= z <= -(res_depth - 25):  # 甲烷水合物区域（储层范围）
            sh = 0.4  # 初始水合物饱和度
            return {'h2o': (1 - 0.0315 / 2.165) * (1 - sh),
                    'inh': (0.0315 / 2.165) * (1 - sh),
                    'ch4_hydrate': sh}
        else:
            return {'h2o': 1 - 0.0315 / 2.165,
                    'inh': 0.0315 / 2.165}

    # co2注入的质量速率随着时间的变化曲线
    vt = [0, year_beg_inj * 365 * 24 * 3600, year_prod * 365 * 24 * 3600]  # 时间节点（s）
    vq = [0, co2_mass_rate, 0]  # 对应时间点的注入速率（kg/s），开始时和结束时均为0

    assert 0.01e-15 <= bound_perm <= 100e-15
    assert 0.01e-15 <= res_perm <= 100e-15

    # 不同位置的渗透率（使用Tensor3支持各向异性）
    def get_k(x, y, z):
        if z >= 0:  # 模拟海水区域，把渗透率设置得更大（高出10倍）
            return Tensor3(xx=bound_perm * 10, yy=bound_perm * 10, zz=bound_perm * 10)
        elif z >= -(res_depth - 25) or z <= -(res_depth + 25):  # 上覆层和下伏层（低渗透隔层）
            return Tensor3(xx=bound_perm, yy=bound_perm, zz=bound_perm)
        else:  # 水合物层（高渗透，且垂向渗透率低于水平，kv/kh=0.25）
            return Tensor3(xx=res_perm, yy=res_perm, zz=res_perm / 4.0)

    # 热传导系数场（空间变化）
    def heat_cond(x, y, z):  # 确保不会有热量通过用于生产的虚拟的cell传递过来
        return 1.0 if abs(y) < 2 else 0.0  # 只在y方向±2m范围内传导热量

    assert 4e6 <= p_seabed <= 30e6

    # 首先，创建co2的注入模型. 但是这里要规定注入的间隔
    model = create(
        mass_rate=[vt, vq],  # 注入速率随时间变化的时间-速率曲线
        years_inj=200.0,  # 此参数用不上（因为注入由vt/vq曲线控制），所以给足够的时间
        p_seabed=p_seabed,
        t_seabed=275.0,
        depth_inj=res_depth,  # 注入点位于储层中心深度
        x_inj=well_dist,  # 注入井位于右侧（x=well_dist处）
        perm=get_k,  # 空间变化的各向异性渗透率
        mesh=mesh, s_ini=s_ini,
        save_dt_min=7.0 * 24.0 * 3600.0,  # 每周保存一次结果
        heat_cond=heat_cond,  # 空间变化的热传导系数
        prods=[{'index': mesh.cell_number - 1, 't': [0, 1e20], 'p': [3e6, 3e6]}],  # 以3MPa的恒定压力降压开发
        co2_temp=co2_temp,
        **other_opts
    )

    # 在最后的虚拟边界，不发生物质的反应. hyd_rate在create函数中定义了
    idx = model.get_cell_key('hyd_rate')
    assert idx is not None
    model.get_cell(-1).set_attr(idx, 0)  # 最后一个单元（生产井）不进行水合物反应

    # 修改绘图的范围（聚焦于储层区域）
    model.set_text('show_2d_v2_opts', dict(
        yr=[-1, 1], zr=[-(res_depth + 50), 0]  # 垂向显示范围
    ))

    # 修改求解选项：添加生产井的监测
    opt = eval(model.get_text('solve'))
    opt['monitor'] = {'cell_ids': [model.cell_number - 1]}  # 监视最后一个单元（生产井）的状态
    tfc.set_solve(model, **opt)

    # 添加定时操作，用来管理生产的开启和闭合
    timer.add_setting(model, time=year_prod * 365 * 24 * 3600, name='close_prod', args=['@model'])

    # 关闭生产井（将生产井面的面积设为0，即停止生产）
    def close_prod(m: Seepage):
        """
        关闭生产井的回调函数。

        将生产井所在面的面积设为0，从而停止流体产出。

        参数:
            m (Seepage): 水合物模型对象。
        """
        tfc.set_face(face=m.get_face(-1), area=0)

    # 执行模型的求解
    solve(
        model, folder=folder, slots={'close_prod': close_prod},
        gui_iter=GuiIterator(ratio=0.05)  # GUI迭代器，每步显示进度
    )


if __name__ == '__main__':  # 对比注入和不注入的效果
    from zmlx.ui import gui
    gui.execute(lambda: execute(folder=opath('hydrate', 'co2_disp')), close_after_done=True)
