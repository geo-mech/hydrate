# -*- coding: utf-8 -*-


def linspace(start, stop, num=50):
    """
    Return evenly spaced numbers over a specified interval.
    """
    dv = (stop - start) / max(num - 1, 1)
    return [start + dv * i for i in range(num)]


if __name__ == '__main__':
    x = linspace(0, 1, 11)
    print(x)
    print(x[1:])
