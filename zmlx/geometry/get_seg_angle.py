from zmlx.geometry.get_angle import get_angle


def get_seg_angle(x0, y0, x1, y1):
    return get_angle(x1 - x0, y1 - y0)
