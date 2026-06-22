# ** desc = '浮力作用下气体运移成藏过程模拟(考虑氦气等多组分气体)'

from zmlx import *


_EQUILIBRIA = {}
_EQUILIBRIUM_ERRORS = set()


def _get_components(mass):
    comps = []
    for name in mass:
        if name == 'H2O':
            continue
        comp = name[:-4] if name.endswith('(aq)') else name
        if comp not in comps:
            comps.append(comp)
    return tuple(comps)


def _get_gas_water_equilibrium(components):
    key = tuple(components)
    if key in _EQUILIBRIA:
        return _EQUILIBRIA[key]
    if key in _EQUILIBRIUM_ERRORS:
        return None
    try:
        from gas_water_uv_equilibrium import GasWaterUVEquilibrium
        eq = GasWaterUVEquilibrium(
            database_name='supcrtbl',
            gas_components=key,
            include_water_vapor=False,
            auto_use_organics=True,
        )
    except Exception as err:
        _EQUILIBRIUM_ERRORS.add(key)
        print(f'GasWaterUVEquilibrium 初始化失败，跳过本次化学平衡: {err}')
        return None
    _EQUILIBRIA[key] = eq
    return eq


def _get_mass_at(mass, name, index):
    if name not in mass:
        return 0.0
    return max(0.0, float(mass[name][index]))


def _update_mass_by_equilibrium(p, t, mass, equilibrium=None):
    components = _get_components(mass)
    if equilibrium is None:
        equilibrium = _get_gas_water_equilibrium(components)
    if equilibrium is None:
        return {'updated': 0, 'failed': 0, 'skipped': len(p)}

    updated = 0
    failed = 0
    skipped = 0
    for index in range(len(p)):
        water_kg = _get_mass_at(mass, 'H2O', index)
        gas_kg = {comp: _get_mass_at(mass, comp, index) for comp in components}
        aq_gas_kg = {comp: _get_mass_at(mass, f'{comp}(aq)', index) for comp in components}
        total_kg = water_kg + sum(gas_kg.values()) + sum(aq_gas_kg.values())
        if total_kg <= 1.0e-30:
            skipped += 1
            continue

        try:
            result = equilibrium.solve(
                temperature_K=float(t[index]),
                pressure_Pa=float(p[index]),
                water_kg=water_kg,
                aq_gas_kg=aq_gas_kg,
                gas_kg=gas_kg,
                fixed_volume_m3=None,
                temperature_bounds_K=(250.0, 800.0),
                pressure_bounds_Pa=(1.0e5, 1.0e9),
            )
        except Exception:
            failed += 1
            continue
        if not result.get('success', False):
            failed += 1
            continue

        if 'H2O' in mass:
            mass['H2O'][index] = result.get('water_kg', mass['H2O'][index])
        result_gas = result.get('gas_kg') or {}
        result_aq = result.get('aq_gas_kg') or {}
        for comp in components:
            if comp in mass and comp in result_gas:
                mass[comp][index] = result_gas[comp]
            aq_name = f'{comp}(aq)'
            if aq_name in mass and comp in result_aq:
                mass[aq_name][index] = result_aq[comp]
        updated += 1

    if failed > 0:
        print(f'GasWaterUVEquilibrium 有 {failed} 个cell未收敛，已保持原质量。')
    return {'updated': updated, 'failed': failed, 'skipped': skipped}


def create(jx, jz):
    dt = 3600 * 24 * 30.0
    mesh = create_cube(
        x=linspace(0, 300, jx + 1),
        y=(-0.5, 0.5),
        z=linspace(-500, 0, jz + 1)
    )

    # todo: 修改流体定义
    gas = ch4.create()
    wat = h2o.create()
    fludefs = [
        FluDef.create(defs=[gas.get_copy("N2"), gas.get_copy("He"), gas.get_copy("CH4")], name="gas"),
        FluDef.create(
            defs=[wat.get_copy("H2O"), wat.get_copy("N2(aq)"), wat.get_copy("He(aq)"), wat.get_copy("CH4(aq)")],
            name="aqueous"),
    ]

    def get_t(x, y, z):
        return 278 + 22.15 - 0.0443 * z

    def get_p(x, y, z):
        return 10e6 + 5e6 - 1e4 * z

    def is_gas_region(x, y, z):
        return get_distance([x, y, z], [150, 0, -500]) < 50

    def get_s(x, y, z):
        if is_gas_region(x, y, z):
            return {'CH4': 1}
        else:
            return {'H2O': 1, 'He(aq)': 0.001}

    z0, z1 = mesh.get_pos_range(2)

    def get_denc(x, y, z):
        if abs(z - z0) < 0.1 or abs(z - z1) < 0.1:
            return 1.0e20
        else:
            return 1.0e6

    def get_k(x, y, z):
        return 1.0e-14

    def get_porosity(x, y, z):
        if is_gas_region(x, y, z):
            return 1.0  # 使得有更多的气体
        else:
            return 0.1

    model = tfc.create(
        mesh, porosity=get_porosity, pore_modulus=100e6,
        denc=get_denc, dist=0.1,
        temperature=get_t, p=get_p, s=get_s,
        perm=get_k, heat_cond=2.0,
        fludefs=fludefs,
        dt_ini=dt, dt_max=dt, dv_relative=0.0, gravity=(0, 0, -10)
    )

    # 用于求解的选项
    model.set_text(
        key='solve',
        text={'time_max': 3600 * 24 * 365 * 6, 'step_max': 1, }
    )
    step_iteration.add_setting(model, name='balance', step=1, args=['@model'])
    return model


