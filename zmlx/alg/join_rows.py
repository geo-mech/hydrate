import zmlx.alg.sys as warnings
from zmlx.alg.base import join_rows
from zmlx.exts import np

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)


def test():
    assert np is not None
    a = np.array([[1, 2], [3, 4]])
    b = np.array([[5, 6]])

    combined_matrix = join_rows(a, b)
    print(combined_matrix)


if __name__ == '__main__':
    test()
