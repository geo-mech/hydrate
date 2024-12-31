# ** desc = '竖直方向二维的水合物开发过程'
from zml import Vector, Interp1, Seepage
from zmlx import clamp
from zmlx.config import seepage, hydrate, step_iteration
from zmlx.geometry.point_distance import point_distance
from zmlx.seepage_mesh.add_cell_face import add_cell_face
from zmlx.seepage_mesh.hydrate import create_xz


def create():
    """
    创建模型
    """
    mesh = create_xz(x_max=50, z_min=-100, z_max=0, dx=1, dz=1,
                     upper=30, lower=30)

    # 添加虚拟的cell和face用于生产
    add_cell_face(mesh, pos=[0, 0, -50],
                  offset=[0, 10, 0],
                  vol=1000,
                  area=5, length=1)

    # 找到上下范围，从而去找到顶底的边界
    z_min, z_max = mesh.get_pos_range(2)

    def is_upper(x, y, z):
        return abs(z - z_max) < 0.01

    def is_lower(x, y, z):
        return abs(z - z_min) < 0.01

    def is_prod(x, y, z):
        return abs(y - 10) < 0.1

    def get_s(x, y, z):
        if is_prod(x, y, z) or z > -30 or z < -70:
            return {'h2o': 1}
        else:
            return {'h2o': 0.6, 'ch4_hydrate': 0.4}

    def get_k(x, y, z):
        if z > -30 or z < -70:
            return 1.0e-15
        else:
            return 1.0e-14

    def get_p(x, y, z):
        return 10e6 - z * 1e4

    def get_t(x, y, z):
        return 285 - z * 0.04

    def denc(*pos):
        return 1e20 if is_upper(*pos) or is_lower(*pos) else 5e6

    def get_fai(x, y, z):
        if is_upper(x, y, z):  # 顶部固定压力
            return 1.0e10
        else:
            return 0.3

    def heat_cond(x, y, z):  # 确保不会有热量通过用于生产的虚拟的cell传递过来.
        return 1.0 if abs(y) < 2 else 0.0

    # 关键词
    kw = hydrate.create_kwargs(gravity=[0, 0, -10],
                               dt_min=1,
                               dt_max=24 * 3600,
                               dv_relative=0.1,
                               mesh=mesh,
                               porosity=get_fai,
                               pore_modulus=100e6,
                               denc=denc,
                               temperature=get_t,
                               p=get_p,
                               s=get_s,
                               perm=get_k,
                               heat_cond=heat_cond,
                               prods=[{'index': mesh.cell_number - 1,
                                       't': [0, 1e20],
                                       'p': [3e6, 3e6]}]
                               )
    model = seepage.create(**kw)

    # 从index = 10开始，逐步添加90个kr，每一个缩减1%，这样，在后续可以在各个face的位置，根据
    # 阻力的大小，选择合适的kr
    for idx in range(90):
        # kr缩减的比例
        ratio = 1.0 - 0.01 * idx
        x, y = model.get_kr(index=1).get_data()
        assert isinstance(x, Vector) and isinstance(y, Vector)
        for i in range(len(y)):
            y[i] = y[i] * ratio
        model.set_kr(index=idx + 10, kr=Interp1(x=x, y=y))

    # 在各个face位置，对于水，初始先择第10个kr，即缩减的比例为0
    for face in model.faces:
        assert isinstance(face, Seepage.Face)
        face.set_ikr(index=1, value=10)

    step_iteration.add_setting(model,
                               step=5,
                               name='update_ikr',
                               args=['@model'])

    # 用于solve的选项
    model.set_text(key='solve',
                   text={'monitor': {'cell_ids': [model.cell_number - 1]},
                         'show_cells': {'dim0': 0,
                                        'dim1': 2,
                                        'mask': seepage.get_cell_mask(model=model, yr=[-1, 1])},
                         'time_max': 3 * 365 * 24 * 3600,
                         }
                   )
    # 返回模型
    return model


def get_ikr(ratio):
    """
    给定需要矫正的比例，返回所需要选择的kr的index
    """
    return clamp(round((1.0 - ratio) / 0.01 + 10), 10, 99)


def update_ikr(model: Seepage):
    """
    根据各个face两侧的压力差，更新对于face需要选择的kr
    """
    for face in model.faces:
        assert isinstance(face, Seepage.Face)
        c0, c1 = face.get_cell(0), face.get_cell(1)
        p0, p1 = c0.pre, c1.pre
        z0, z1 = c0.z, c1.z
        dist = point_distance(c0.pos, c1.pos)
        grad = abs(p0 + 10 * z0 - p1 - 10 * z1) / dist
        # 下面，根据梯度，计算需要修正的比例
        ratio = clamp(grad / 2e5, 0, 1)
        i0 = face.get_ikr(index=1)
        i1 = get_ikr(ratio)
        if i1 > i0:
            face.set_ikr(index=1, value=clamp(i0 + 1, 10, 99))
            continue
        if i1 < i0:
            face.set_ikr(index=1, value=clamp(i0 - 1, 10, 99))
            continue


def main():
    model = create()
    slots = {'update_ikr': update_ikr}
    seepage.solve(model, close_after_done=True, slots=slots)


if __name__ == '__main__':
    main()
