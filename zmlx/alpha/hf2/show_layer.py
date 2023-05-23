from zmlx.alpha.hf2.layers import get_middle_layer
from zmlx.alpha.hf2 import CellKeys, FracKeys
from zmlx.plt.show_fn2 import show_fn2


def show_layer(layers, network):
    show_fn2(network=network, seepage=get_middle_layer(layers),
             ca_c=CellKeys.ny, w_max=6,
             caption='Stress', fa_id=FracKeys.id)

    show_fn2(network=network, seepage=get_middle_layer(layers),
             ca_c=-11, w_max=6,
             caption='Width', fa_id=FracKeys.id)

    show_fn2(network=network, seepage=get_middle_layer(layers),
             ca_c=CellKeys.fp, w_max=6,
             caption='Pressure', fa_id=FracKeys.id)

    show_fn2(network=network, seepage=get_middle_layer(layers),
             ca_c=-5, w_max=6,
             caption='cell_k', fa_id=FracKeys.id)
