# -*- coding: utf-8 -*-

from zmlx.scen.uv_equilibrium.N2_CH4_He import GasWaterUVEquilibrium


def test():
    x = GasWaterUVEquilibrium()
    cases = [
        ("gas mixture", 320, 10e6, {
            'H2O(aq)': 1000,
            'CH4(g)': 100,
            'N2(g)': 100,
            'He(g)': 100,
        }),
        ("aqueous gases", 320, 10e6, {
            'H2O(aq)': 1000,
            'CH4(aq)': 1,
            'N2(aq)': 1,
            'He(aq)': 1,
        }),
        ("gas and aqueous", 320, 20e6, {
            'H2O(aq)': 1000,
            'CH4(aq)': 5,
            'He(aq)': 0.1,
            'CH4(g)': 100,
            'N2(g)': 10,
            'He(g)': 1,
        }),
        ("CH4 only", 320, 20e6, {
            'H2O(aq)': 1000,
            'CH4(g)': 100000,
        }),
        ("trace gases", 320, 20e6, {
            'H2O(aq)': 1000,
            'CH4(g)': 4000,
            'CH4(aq)': 1,
            'N2(g)': 0,
            'N2(aq)': 0,
            'He(g)': 1.0e-40,
            'He(aq)':1.0e-40

        }),
    ]

    for name, temperature, pressure, masses in cases:
        print("\n" + name)
        r = x.get_next_state(temperature=temperature, pressure=pressure, masses=masses)
        print(r)


if __name__ == "__main__":
    test()
