"""
对zml中定义的压裂相关的类的功能的扩展。不针对具体的工程.
"""

from zml import FractureNetwork, Seepage


def get_fn2(network: FractureNetwork, key=None):
    """
    转化为可以用来绘图的fn2数据. 其中宽度为-dn，颜色由key指定
    """
    pos = []
    w = []
    c = []

    for fracture in network.fractures:
        pos.append(fracture.pos)
        w.append(-fracture.dn)

        # 默认情况下，显示宽度
        if key is None:
            c.append(-fracture.dn)
            continue
        if key >= 0:
            c.append(fracture.get_attr(key))
            continue
        if key == -1:
            c.append(fracture.ds)
            continue
        if key == -2:
            c.append(-fracture.dn)
            continue
        # 默认情况下，显示宽度
        c.append(-fracture.dn)
    return pos, w, c


def update_seepage_topology(model: Seepage, network: FractureNetwork,
                            z=0.0):
    """
    更新渗流模型的结构. 此渗流模型，应该为network的结构更新之前的模型.
    此函数运行之后，model中的Cell的数量将和network的Fracture的数量
    相等，并且具有相同的序号. 其中参数z为model中Cell的z坐标.
    """
    backup = model.get_copy()
    model.clear_cells_and_faces()
    while model.cell_number < network.fracture_number:
        cell = model.add_cell()
        f = network.get_fracture(index=cell.index)
        c = f.center
        cell.pos = [c[0], c[1], z]
        lex = f.flu  # 流体的表达式，接下来根据此来更新单元的数据



