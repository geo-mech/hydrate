# -*- coding: utf-8 -*-


import os
from zml import is_array
import warnings


def load_col(fname, index=0, dtype=float):
    """
    从给定的数据文件导入一列数据。 其中index为列的编号
    """
    if not os.path.isfile(fname):
        return []
    data = []
    with open(fname, 'r') as file:
        for line in file.readlines():
            try:
                vx = [dtype(x) for x in line.split()]
                if is_array(index):
                    vy = [vx[i] for i in index if i < len(vx)]
                    if len(vy) == len(index):
                        data.append(vy)
                else:
                    if index < len(vx):
                        data.append(vx[index])
            except Exception as err:
                warnings.warn(f'meet Exception: {err} in load_col when fname={fname} and index = {index}')
    return data
