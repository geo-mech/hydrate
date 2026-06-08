"""
计算各个face的位置流体压力的梯度，并作为一个numpy的数组返回
"""

from zmlx.exts import FluDef, const_f64_ptr
from zmlx.tfc._sand import get_face_pressure_gradient

_keep = [get_face_pressure_gradient]

import zmlx.alg.sys as warnings

warnings.warn(f'{__name__} will be removed after 2027-5-25', DeprecationWarning, stacklevel=2)


def test_1():
    from zmlx.exts import np
    from zmlx import tfc
    from zmlx.seepage_mesh.cube import create_cube
    assert np is not None

    mesh = create_cube(
        x=np.linspace(0, 3, 3),
        y=(-0.5, 0.5),
        z=np.linspace(0, 3, 5)
    )

    def get_p(x, y, z):
        return 5e6 - 1e4 * z + 100 * x

    model = tfc.create(
        mesh, p=get_p,
        s={'h2o': 1},
        fludefs=[FluDef(den=1000, name='h2o')],
        gravity=(0, 0, -10))

    print(get_face_pressure_gradient(model))
    grad_p = get_face_pressure_gradient(model, fluid='h2o')
    print(grad_p)
    print(model.get_cell_max(fa=const_f64_ptr(grad_p)))


if __name__ == '__main__':
    test_1()
