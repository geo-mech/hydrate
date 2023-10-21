from zmlx.geometry.get_seg_point_distance import get_seg_point_distance


def get_cells_around_seg(seg, dist, model):
    """
    返回给定线段一定距离范围内的所有的Cell. 需要Cell定义pos属性
    """
    return [cell for cell in model.cells if get_seg_point_distance(seg, cell.pos) <= dist]


def get_cell_ids_around_seg(seg, dist, model):
    """
    返回给定线段一定距离范围内的所有的Cell的Index. 需要Cell定义pos属性
    """
    return [cell.index for cell in get_cells_around_seg(seg, dist, model)]
