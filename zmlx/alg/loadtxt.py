# -*- coding: utf-8 -*-


import os


def loadtxt(fname, dtype=float):
    """
    从给定的数据文件导入数据
    """
    if not os.path.isfile(fname):
        return []
    data = []
    try:
        with open(fname, 'r') as file:
            for line in file.readlines():
                try:
                    vx = [dtype(x) for x in line.split()]
                    if len(vx) > 0:
                        data.append(vx)
                except:
                    pass
    except:
        pass
    return data

