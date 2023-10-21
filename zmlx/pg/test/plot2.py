import time

import numpy as np

from zmlx.pg.plot2 import *


def test1():
    plot(title="Basic array plotting", y=np.random.normal(size=100))


def test2():
    plot(np.random.normal(size=100), pen=(255, 0, 0), name="Red curve")
    plot(np.random.normal(size=110) + 5, pen=(0, 255, 0), name="Green curve")
    plot(np.random.normal(size=120) + 10, pen=(0, 0, 255), name="Blue curve")


def test3():
    plot(np.random.normal(size=100), pen=(200, 200, 200), symbolBrush=(255, 0, 0), symbolPen='w')


def test4():
    x = np.cos(np.linspace(0, 2 * np.pi, 1000))
    y = np.sin(np.linspace(0, 4 * np.pi, 1000))
    plot(x, y)
    show_grid(x=True, y=True)


def test5():
    p5 = plot(caption='Zhang')
    x = np.random.normal(size=1000) * 1e-5
    y = x * 1000 + 0.005 * np.random.normal(size=1000)
    y -= y.min() - 1.0
    mask = x > 1e-15
    x = x[mask]
    y = y[mask]
    p5.setData(x, y, pen=None, symbol='t', symbolPen=None, symbolSize=55, symbolBrush=(100, 100, 255, 50))
    set_label('left', "Y Axis", units='A')
    set_label('bottom', "Y Axis", units='s')
    set_log_mode(x=True, y=False)


def test6():
    curve = plot(pen='y')
    data = np.random.normal(size=(10, 1000))
    ptr = 0
    for step in range(50000):
        gui.break_point()
        curve.setData(data[ptr % 10])
        if ptr == 0:
            enable_auto_range('xy', False)  # stop auto-scaling after the first data set is plotted
        ptr += 1
        time.sleep(0.01)


def test7():
    y = np.sin(np.linspace(0, 10, 1000)) + np.random.normal(size=1000, scale=0.1)
    plot(y, fillLevel=-0.3, brush=(50, 50, 200, 100))
    show_axis('bottom', False)


def test8():
    x2 = np.linspace(-100, 100, 1000)
    data2 = np.sin(x2) / x2
    plot(data2, pen=(255, 255, 255, 200))
    lr = pg.LinearRegionItem([400, 700])
    lr.setZValue(-10)
    add_item(lr)


def test9():
    set_axis_items(axisItems={'bottom': pg.DateAxisItem()})
    show_grid(x=True, y=True)
    now = time.time()
    x = np.linspace(2 * np.pi, 1000 * 2 * np.pi, 8301)
    plot(now - (2 * np.pi / x) ** 2 * 100 * np.pi * 1e7, np.sin(x), symbol='o')


def test10():
    plt1 = plot(caption='A')
    plt2 = plot(caption='B')

    # make interesting distribution of values
    vals = np.hstack([np.random.normal(size=500), np.random.normal(size=260, loc=4)])

    # compute standard histogram
    y, x = np.histogram(vals, bins=np.linspace(-3, 8, 40))

    # Using stepMode="center" causes the plot to draw two lines for each sample.
    # notice that len(x) == len(y)+1
    plt1.setData(x, y, stepMode="center", fillLevel=0, fillOutline=True, brush=(0, 0, 255, 150))

    # Now draw all points as a nicely-spaced scatter plot
    y = pg.pseudoScatter(vals, spacing=0.15)
    # plt2.plot(vals, y, pen=None, symbol='o', symbolSize=5)
    plt2.setData(vals, y, pen=None, symbol='o', symbolSize=5, symbolPen=(255, 255, 255, 200),
                 symbolBrush=(0, 0, 255, 150))


def test11():
    s4 = pg.ScatterPlotItem(
        size=10,
        pen=pg.mkPen(None),
        brush=pg.mkBrush(255, 255, 255, 20),
        hoverable=True,
        hoverSymbol='s',
        hoverSize=15,
        hoverPen=pg.mkPen('r', width=2),
        hoverBrush=pg.mkBrush('g'),
    )
    n = 10000
    pos = np.random.normal(size=(2, n), scale=1e-9)
    s4.addPoints(
        x=pos[0],
        y=pos[1],
        # size=(np.random.random(n) * 20.).astype(int),
        # brush=[pg.mkBrush(x) for x in np.random.randint(0, 256, (n, 3))],
        data=np.arange(n)
    )
    add_item(s4)


if __name__ == '__main__':
    gui.execute(test2, close_after_done=False)
