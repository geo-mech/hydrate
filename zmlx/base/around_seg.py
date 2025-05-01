from zmlx.geometry.utils import seg_point_distance as get_seg_point_distance


def get_cells_around_seg(seg, dist, model):
    """
    返回给定线段一定距离范围内的所有的Cell. 需要Cell定义pos属性
    """
    return [cell for cell in model.cells if
            get_seg_point_distance(seg, cell.pos) <= dist]


def get_cell_ids_around_seg(seg, dist, model):
    """
    返回给定线段一定距离范围内的所有的Cell的Index. 需要Cell定义pos属性
    """
    return [cell.index for cell in get_cells_around_seg(seg, dist, model)]


def get_faces_around_seg(seg, dist, model):
    """
    返回给定线段一定距离范围内的所有的face. 需要face定义pos属性
    """
    return [face for face in model.faces if
            get_seg_point_distance(seg, face.pos) <= dist]


def get_face_ids_around_seg(seg, dist, model):
    """
    返回给定线段一定距离范围内的所有的face的Index. 需要face定义pos属性
    """
    return [face.index for face in get_faces_around_seg(seg, dist, model)]
