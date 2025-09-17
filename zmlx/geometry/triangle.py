try:
    import numpy as np
except ImportError:
    np = None


def get_area(a, b, c):
    """
    get the area of a triangle by the length of its edge.
        see: http://baike.baidu.com/view/1279.htm
    """
    p = (a + b + c) / 2
    p = p * (p - a) * (p - b) * (p - c)
    return p ** 0.5 if p > 0 else 0


def _dist(p1, p2):
    """
    Returns the distance between two points
    """
    return np.linalg.norm(
        np.asarray(p1, dtype=np.float64) - np.asarray(p2, dtype=np.float64))


def get_area_by_vertices(a, b, c):
    """
    get the area of a triangle by the vertices.
    """
    return get_area(
        _dist(a, b), _dist(b, c), _dist(c, a))


if __name__ == '__main__':
    print(get_area(3, 4, 5))
    print(get_area_by_vertices([0, 0, 0], [1, 0, 0], [0, 1, 0]))
