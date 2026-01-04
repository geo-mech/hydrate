# ** desc = '原位转化-竖直井-在一个圆柱形状的区域内'


from zmlx import *


def create(years_heating=10.0, years_max=10.0, power=50e3):
    """
    建立模型. 其中years_heating为加热的时长(年), years_max为计算的总的时长(年)，power为加热的功率.
    """
    from zmlx.seepage_mesh.cylinder import create_vertical_cylinder

    # 在半径方向的网格节点
    vr = [0.0]
    dr = 1.0
    while vr[-1] < 50.0:
        vr.append(vr[-1] + dr)
        dr += 0.1
    vr = sorted(vr)

    # 在竖直方向的网格节点
    vz = np.linspace(-15, 15, 31).tolist()  # 储层范围内的网格节点
    dz = 1.0
    while max(vz) < 40.0:
        vz.append(max(vz) + dz)
        dz += 0.2
    dz = 1.0
    while min(vz) > -40.0:
        vz.append(min(vz) - dz)
        dz += 0.2
    vz = sorted(vz)

    # 显示网格节点
    print(f"vr = {vr}")
    print(f"vz = {vz}")

    # 创建圆柱的Mesh
    mesh = create_vertical_cylinder(z=vz, r=vr)
    print(f"mesh = {mesh}")

    z_min, z_max = get_pos_range(mesh, 2)
    print(f"z_min = {z_min}, z_max = {z_max}")

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

    # 设置竖直井加热的范围，默认为-10到10之间，然后，找到涉及的cells
    heating_cell_ids = []
    for z in np.linspace(-10, 10, 100):
        c = mesh.get_nearest_cell(pos=[0, 0, z])
        if c.index not in heating_cell_ids:
            heating_cell_ids.append(c.index)

    print(f"heating_cell_ids = {heating_cell_ids}")
    v_pos = [mesh.get_cell(i).pos for i in heating_cell_ids]

    ca = tfc.cell_keys()
    injectors = [
        {'pos': pos, 'radi': 3, 'ca_mc': ca.mc,
         'ca_t': ca.temperature,
         'value': power / len(v_pos),
         'opers': [[years_heating * 3600.0 * 24.0 * 365.0,
                    '0']],
         } for pos in v_pos]

    # 用于solve的选项
    solve = {
        'time_max': 3600.0 * 24.0 * 365.0 * years_max,
    }

    # 创建模型
    model = tfc.create(
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
        dt_max=3600.0 * 24.0 * 5.0,
        gravity=[0, 0, -10],
        gr=gr,
        default_kr=default_kr,
        injectors=injectors,
        texts={'solve': solve},
    )
    # 返回模型
    return model


def show(model: Seepage):
    def on_figure(figure):
        from zmlx.plt import calculate_subplot_layout
        n_rows, n_cols = calculate_subplot_layout(8, subplot_aspect_ratio=0.5, fig=figure)
        opts = dict(ncols=n_cols, nrows=n_rows, xlabel='x', ylabel='z', aspect='equal')
        mask = get_cell_mask(model=model, xr=[0, 30], zr=[-20, 20])
        x = tfc.get_x(model, mask=mask)
        z = tfc.get_z(model, mask=mask)
        args = ['tricontourf', x, z, ]
        t = tfc.get_t(model, mask=mask)
        add_axes2(figure, add_items, item(*args, t, cbar=dict(label='温度', shrink=0.6), cmap='coolwarm'),
                  title='温度', index=1, **opts)
        p = tfc.get_p(model, mask=mask)
        add_axes2(figure, add_items, item(*args, p, cbar=dict(label='压力', shrink=0.6), cmap='jet'),
                  title='压力', index=2, **opts)
        v = tfc.get_v(model, mask=mask)
        index = 3
        for fid in ['kg', 'ho', 'lo', 'ch4', 'h2o', 'steam', ]:
            s = tfc.get_v(model, mask=mask, fid=fid) / v
            add_axes2(figure, add_items, item(*args, s, cbar=dict(label=f'{fid}饱和度', shrink=0.6)),
                      title=f'{fid}饱和度', index=index, **opts)
            index += 1

    plot(on_figure, caption=f'model({model.handle})', clear=True, tight_layout=True,
         suptitle=f'time = {tfc.get_time(model, as_str=True)}'
         )


def main():
    model = create()
    tfc.solve(model=model, extra_plot=lambda: show(model))


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
