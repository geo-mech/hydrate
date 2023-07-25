from zmlx.geometry.get_seg_point_distance import get_seg_point_distance


def get_faces_around_seg(seg, dist, model):
    """
    返回给定线段一定距离范围内的所有的face. 需要face定义pos属性
    """
    return [face for face in model.faces if get_seg_point_distance(seg, face.pos) <= dist]


def get_face_ids_around_seg(seg, dist, model):
    """
    返回给定线段一定距离范围内的所有的face的Index. 需要face定义pos属性
    """
    return [face.index for face in get_faces_around_seg(seg, dist, model)]
