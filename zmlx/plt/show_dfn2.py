# -*- coding: utf-8 -*-


from zml import Dfn2
from zmlx.plt.plot2 import plot2


def show_dfn2(dfn2, **kwargs):
    """
    利用画线的方式显示一个二维的离散裂缝网络
    """
    data = []
    for row in dfn2:
        x0 = row[0]
        y0 = row[1]
        x1 = row[2]
        y1 = row[3]
        d = {'name': 'plot', 'args': [[x0, x1], [y0, y1]]}
        data.append(d)

    kwargs['aspect'] = 'equal'
    plot2(data=data, **kwargs)


def __test(opath=None, show=False, angle=None, length=None,
           pos_range=None, p21=None, lmin=None):
    """
    创建二维的DFN模型，并将它保存到给定的文件.
    返回二维DFN对象
    """
    if length is None:
        length = [float(i) + 10.0 for i in range(51)]
    if angle is None:
        angle = [0, 1.5]
    dfn = Dfn2()
    if pos_range is None:
        dfn.range = [-75, -250, 75, 250]
    else:
        dfn.range = pos_range
    if p21 is None:
        p21 = 0
    if lmin is None:
        lmin = -1
    dfn.add_frac(angles=angle, lengths=length, p21=p21, l_min=lmin)

    if opath is not None:
        dfn.print_file(opath)
        print(f'dfn2 is printed to file: <{opath}>')

    data = [dfn.get_fracture(i) for i in range(dfn.fracture_n)]

    if show:
        show_dfn2(data, caption='Dfn2')

    return data


if __name__ == '__main__':
    __test(show=True, p21=0.2, lmin=2, pos_range=[-100, -100, 100, 100])
