# -*- coding: utf-8 -*-
"""

@author: Maryelin

Specific Heat of Oxigen Gas  from:
https://www.engineeringtoolbox.com/oxygen-d_978.html
"""
from zmlx.fluid.conf.gas_density.O2_density import *
from zmlx.fluid.conf.gas_viscosity.O2_viscosity import *
from zml import Interp2, Seepage

import numpy as np
import matplotlib.pyplot as plt
import warnings


def create(tmin=280, tmax=700, pmin=1.0e6, pmax=20.0e6, name=None):
    assert 250 < tmin < tmax < 750
    assert 0.01e6 < pmin < pmax < 30.0e6

    def liq_den(P, T):
        density = den_O2(P, T)
        return density

    def get_density(P, T):
        return liq_den(P, T)

    def create_density():
        den = Interp2()
        den.create(pmin, 1e6, pmax, 280, 10, 750, get_density)
        return den

    def liq_vis(P, T):
        viscosity = vis_o2(P, T)
        return viscosity

    def get_viscosity(P, T):
        return liq_vis(P, T)

    def create_viscosity():
        vis = Interp2()
        vis.create(pmin, 1e6, pmax, tmin, 10, tmax, get_viscosity)
        return vis

    specific_heat = 1090  # J/kg K
    return Seepage.FluDef(den=create_density(), vis=create_viscosity(), specific_heat=specific_heat, name=name)


def create_flu(*args, **kwargs):
    warnings.warn('use function <create> instead', DeprecationWarning)
    return create(*args, **kwargs)


if __name__ == '__main__':
    flu = create()

    # Crear mallas de presión y temperatura
    P_values = np.linspace(1.0e6, 20.0e6, 100)
    T_values = np.linspace(280, 700, 100)
    P_grid, T_grid = np.meshgrid(P_values, T_values)

    # Calcular densidad y viscosidad en función de P y T
    density_grid = np.zeros_like(P_grid)
    viscosity_grid = np.zeros_like(P_grid)

    for i in range(P_grid.shape[0]):
        for j in range(P_grid.shape[1]):
            p = P_grid[i, j]
            t = T_grid[i, j]
            density_grid[i, j] = den_O2(p, t)
            viscosity_grid[i, j] = vis_o2(p, t)

    # Gráficos de superficie para la densidad
    plt.figure(figsize=(8, 6))
    cp_density = plt.contourf(P_grid / 1e6, T_grid, density_grid, cmap='coolwarm')
    plt.title('Densidad del Oxígeno')
    plt.xlabel('Presión (MPa)')
    plt.ylabel('Temperatura (K)')
    cbar_density = plt.colorbar(cp_density, label='Densidad (kg/m^3)')
    plt.show()

    # Gráficos de superficie para la viscosidad
    plt.figure(figsize=(8, 6))
    cp_viscosity = plt.contourf(P_grid / 1e6, T_grid, viscosity_grid, cmap='coolwarm')
    plt.title('Viscosidad del Oxígeno')
    plt.xlabel('Presión (MPa)')
    plt.ylabel('Temperatura (K)')
    cbar_viscosity = plt.colorbar(cp_viscosity, label='Viscosidad (Pa·s)')
    plt.show()
