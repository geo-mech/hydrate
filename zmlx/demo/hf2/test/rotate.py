from zml import *
import random

from zmlx.geometry.get_angle import get_angle


def test():
    tensor = Tensor2(xx=random.uniform(0, 1), yy=random.uniform(0, 1), xy=random.uniform(-1, 1))
    dx, dy = random.uniform(-1, 1), random.uniform(-1, 1)
    angle = get_angle(dx, dy)
    t2 = tensor.get_rotate(angle=angle)

    c1 = Coord2()
    c2 = Coord2(origin=[0, 0], xdir=[dx, dy])
    t3 = c2.view(c1, tensor)

    print(t2, t3)


if __name__ == '__main__':
    for i in range(100):
        test()
