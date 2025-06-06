# ** desc = '原位转化：在xz平面二维的模型 (动态调整导热系数)'


from zmlx import *


def create(years_heating=5.0, years_max=8.0, power=5e3):
    """
    建立模型. 其中years_heating为加热的时长(年), years_max为计算的总的时长(年)，power为加热的功率.
    """
    mesh = create_xz(x_min=0, dx=0.3, x_max=15.0, y_min=-1, y_max=0,
                     z_min=-30.0, dz=0.3, z_max=30.0)

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
    injectors = [{'pos': pos, 'radi': 3, 'ca_mc': ca.mc,
                  'ca_t': ca.temperature,
                  'value': power / len(v_pos),
                  'opers': [[years_heating * 3600.0 * 24.0 * 365.0,
                             '0']],
                  } for pos in v_pos]

    # 用于接收流体产出的cell
    prods = [{'index': mesh.cell_number - 1,
              't': [0, 1e10],
              'p': [20e6, 20e6]
              }]

    # 用于solve的选项
    solve = {'monitor': {'cell_ids': [mesh.cell_number - 1]},  # 监视用于产出的cell
             'time_max': 3600.0 * 24.0 * 365.0 * years_max,
             'show_cells': {'dim0': 0,
                            'dim1': 2,
                            'mask': get_cell_mask(model=mesh,
                                                  yr=[-3, 3])},
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
    # 定时更新热传导系数
    for year in np.linspace(0, years_max, round(years_max * 10)).tolist():
        timer_config.add_setting(model, time=year * 365 * 24 * 3600,
                                 name='update_hc',
                                 args=['@model', '@time'])

    # 返回模型
    return model


def get_hc(T):
    """
    根据温度(单位为K)计算热传导系数. （请重写此函数）
    """
    pass


def update_hc(m: Seepage, t=None):
    """
    更新模型的热传导系数
    """
    ca_idx = m.get_cell_key('temperature')
    temp = [c.get_attr(ca_idx) for c in m.cells]
    fa = seepage.face_keys(m)
    fa_s = fa.area
    fa_l = fa.length
    fa_g = fa.g_heat
    for face in m.faces:
        assert isinstance(face, Seepage.Face)
        T = (temp[face.get_cell(0).index] + temp[face.get_cell(1).index]) / 2.0
        hc = get_hc(T)
        if hc is not None:
            assert 0 <= hc <= 100
            s = face.get_attr(fa_s)
            l = face.get_attr(fa_l)
            g = s * hc / l
            face.set_attr(fa_g, g)
    if t is not None:
        print(f'Heat cond Update when {time2str(t)}')


if __name__ == '__main__':
    seepage.solve(model=create(), close_after_done=True,
                  folder=opath('icp_xz_hc_dyn'),
                  slots={'update_hc': update_hc})
