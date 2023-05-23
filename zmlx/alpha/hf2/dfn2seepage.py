from zml import Seepage
from zmlx.alpha.hf2 import dfn_v3
from zmlx.alg.get_frac_cond import get_frac_cond
from zmlx.alpha.hf2 import CellKeys, FaceKeys


def dfn2seepage(path=None, dfn3=None):
    """
    根据天然裂缝模型，创建相应的渗流模型. 注意这个新创建的渗流模型的流体是空的.
    """
    if dfn3 is None:
        if path is None:
            dfn3 = dfn_v3.create()
            print(f'dfn3 created. count = {len(dfn3)}')
        else:
            dfn3 = dfn_v3.load(path)
            print(f'dfn3 loaded. count = {len(dfn3)}')
    assert dfn3 is not None
    assert len(dfn3) > 0

    seepage = Seepage()

    dfn_v3.add_fractures(seepage, dfn3, ca_s=CellKeys.s, **CellKeys.kw12)
    cells = seepage.numpy.cells
    cells.v0 = 0  # 压力为0的时候，裂缝宽度为0
    area = cells.get(CellKeys.s)
    cells.k = area * 1.0e-8  # 1MPa的流体压力，张开1cm的缝宽
    cells.set(CellKeys.v0, area * 0.01)  # 缝宽1cm的时候的体积
    g = get_frac_cond(1.0e-3, 1.0, 1.0, 1.0) * 10.0  # 1cm缝宽对应导流系数
    seepage.numpy.faces.set(FaceKeys.g0, g)

    return seepage


if __name__ == '__main__':
    print(dfn2seepage())
