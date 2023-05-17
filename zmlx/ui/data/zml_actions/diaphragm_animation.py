import os
import time

import matplotlib.tri as tri
import numpy as np

import zml

xy = np.loadtxt('nodes.txt')
x = xy[:, 0]
y = xy[:, 1]

triangulation = tri.Triangulation(x, y)
print(triangulation)


def plot(file):
    data = np.loadtxt(file)
    v0 = data[:, 0]
    v1 = data[:, 1]
    v2 = data[:, 2]

    def f(fig, z):
        ax = fig.subplots()
        ax.set_aspect('equal')
        ax.set_xlabel('x/m')
        ax.set_ylabel('y/m')
        contour = ax.tricontourf(triangulation, z, levels=20, cmap='coolwarm', antialiased=True)
        fig.colorbar(contour, ax=ax)

    zml.plot(kernel=lambda fig: f(fig, v0), caption='膜片位置', clear=True)
    # zml.plot(kernel=lambda fig: f(fig, v1), caption='油压', clear=True)
    # zml.plot(kernel=lambda fig: f(fig, v2), caption='气压', clear=True)


def run():
    for file in os.listdir('nodes'):
        path = os.path.join('nodes', file)
        print(path)
        plot(path)
        time.sleep(0.1)


zml.gui.execute(run, keep_cwd=True, close_after_done=False)
