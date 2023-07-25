"""
Created on Thu Jan 26 18:50:17 2023

@author: Maryelin

Density of Compressed liquid base on:
Thomson, G. H., Brobst, K. R., & Hankinson, R. W. (1982).
An improved correlation for densities of compressed liquids and liquid mixtures. 
AIChE Journal, 28(4), 671–676. doi:10.1002/aic.690280420

Vapor Pressure by: 
Antoine, C. 1888. Tensions des Vapeurs: Nouvelle Relation Entre les Tensions et les Tempé. Compt.Rend. 107:681-684.
Yaws, Carl L. The Yaws Handbook of Vapor Pressure: Antoine Coefficients. 1 edition. Houston, Tex: Gulf Publishing Company, 2007.

Vs = Saturation liquid Volumen using the packages 
chemicals: Chemical properties component of Chemical Engineering Design Library (ChEDL)
https://chemicals.readthedocs.io/index.html
https://github.com/CalebBell/chemicals
https://chemicals.readthedocs.io/chemicals.volume.html#pure-high-pressure-liquid-correlations

TEMP = (100-600)K
"""
import chemicals  # pip install chemicals (https://chemicals.readthedocs.io/index.html#installation)
import numpy as np


def liq_den_c11h24(P, T):
    # parameters COSTALD
    a = -9.070217
    b = 62.45326
    d = -135.1102
    f = 4.79594
    g = 0.250047
    h = 1.14188
    j = 0.0861488
    k = 0.0344483

    # compound properties
    PM = 0.15631  # Kg/mol
    Tc = 638.8  # K
    Pc = 1.961e6  # Pa
    Vc = 6.57e-4  # m3/mol
    omega = 0.536

    # Vapor Pressure Antoine (Yaws Carl)
    t = T - 273.15  # convert kelvin to celsius
    A = 6.95567
    B = 1498.32
    C = 187.7
    LOGP = A - (B / (t + C))
    Pv = 10 ** (LOGP) * 133.32  # convert mmHg to Pa
    Psat = Pv

    # Saturation liquid Volumen
    Vs = chemicals.volume.COSTALD(T, Tc, Vc, omega)

    # COSTALD EQUATION
    e = np.exp(f + omega * (g + h * omega))
    C = j + k * omega
    tau = (1.0 - T / Tc)
    tau13 = tau ** (1.0 / 3.0)
    B = Pc * (-1.0 + a * tau13 + b * tau13 * tau13 + d * tau + e * tau * tau13)
    l = (B + P) / (B + Psat)
    V = Vs * (1.0 - C * np.log(l))  # m3/mol
    den = (1 / V) * PM
    return den
