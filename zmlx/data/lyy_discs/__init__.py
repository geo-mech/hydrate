# -*- coding: utf-8 -*-


from zml import *
import os

fpath = os.path.join(os.path.dirname(__file__), 'discs')

# 数据的坐标范围 [m]
xr = (-7.5, 7.5)
yr = (-7.5, 7.5)
zr = (-7.5, 7.5)


def get_text():
    return read_text(fpath)


def get_discs(set_ids=None, da_set=None):
    """
    返回所有的圆盘数据(当指定set_ids的时候，则仅仅返回该组圆盘)
    """
    discs = Disc3Vec()
    for line in get_text().splitlines():
        words = line.split()
        if len(words) == 7:
            set_id = int(words[6])
            if set_ids is None or set_id in set_ids:
                disc = Disc3.create(*[float(words[i]) for i in range(6)])
                if da_set is not None:
                    # 设置SetID的属性
                    disc.set_attr(da_set, set_id)
                discs.append(disc)
    return discs


if __name__ == '__main__':
    print(get_discs())
