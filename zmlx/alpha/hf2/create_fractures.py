from zmlx.alpha.hf2.Attrs import *
from zmlx.alpha.hf2 import dfn_v3
from zmlx.alg.opath import opath
import os
from zmlx.alpha.hf2.save_c14 import save_c14
from zmlx.alg.linspace import linspace


def create_fractures(fpath=None):
    """
    创建用于计算的天然裂缝，并且缓存到文件中。之所以有这个函数，是因为要计算裂缝之间的位置关系，这非常耗时，
    特别是用Python来实现。因此，缓存以备用.
    ---
        Cell具有如下属性:
            位置 pos
            面积 s
            三维矩形 rect3
            -- 其它所有的Cell属性均未设置.

        Face所有属性均没有设置
            仅添加Face，没有进行任何初始化.
    """
    if fpath is None:
        fpath = opath('hf2', 'fractures.xml')

    model = Seepage()
    if fpath is not None:
        if os.path.isfile(fpath):
            model.load(fpath)
            print(f'Load fracture model from <{fpath}>, model = {model}')
            return model

    ca = CellAttrs(model)
    fa = FaceAttrs(model)

    dfn_v3.add_fracture(model, f3=[0, -150, -25, 0, 150, 25], dx=3, dy=2)

    for cell in model.cells:
        ca.set_tag(cell, 1)
    for face in model.faces:
        fa.set_tag(face, 1)

    cell_n0 = model.cell_number
    face_n0 = model.face_number

    fx = dfn_v3.create(p21=0.3, angles=linspace(-0.2, 0.2, 100), lengths=linspace(10, 20, 100))
    fy = dfn_v3.create(p21=0.7, angles=linspace(1.57 - 0.2, 1.57 + 0.2, 100), lengths=linspace(20, 40, 100))

    dfn_v3.add_fractures(model, fx + fy)

    for idx in range(cell_n0, model.cell_number):
        ca.set_tag(model.get_cell(idx), 2)
    for idx in range(face_n0, model.face_number):
        fa.set_tag(model.get_face(idx), 2)

    if fpath is not None:
        model.save(fpath)
        print(f'fracture model saved to <{fpath}>')

    return model


if __name__ == '__main__':
    from random import uniform
    m = create_fractures()
    ca = CellAttrs(m)
    def get_c(c):
        return uniform(0, 1) + ca.get_tag(c) * 5

    def is_used(c):
        return ca.get_tag(c) == 2

    save_c14(opath('hf2', 'fractures.c14'), m, is_used=is_used)

