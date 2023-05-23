from zmlx.alpha.hf2.Attrs import *


def save_c14(path, model, get_c=None, get_a=None, is_used=None):
    """
    将渗流模型保存为14列的数据，用于Matlab绘图
    """
    assert isinstance(model, Seepage)
    ca = CellAttrs(model)
    idx12 = [ca.x0, ca.x1, ca.x2, ca.x3,
             ca.y0, ca.y1, ca.y2, ca.y3,
             ca.z0, ca.z1, ca.z2, ca.z3]

    with open(make_parent(path), 'w') as file:
        for cell in model.cells:
            if is_used is not None:
                if not is_used(cell):
                    continue
            for i in idx12:
                value = cell.get_attr(i)
                if value is None:
                    file.write('0\t')
                else:
                    file.write(f'{value}\t')
            if get_c is not None:
                file.write(f'{get_c(cell)}\t')
            else:
                file.write(f'{cell.pre}\t')
            if get_a is not None:
                file.write(f'{get_a(cell)}\n')
            else:
                file.write(f'{cell.fluid_vol}\n')


