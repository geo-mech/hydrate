import numpy as np


def stone_model_I(swir, sorg, sorw, sgc, krwro, kroiw, krgro, nw, nsorw, ng, nog):
    """
    An oil-gas-water three-phase relative permeability model.

    By Maryelin.
    """

    assert swir < 1
    # oil-water system and gas-oil system Corey two phases model
    # variables
    sw = np.linspace(swir, 1 - sorw, 20, endpoint=True)
    sg = np.linspace(sgc, 1 - sorg, 20, endpoint=True)
    so = 1 - sg
    # Models Corey, 1954
    krw = krwro * ((sw - swir) / (1 - sorw - swir)) ** nw

    krow = kroiw * ((1 - sw - sorw) / (1 - sorw - swir)) ** nsorw

    krg = krgro * ((sg - sgc) / (1 - sgc - sorg - swir)) ** ng
    krg[krg >= 1] = 1

    krog = kroiw * ((1 - sg - sorg - swir) / (1 - sgc - sorg - swir)) ** nog

    # Stone Model I normalized by Aziz and Settari, 1979
    # swc = swir
    # Fayers and Mattews 1984
    a = 1 - (sg / (1 - swir - sorg))
    som = (a * sorw) + ((1 - a) * sorg)
    s_o = np.abs(so - som) / (1 - swir - som)  # so>= som
    s_w = np.abs(sw - swir) / (1 - swir - som)  # sw >= swir
    s_g = (sg) / (1 - swir - som)
    s_o[s_o >= 1.0] = 1 - swir
    s_w[s_w >= 1.0] = 1 - sorw
    s_g[s_g >= 1.0] = 1 - sorg
    kro0 = kroiw
    kro = (s_o / kro0) * (krow / (1 - s_w)) * (krog / (1 - s_g))
    kro[kro >= 1] = 1
    return sw, krw, sg, krg, so, kro


if __name__ == '__main__':
    try:
        sw, krw, sg, krg, so, kro = stone_model_I(swir=0.1, sorg=0.1, sorw=0.1, sgc=0.1, krwro=0.9, kroiw=1, krgro=0.9,
                                                  nw=2,
                                                  nsorw=2, ng=2, nog=2)


        def f(fig):
            ax = fig.subplots()
            ax.plot(sw, krw)
            ax.plot(sg, krg)
            ax.plot(so, kro)


        from zml import plot

        plot(f)
    except Exception as err:
        print(err)