def balance(model: Seepage):
    """
    计算溶解/脱溶的平衡
    """
    ada = as_numpy(model)

    # step 1. 获取各个cell的压力、温度, 获取各个主要组分的质量
    p = ada.cells.pre
    t = ada.fluids('aqueous').get_attr('temperature')
    names = tfc.list_comp(model, keep_structure=False)
    mass = {name: ada.fluids(name).mass for name in names}

    # step 2.
    # todo: 调用化学库来更新各个组分的质量（更新mass）
    #       请宇轩实现
    #       注意：1、不要使用cell的volume属性，因为model中流体的密度可能和Reaktoro不同
    #            2、这里给的质量都是numpy数组，看Reaktoro能否向量化计算以提升效率
    _update_mass_by_equilibrium(p=p, t=t, mass=mass)

    # step 3.
    # 将更新之后的mass重新应用到模型中
    for name in names:
        ada.fluids(name).mass = mass[name]


def show(model, jx, jz):
    def on_figure(fig):
        from zmlx.plt import AutoLayout
        layout = AutoLayout(fig, num_plots=6, subplot_aspect_ratio=0.6, aspect='equal', xlabel='x/m', ylabel='z/m')

        x = tfc.get_x(model, shape=(jx, jz))
        z = tfc.get_z(model, shape=(jx, jz))
        p = tfc.get_p(model, shape=(jx, jz))
        angles = np.linspace(0, np.pi, 100)

        ax = layout.add_axes2(add_contourf, x, z, p, cbar=dict(label='p', shrink=0.6), title='pressure',
                              cmap='coolwarm')
        ax.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), 'k--')

        v_gas = tfc.get_v(model, fid='gas', shape=(jx, jz))
        v_aqueous = tfc.get_v(model, fid='aqueous', shape=(jx, jz))
        v_all = v_gas + v_aqueous
        ax = layout.add_axes2(add_contourf, x, z, v_gas / v_all, cbar=dict(label='s', shrink=0.6),
                              title='gas saturation')
        ax.plot(150 + 50 * np.cos(angles), -500 + 50 * np.sin(angles), 'r--')

        m_gas = tfc.get_m(model, fid='gas', shape=(jx, jz))
        m_aq = tfc.get_m(model, fid='aqueous', shape=(jx, jz))
        m_gas[m_gas < 1.0e-10] = 1.0e-10
        m_aq[m_aq < 1.0e-10] = 1.0e-10
        for name in ['CH4', 'He']:
            m = tfc.get_m(model, fid=name, shape=(jx, jz))
            layout.add_axes2(add_contourf, x, z, m / m_gas, cbar=dict(label='x', shrink=0.6),
                             title=f'{name} mass fraction')
            m = tfc.get_m(model, fid=f'{name}(aq)', shape=(jx, jz))
            layout.add_axes2(add_contourf, x, z, m / m_aq, cbar=dict(label='x', shrink=0.6),
                             title=f'{name}(aq) mass fraction')

    return plot(
        on_figure,
        caption=f'Seepage({model.handle_str})',
        suptitle=f'时间: {tfc.get_time(model, as_str=True)}',
        tight_layout=True,
        clear=True,
        gui_mode=True)


def main():
    jx, jz = 60, 100
    model = create(jx, jz)
    tfc.solve(model, close_after_done=False, extra_plot=lambda: show(model, jx, jz),
              slots={'balance': balance}
              )


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
