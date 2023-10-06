from zmlx.pg.plot3 import *
import time
import numpy as np

g = Grid()

pos = np.empty((53, 3))
size = np.empty((53))
color = np.empty((53, 4))
pos[0] = (1, 0, 0)
size[0] = 0.5
color[0] = (1.0, 0.0, 0.0, 0.5)
pos[1] = (0, 1, 0)
size[1] = 0.2
color[1] = (0.0, 0.0, 1.0, 0.5)
pos[2] = (0, 0, 1)
size[2] = 2. / 3.
color[2] = (0.0, 1.0, 0.0, 0.5)

z = 0.5
d = 6.0
for i in range(3, 53):
    pos[i] = (0, 0, z)
    size[i] = 2. / d
    color[i] = (0.0, 1.0, 0.0, 0.5)
    z *= 0.5
    d *= 2.0

sp1 = Scatter(pos=pos, size=size, color=color, pxMode=False)
sp1.translate(5, 5, 0)

pos = np.random.random(size=(100000, 3))
pos *= [10, -10, 10]
pos[0] = (0, 0, 0)
color = np.ones((pos.shape[0], 4))
d2 = (pos ** 2).sum(axis=1) ** 0.5
size = np.random.random(size=pos.shape[0]) * 10
sp2 = Scatter(pos=pos, color=(1, 1, 1, 1), size=size)
phase = 0.

pos3 = np.zeros((100, 100, 3))
pos3[:, :, :2] = np.mgrid[:100, :100].transpose(1, 2, 0) * [-0.1, 0.1]
pos3 = pos3.reshape(10000, 3)
d3 = (pos3 ** 2).sum(axis=1) ** 0.5
sp3 = Scatter(pos=pos3, color=(1, 1, 1, .3), size=0.1, pxMode=False)


def update():
    # update volume colors
    global phase, sp2, d2
    s = -np.cos(d2 * 2 + phase)
    color = np.empty((len(d2), 4), dtype=np.float32)
    color[:, 3] = np.clip(s * 0.1, 0, 1)
    color[:, 0] = np.clip(s * 3.0, 0, 1)
    color[:, 1] = np.clip(s * 1.0, 0, 1)
    color[:, 2] = np.clip(s ** 3, 0, 1)
    sp2.setData(color=color)
    phase -= 0.1

    # update surface positions and colors
    global sp3, d3, pos3
    z = -np.cos(d3 * 2 + phase)
    pos3[:, 2] = z
    color = np.empty((len(d3), 4), dtype=np.float32)
    color[:, 3] = 0.3
    color[:, 0] = np.clip(z * 3.0, 0, 1)
    color[:, 1] = np.clip(z * 1.0, 0, 1)
    color[:, 2] = np.clip(z ** 3, 0, 1)
    sp3.setData(pos=pos3, color=color)


def main():
    set_distance(20)
    for item in (g, sp1, sp2, sp3):
        add_item(item)

    for i in range(1000):
        gui.break_point()
        update()
        time.sleep(0.01)


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
