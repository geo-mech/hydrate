# -*- coding: utf-8 -*-
"""
Define the property of oil.

data From Maryelin. 2022.11.16

by 张召彬

注意，此处定义的oil为重油，粘度非常大，如下所示，可见在温度低于350K的时候，它的粘性比水大了
将近3个数量级，因此几乎是很难流动的。

这个油必须加热，才能具有有效的流动性

p = 10000000.0Pa, T = 280K, vis = 2426.073208739302Pa.s, den = 1021.584094kg/m^3
p = 10000000.0Pa, T = 300K, vis = 97.29407445378405Pa.s, den = 1010.354894kg/m^3
p = 10000000.0Pa, T = 350K, vis = 0.7468576292043122Pa.s, den = 982.281894kg/m^3
p = 10000000.0Pa, T = 400K, vis = 0.0605029228796798Pa.s, den = 954.208894kg/m^3
p = 10000000.0Pa, T = 500K, vis = 0.0063358958456372905Pa.s, den = 898.062894kg/m^3

"""

from math import log, exp

from zml import Interp2, TherFlowConfig


def create_flu(tmin=270, tmax=1000, pmin=1e6, pmax=40e6):
    def oil_den(pressure, temp):
        """
        Nourozieh, H., et al. (2015). "Density and Viscosity of Athabasca Bitumen Samples at Temperatures up to 200° C and Pressures up to 10 MPa." SPE Reservoir Evaluation & Engineering 18(03): 375-386.
        """
        a1 = 1021.62  # kg*m^-3
        a2 = - 0.58976  # kg*m^-3 * C^-1
        a4 = 0.382  # 1/MPa
        a5 = 0.00283  # C^-1
        alpha = a4 + a5 * (temp - 273.5)  # temp = Kelvin to Celsius
        den_o = a1 + a2 * (temp - 273.15)
        den = den_o + alpha * (pressure * 0.000001)  # Pressure Mpa
        return den

    def get_density(P, T):
        return oil_den(P, T)

    def oil_vis(pressure, temp):  # Mehrotra and Svrcek, 1986
        """
        Mehrotra, A. K. and W. Y. Svrcek (1986).
        "Viscosity of compressed athabasca bitumen." The Canadian Journal of Chemical Engineering 64(5): 844-847.
        """
        b1 = 22.8515
        b2 = -3.5784
        b3 = int(0.00511938)
        A = (b1 + (b2 * log(temp))) + (b3 * (pressure * 0.000001))
        vis_oil = 0.001 * (exp(exp(A)))
        return vis_oil

    def get_viscosity(P, T):
        return oil_vis(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, tmin, 10, tmax, get_density)
        return den

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 1800
    return TherFlowConfig.FluProperty(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat)


if __name__ == '__main__':
    flu = create_flu()
    print(flu)
    for p, T in [(10e6, 280), (10e6, 300), (10e6, 350), (10e6, 400), (10e6, 500)]:
        vis = flu.vis(p, T)
        den = flu.den(p, T)
        print(f'p = {p}Pa, T = {T}K, vis = {vis}Pa.s, den = {den}kg/m^3')
    try:
        from zmlx.plt.show_field2 import show_field2

        show_field2(flu.vis, [1e6, 40e6], [300, 1000])
        show_field2(flu.den, [1e6, 40e6], [300, 1000])
    except:
        pass

    """
p = 10000000.0Pa, T = 280K, vis = 2426.073208739302Pa.s, den = 1021.584094kg/m^3
p = 10000000.0Pa, T = 300K, vis = 97.29407445378405Pa.s, den = 1010.354894kg/m^3
p = 10000000.0Pa, T = 350K, vis = 0.7468576292043122Pa.s, den = 982.281894kg/m^3
p = 10000000.0Pa, T = 400K, vis = 0.0605029228796798Pa.s, den = 954.208894kg/m^3
p = 10000000.0Pa, T = 500K, vis = 0.0063358958456372905Pa.s, den = 898.062894kg/m^3
    """
