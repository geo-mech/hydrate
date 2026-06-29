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
        ("trace gases", 321.5247499999999, 20e6, {
            'H2O(aq)': 1.5729881371397732e-12,
            'CH4(g)': 4086.2041550808335,
            'CH4(aq)': 1.604276000000001e-32,
            'N2(g)': 1.9999999999999998e-15,
            'N2(aq)': 6.338597851491371e-31,
            'He(g)': 2e-15,
            'He(aq)':7.7440787912272335e-16

        }),
        ("trace gases2", 320.8602499999998, 20e6, {
            'H2O(aq)': 4.723755107775538e-12,
            'CH4(g)': 4055.4941995691584,
            'CH4(aq)': 1.604276000000001e-32,
            'N2(g)': 2.9999999999999987e-15,
            'N2(aq)': 5.116488731469181e-31,
            'He(g)': 3.4710901301181186e-15,
            'He(aq)': 5.648472375049904e-16

        }),
        ("trace gases3", 321.3032499999999, 19774992.847443175, {
            'H2O(aq)': 2.963995067625287e-12,
            'CH4(g)': 4075.978388727625,
            'CH4(aq)': 1.604276000000002e-32,
            'N2(g)': 1.9999999999999724e-18,
            'N2(aq)': 2.915630225956565e-32,
            'He(g)': 2.000000000000195e-18,
            'He(aq)': 1.4583199953781014e-15

        }),
    ]

    for name, temperature, pressure, masses in cases:
        print("\n" + name)
        r = x.get_next_state(temperature=temperature, pressure=pressure, masses=masses)
        print(r)


if __name__ == "__main__":
    test()
