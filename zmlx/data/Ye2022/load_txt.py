import os

import numpy as np


def load_txt(name):
    return np.loadtxt(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'raw'), name))
