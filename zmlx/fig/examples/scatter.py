from zmlx.fig import *

def test():
    import numpy as np
    x = np.random.rand(100).tolist()
    y = np.random.rand(100).tolist()
    z = np.random.rand(100).tolist()
    c = np.random.rand(100).tolist()
    obj = axes3(
        scatter(x, y, z, c=c, cbar=dict(label='label', title='title'), cmap='coolwarm'),
        title='My Scatter',
        xlabel='x/m', ylabel='y/m', zlabel='z/m',
    )
    plt_show(obj)


if __name__ == '__main__':
    test()
