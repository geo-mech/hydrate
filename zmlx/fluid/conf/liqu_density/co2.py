"""

New correlations predict aqueous solubility and density of carbon dioxide.
https://doi.org/10.1016/j.ijggc.2009.01.003


the paper uses two tunned coefficients for different ranges of pressure, 
for the project range P=(1 MPA - 50 MPA) and T=(270K - 330K), 
only the second coefficients fit

For very low pressures the densities are negative, 
it is due to the proximity of the gaseous phase of CO2,
therefore, the values adjust to the general value of 
the density of CO2 in the gaseous phase (1.975 kg/m^3).

"""


def liq_den_co2(p, t):
    p = p / 0.1e6  # convert Pa to Bar

    a1 = 1.053293651041897e5
    b1 = -9.396448507019846e2
    c1 = 2.397414334181339
    d1 = -1.819046028481314e-3

    a2 = -8.253383504614545e2
    b2 = 7.618125848567747
    c2 = -1.963563757655062e-2
    d2 = 1.497658394413360e-5

    a3 = 2.135712083402950
    b3 = -2.023128850373911e-2
    c3 = 5.272125417813041e-5
    d3 = -4.043564072108339e-8

    a4 = -1.827956524285481e-3
    b4 = 1.768297712855951e-5
    c4 = -4.653377143658811e-8
    d4 = 3.586708189749551e-11

    alpha = a1 + b1 * p + c1 * p ** 2 + d1 * p ** 3
    betha = a2 + b2 * p + c2 * p ** 2 + d2 * p ** 3
    rho = a3 + b3 * p + c3 * p ** 2 + d3 * p ** 3
    theta = a4 + b4 * p + c4 * p ** 2 + d4 * p ** 3
    density = alpha + betha * t + rho * t ** 2 + theta * t ** 3

    return max(density, 1.95)

# # #Test
# temperature = np.linspace(270, 330, 100)
# pressure = np.linspace(1.0e6, 50e6, 100)
# den = []
# for t in temperature:
#     for p in pressure:
#         den.append(liq_den_co2(p, t))

# print (den)
# X, Y = np.meshgrid(temperature, pressure)
# Y = Y / 1.0E6
# den = np.array(den)
# den = np.transpose(den.reshape(100, 100))
# plt.contourf(den, 20, extent=[X.min(), X.max(), Y.min(), Y.max()], cmap='viridis')        
# plt.colorbar()
