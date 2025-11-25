"""
计算各个face的位置流体压力的梯度，并作为一个numpy的数组返回
"""

from zmlx.base.seepage import as_numpy
from zmlx.base.zml import Seepage, get_pointer64 as pointer


def get_face_pressure_gradient(model: Seepage, fluid=None):
    """
    计算各个face的位置流体压力的梯度，并作为一个numpy的数组返回。
    如果给定了流体，则会排除掉流体的静水压力，从而获得能够驱动流体流动的压力梯度
    """
    result = model.get_face_gradient(ca=pointer(as_numpy(model).cells.pre))
    if fluid is not None:
        density = model.get_face_average(
            ca=pointer(as_numpy(model).fluids(fluid).den))
        faces = as_numpy(model).faces
        result -= faces.gravity * density / faces.dist
    return result


def test_1():
    from zmlx.base.zml import np
    from zmlx.config import seepage
    from zmlx.seepage_mesh.cube import create_cube

    mesh = create_cube(x=np.linspace(0, 3, 3),
                       y=(-0.5, 0.5),
                       z=np.linspace(0, 3, 5)
                       )

    def get_p(x, y, z):
        return 5e6 - 1e4 * z + 100 * x

    model = seepage.create(mesh, p=get_p,
                           s={'h2o': 1},
                           fludefs=[Seepage.FluDef(den=1000, name='h2o')],
                           gravity=(0, 0, -10))

    print(get_face_pressure_gradient(model))
    grad_p = get_face_pressure_gradient(model, fluid='h2o')
    print(grad_p)
    print(model.get_cell_max(fa=pointer(grad_p)))


if __name__ == '__main__':
    test_1()
