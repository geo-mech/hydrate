import numpy as np


def point_distance(p1, p2):
    """
    Returns the distance between two points
    """
    return np.linalg.norm(np.asarray(p1) - np.asarray(p2))


if __name__ == '__main__':
    print(point_distance(p1=(0, 0, 0), p2=(1, 0, 0)))
