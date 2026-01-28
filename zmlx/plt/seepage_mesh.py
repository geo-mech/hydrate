from zmlx.plt.on_axes.seepage_mesh import add_seepage_mesh


def test():
    """
    测试
    """
    from zmlx import create_cube, plot, add_axes3
    import random
    import numpy as np

    mesh = create_cube(
        x=np.linspace(0, 10, 30),
        y=np.linspace(0, 20, 50),
        z=[-1, 1])

    for c in mesh.cells:
        c.vol = random.uniform(0.5, 5)
        x, y, z = c.pos
        z = np.sin(x / 5) * np.cos(y / 5) * 3
        c.pos = [x, y, z]

    plot(add_axes3, add_seepage_mesh, mesh,
         cbar=dict(label='Volume', shrink=0.5),
         gui_mode=True,
         aspect='equal', xlabel='x', ylabel='y', zlabel='z', title=f'A Seepage Mesh'
         )


if __name__ == '__main__':
    test()
