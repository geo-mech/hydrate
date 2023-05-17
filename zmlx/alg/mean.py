# -*- coding: utf-8 -*-


def mean(*args):
    """
    计算给定的各个参数的平均值
    """
    n = len(args)
    if n > 0:
        return sum(args) / n


if __name__ == '__main__':
    print(mean(1, 2))
