"""几何基础模块（聚合导出点/线段/矩形/三角形的所有函数）.

Modified by Claude, 2026-08-12
"""
from zmlx.geometries.point import get_angle, get_norm
from zmlx.geometries.point import point_distance
from zmlx.geometries.segment import get_seg_angle, get_center, seg_intersection, seg_point_distance
from zmlx.geometries.triangle import get_area as triangle_area

_keep = [triangle_area, point_distance, seg_point_distance, get_angle, get_norm,
         get_seg_angle, get_center, seg_intersection]
