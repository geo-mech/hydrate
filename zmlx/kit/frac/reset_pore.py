from zml import Seepage


def reset_pore(obj, v0: float, k: float):
    """更新孔隙弹性参数 (将所有的孔隙都设置为完全一样的。这是这个版本的一个强有力的简化)

    Args:
        obj (Seepage): 渗流模型对象
        v0 (float, optional): 当流体压力等于0时，该Cell内流体的存储空间
        k (float, optional): 流体压力增加1Pa的时候，孔隙体积的增加量(m^3)

    Returns:
        None
    """
    if isinstance(obj, Seepage.CellData):
        obj.v0, obj.k = v0, k
        return
    else:
        assert isinstance(obj, Seepage)
        for cell in obj.cells:
            cell.v0, cell.k = v0, k
