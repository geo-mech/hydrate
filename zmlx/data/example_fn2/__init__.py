# -*- coding: utf-8 -*-


from zmlx.alg.loadcol import loadcol
import os

__fname = os.path.join(os.path.dirname(__file__), 'example.fn2')
pos = loadcol(__fname, index=[0, 1, 2, 3])
w = loadcol(__fname, 4)
c = loadcol(__fname, 6)

if __name__ == '__main__':
    print(pos)
    print(w)
    print(c)
