# -*- coding: utf-8 -*-


from zmlx.alg.loadcol import loadcol
import os


# 文件路径
fpath = os.path.join(os.path.dirname(__file__), 'example.fn2')

# 裂缝位置
pos = loadcol(fpath, index=[0, 1, 2, 3])

# 裂缝宽度
w = loadcol(fpath, 4)

# 裂缝颜色
c = loadcol(fpath, 6)


if __name__ == '__main__':
    print(pos)
    print(w)
    print(c)
