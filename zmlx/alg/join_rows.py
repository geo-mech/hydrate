import warnings

import numpy as np

from zmlx.alg.utils import join_rows

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)




def test():
    a = np.array([[1, 2], [3, 4]])
    b = np.array([[5, 6]])

    combined_matrix = join_rows(a, b)
    print(combined_matrix)


if __name__ == '__main__':
    test()
