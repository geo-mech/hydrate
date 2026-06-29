# ** desc = 'Gas migration with N2_CH4_He equilibrium interface'

from zmlx import *
from zmlx.scen.uv_equilibrium.N2_CH4_He import GasWaterUVEquilibrium


MASS_CUTOFF_KG = 1.0e-30


def create(jx, jz):
    mesh = create_cube(
        x=linspace(0, 300, jx + 1),
        y=(-0.5, 0.5),
        z=linspace(-500, 0, jz + 1)
    )

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
            return {'CH4': 0.9, 'H2O': 0.1}
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
            return 1.0
        else:
            return 0.1

    model = tfc.create(
        mesh, porosity=get_porosity, pore_modulus=100e6,
        denc=get_denc, dist=0.1,
        temperature=get_t, p=get_p, s=get_s,
        perm=get_k, heat_cond=2.0,
        fludefs=fludefs,
        dt_max=3600 * 24 * 30.0, gravity=(0, 0, -10)
    )

    model.set_text(
        key='solve',
        text={'time_max': 3600 * 24 * 365 * 6, }
    )
    step_iteration.add_setting(model, name='balance', step=1, args=['@model'])
    return model


def balance(model: Seepage):
    ada = as_numpy(model)

    p = ada.cells.pre
    t = ada.fluids('aqueous').get_attr('temperature')
    names = tfc.list_comp(model, keep_structure=False)
    mass = {name: ada.fluids(name).mass for name in names}

    for item in mass.values():
        item[np.abs(item) < MASS_CUTOFF_KG] = 0.0
    mass0 = sum(np.sum(item) for item in mass.values())

    if not hasattr(balance, "eq"):
        balance.eq = GasWaterUVEquilibrium()
    eq = balance.eq

    gas_mass = mass["CH4"] + mass["N2"] + mass["He"]
    failed = 0
    for i in np.flatnonzero((mass["H2O"] > 1.0e-20) & (gas_mass > 1.0e-6 * mass["H2O"])):
        try:
            result = eq.get_next_state(float(t[i]), float(p[i]), {
                "H2O(aq)": float(mass["H2O"][i]),
                "CH4(aq)": float(mass["CH4(aq)"][i]),
                "N2(aq)": float(mass["N2(aq)"][i]),
                "He(aq)": float(mass["He(aq)"][i]),
                "H2O(g)": 0.0,
                "CH4(g)": float(mass["CH4"][i]),
                "N2(g)": float(mass["N2"][i]),
                "He(g)": float(mass["He"][i]),
            })
        except Exception:
            failed += 1
            continue

        mass["H2O"][i] = result["H2O(aq)"] + result["H2O(g)"]
        mass["CH4(aq)"][i] = result["CH4(aq)"]
        mass["N2(aq)"][i] = result["N2(aq)"]
        mass["He(aq)"][i] = result["He(aq)"]
        mass["CH4"][i] = result["CH4(g)"]
        mass["N2"][i] = result["N2(g)"]
        mass["He"][i] = result["He(g)"]

    if failed > 0:
        print(f"N2_CH4_He equilibrium failed in {failed} cells.")

    for item in mass.values():
        item[np.abs(item) < MASS_CUTOFF_KG] = 0.0
    assert np.isclose(sum(np.sum(item) for item in mass.values()), mass0)

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
            m = np.log10(1.0 + m / max(np.max(m) * 1.0e-6, 1.0e-30))
            layout.add_axes2(add_contourf, x, z, m, cbar=dict(label='log mass', shrink=0.6),
                             title=f'{name} mass')
            m = tfc.get_m(model, fid=f'{name}(aq)', shape=(jx, jz))
            m = np.log10(1.0 + m / max(np.max(m) * 1.0e-6, 1.0e-30))
            layout.add_axes2(add_contourf, x, z, m, cbar=dict(label='log mass', shrink=0.6),
                             title=f'{name}(aq) mass')

    return plot(
        on_figure,
        caption=f'Seepage({model.handle_str})',
        suptitle=f'time: {tfc.get_time(model, as_str=True)}',
        tight_layout=True,
        clear=True,
        gui_mode=True)


def main():
    jx, jz = 60, 100
    model = create(jx, jz)
    tfc.solve(model, close_after_done=False, extra_plot=lambda: show(model, jx, jz),
              slots={'balance': balance})


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
