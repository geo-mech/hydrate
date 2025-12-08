# ** desc = '水平井注采。向水合物储层注入co2，并在另外一口水平井降压开发水合物'

from zmlx.base.zml import Tensor3, Seepage
from zmlx.config import timer, seepage
from zmlx.demo.hydrate.co2 import create, solve
from zmlx.io import opath
from zmlx.seepage_mesh.edit import add_cell_face
from zmlx.seepage_mesh.xz_half import create_xz_half
from zmlx.utility.gui_iterator import GuiIterator


def execute(
        folder=None, co2_mass_rate=10.0 / (3600.0 * 24.0), year_prod=10.0, year_beg_inj=2.0, well_dist=60.0,
        res_depth=125.0, co2_temp=290.0, p_seabed=10e6, res_perm=20e-15, bound_perm=1.0e-15, dx=2.0, dz=2.0,
        **other_opts
):
    """
    从左侧降压生产甲烷；右侧注入co2.
    """
    mesh_depth = res_depth + 75  # 在下面，有25米的储层，以及50米的下伏层
    # 创建mesh
    mesh = create_xz_half(
        x_max=well_dist, depth=mesh_depth, height=100.0,
        dx=dx, dz=dz,
        hc=res_depth + 25,
        rc=100,
        ratio=1.02,
        dx_max=dx, dz_max=dz * 1.5
    )

    # 添加虚拟的cell和face用于生产
    add_cell_face(
        mesh, pos=[0, 0, -res_depth], offset=[0, 10, 0], vol=10000,
        area=1, length=1
    )

    # 初始的体积饱和度
    def s_ini(x, y, z):
        if abs(y) > 1:  # 用于记录生产的虚拟边界 (不存在水合物)
            return {'h2o': 1 - 0.0315 / 2.165,
                    'inh': 0.0315 / 2.165}
        if -(res_depth + 25) <= z <= -(res_depth - 25):  # 甲烷水合物区域
            sh = 0.4
            return {'h2o': (1 - 0.0315 / 2.165) * (1 - sh),
                    'inh': (0.0315 / 2.165) * (1 - sh),
                    'ch4_hydrate': sh}
        else:
            return {'h2o': 1 - 0.0315 / 2.165,
                    'inh': 0.0315 / 2.165}

    # co2注入的质量速率随着时间的变化曲线
    vt = [0, year_beg_inj * 365 * 24 * 3600, year_prod * 365 * 24 * 3600]
    vq = [0, co2_mass_rate, 0]

    assert 0.01e-15 <= bound_perm <= 100e-15
    assert 0.01e-15 <= res_perm <= 100e-15

    # 不同位置的渗透率
    def get_k(x, y, z):
        if z >= 0:  # 模拟海水区域，把渗透率设置得更大
            return Tensor3(xx=bound_perm * 10, yy=bound_perm * 10, zz=bound_perm * 10)
        elif z >= -(res_depth - 25) or z <= -(res_depth + 25):  # 上覆层和下伏层
            return Tensor3(xx=bound_perm, yy=bound_perm, zz=bound_perm)
        else:  # 水合物层
            return Tensor3(xx=res_perm, yy=res_perm, zz=res_perm / 4.0)

    # 热传导系数场
    def heat_cond(x, y, z):  # 确保不会有热量通过用于生产的虚拟的cell传递过来.
        return 1.0 if abs(y) < 2 else 0.0

    assert 4e6 <= p_seabed <= 30e6

    # 首先，创建co2的注入模型. 但是这里要规定注入的间隔
    model = create(
        mass_rate=[vt, vq],
        years_inj=200.0,  # 此参数用不上，所以给足够的时间
        p_seabed=p_seabed,
        t_seabed=275.0,
        depth_inj=res_depth,
        x_inj=well_dist,
        perm=get_k,
        mesh=mesh, s_ini=s_ini,
        save_dt_min=7.0 * 24.0 * 3600.0,
        heat_cond=heat_cond,
        prods=[{'index': mesh.cell_number - 1, 't': [0, 1e20], 'p': [3e6, 3e6]}],  # 以3MPa的压力来降压开发
        co2_temp=co2_temp,
        **other_opts
    )

    # 在最后的虚拟边界，不发生物质的反应. hyd_rate在create函数中定义了
    idx = model.get_cell_key('hyd_rate')
    assert idx is not None
    model.get_cell(-1).set_attr(idx, 0)

    # 修改绘图的范围
    model.set_text('show_2d_v2_opts', dict(
        yr=[-1, 1], zr=[-(res_depth + 50), 0]
    ))

    # 修改求解选项
    opt = eval(model.get_text('solve'))
    opt['monitor'] = {'cell_ids': [model.cell_number - 1]}  # 监视生产过程
    seepage.set_solve(model, **opt)

    # 添加定时操作，用来管理生产的开启和闭合
    timer.add_setting(model, time=year_prod * 365 * 24 * 3600, name='close_prod', args=['@model'])

    # 关闭生产井
    def close_prod(m: Seepage):
        seepage.set_face(face=m.get_face(-1), area=0)

    # 执行模型的求解
    solve(
        model, close_after_done=True, folder=folder, slots={'close_prod': close_prod},
        gui_iter=GuiIterator(ratio=0.05)
    )


if __name__ == '__main__':  # 对比注入和不注入
    execute(folder=opath('hydrate', 'co2_disp'))
