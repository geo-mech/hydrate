from zml import *


def get_outcrop(disc, box=None, coords=None, attr_id=None):
    """
    对于圆盘数据，返回它的露头数据<在一个立方体上面的露头>. 当coords给定的时候，则直接返回和这个坐标系的交线，否则，将根据给定的
    box来计算6个坐标系
    """
    if coords is None:
        x0, y0, z0, x1, y1, z1 = box
        coords = [Coord3(origin=(x0, 0, 0), xdir=(0, 1, 0), ydir=(0, 0, 1)),
                  Coord3(origin=(x1, 0, 0), xdir=(0, 1, 0), ydir=(0, 0, 1)),
                  Coord3(origin=(0, y0, 0), xdir=(1, 0, 0), ydir=(0, 0, 1)),
                  Coord3(origin=(0, y1, 0), xdir=(1, 0, 0), ydir=(0, 0, 1)),
                  Coord3(origin=(0, 0, z0), xdir=(1, 0, 0), ydir=(0, 1, 0)),
                  Coord3(origin=(0, 0, z1), xdir=(1, 0, 0), ydir=(0, 1, 0))]

    if isinstance(disc, Disc3):
        """
        对于一个圆盘，则返回它和这几个坐标系的所有的交线
        """
        segments = []
        for coord in coords:
            temp = disc.get_intersection(coord=coord)
            if temp is not None:
                p1, p2 = temp
                seg = p1.to_list() + p2.to_list()
                if attr_id is not None:
                    seg.append(disc.get_attr(index=attr_id))
                segments.append(seg)
        return segments

    if isinstance(disc, Disc3Vec):
        """
        存在多个圆盘，则依次添加
        """
        segments = []
        for i in range(len(disc)):
            seg = get_outcrop(disc[i], box=box, coords=coords, attr_id=attr_id)
            segments = segments + seg
        return segments
