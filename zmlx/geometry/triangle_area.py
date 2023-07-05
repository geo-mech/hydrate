from math import sqrt


def triangle_area(a, b, c):
    """
    get the area of a triangle by the length of its edge.
        see: http://baike.baidu.com/view/1279.htm
    """
    p = (a + b + c) / 2
    p = p * (p - a) * (p - b) * (p - c)
    return sqrt(p) if p > 0 else 0


if __name__ == '__main__':
    print(triangle_area(3, 4, 5))
