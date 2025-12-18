# ** desc = '原位转化：在xz平面二维的模型'


from zmlx import *


def create(years_heating=5.0, years_max=8.0, power=5e3):
    """
    建立模型. 其中years_heating为加热的时长(年), years_max为计算的总的时长(年)，power为加热的功率.
    """
    mesh = create_xz(x_min=0, dx=0.5, x_max=15.0, y_min=-1, y_max=0,
                     z_min=-30.0, dz=0.5, z_max=30.0)

    z_min, z_max = get_pos_range(mesh, 2)

    # 添加虚拟的cell和face用于生产
    add_cell_face(mesh, pos=[0, 0, 0], offset=[0, 10, 0],
                  vol=10000, area=1, length=1)

    def get_perm(x, y, z):  # 渗透率
        return 1.0e-15 if -15 <= z <= 15 else 0

    def get_s(x, y, z):  # 初始饱和度
        if -15 <= z <= 15 and y < 5:
            return {'ch4': 0.08, 'h2o': 0.04, 'lo': 0.08,
                    'ho': 0.2, 'kg': 0.6}
        else:
            return {'ch4': 1}

    def get_denc(x, y, z):  # 密度和比热的乘积
        if abs(z - z_min) < 0.1 or abs(z - z_max) < 0.1:
            return 1e20
        else:
            return 4e6

    def get_porosity(x, y, z):  # 孔隙度
        return 0.3 if -15 <= z <= 15 else 0.01

    # 渗透率曲线
    gr = create_krf(faic=0.02, n=3.0, k_max=100, s_max=2.0,
                    count=500, as_interp=True)

    # 默认的相对渗透率曲线
    default_kr = create_krf(faic=0.05, n=2.0, count=300,
                            as_interp=True)

    # 定义流体的注入或者储层加热
    v_pos = [[15.0, 1, -7.5],
             [15.0, 1, +7.5]]
    ca = seepage.cell_keys()
    injectors = [
        {'pos': pos, 'radi': 3, 'ca_mc': ca.mc,
         'ca_t': ca.temperature,
         'value': power / len(v_pos),
         'opers': [[years_heating * 3600.0 * 24.0 * 365.0,
                    '0']],
         } for pos in v_pos]

    # 用于接收流体产出的cell
    prods = [
        {'index': mesh.cell_number - 1,
         't': [0, 1e10],
         'p': [20e6, 20e6]
         }]

    # 用于solve的选项
    solve = {
        'monitor': {'cell_ids': [mesh.cell_number - 1]},  # 监视用于产出的cell
        'time_max': 3600.0 * 24.0 * 365.0 * years_max,
    }

    # 创建模型
    model = seepage.create(
        mesh=mesh,
        keys=ca.get_keys(),  # 使用这里定义的key
        fludefs=icp.create_fludefs(),
        reactions=icp.create_reactions(temp_max=1000),
        porosity=get_porosity,
        pore_modulus=100e6,
        p=20e6,
        temperature=350.0,
        denc=get_denc,
        s=get_s,
        perm=get_perm,
        heat_cond=2.0,
        dist=0.2,
        has_solid=False,
        dt_max=3600.0 * 24.0 * 10.0,
        gravity=[0, 0, -10],
        gr=gr,
        default_kr=default_kr,
        injectors=injectors,
        prods=prods,
        texts={'solve': solve},
    )
    # 返回模型
    return model


def show(model: Seepage, caption=None):
    def on_figure(fig):
        from zmlx.plt.subplot_layout import calculate_subplot_layout
        n_rows, n_cols = calculate_subplot_layout(8, subplot_aspect_ratio=0.5, fig=fig)
        opts = dict(ncols=n_cols, nrows=n_rows, xlabel='x', ylabel='z', aspect='equal')
        mask = get_cell_mask(model=model, yr=[-3, 3], zr=[-15, 15])
        x = seepage.get_x(model, mask=mask)
        z = seepage.get_z(model, mask=mask)
        args = ['tricontourf', x, z, ]
        t = seepage.get_t(model, mask=mask)
        add_axes2(fig, add_items, item(*args, t, cbar=dict(label='温度', shrink=0.6), cmap='coolwarm'),
                  title='温度', index=1, **opts)
        p = seepage.get_p(model, mask=mask)
        add_axes2(fig, add_items, item(*args, p, cbar=dict(label='压力', shrink=0.6), cmap='jet'),
                  title='压力', index=2, **opts)
        v = seepage.get_v(model, mask=mask)
        index = 3
        for fid in ['kg', 'ho', 'lo', 'ch4', 'h2o', 'steam', ]:
            s = seepage.get_v(model, mask=mask, fid=fid) / v
            add_axes2(fig, add_items, item(*args, s, cbar=dict(label=f'{fid}饱和度', shrink=0.6)),
                      title=f'{fid}饱和度', index=index, **opts)
            index += 1

    plot(on_figure, caption=caption, clear=True, tight_layout=True,
         suptitle=f'time = {seepage.get_time(model, as_str=True)}'
         )


def main():
    model = create()
    seepage.solve(model=model, extra_plot=lambda: show(model, caption='当前状态'))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
