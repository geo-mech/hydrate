def get_average2(l1, k1, l2, k2):
    """
    获得两段串联的平均值.
    """
    assert l1 > 0 and l2 > 0
    if k1 <= 0 or k2 <= 0:
        return 0
    else:
        return k1 * k2 * (l1 + l2) / (l1 * k2 + l2 * k1)


def get_average(*perm):
    """
    返回多段（长度相等）串联的平均的渗透率.
    """
    assert len(perm) > 0
    k1 = perm[0]
    l1 = 1
    for i in range(1, len(perm)):
        k2 = perm[i]
        l2 = 1
        k1 = get_average2(l1, k1, l2, k2)
        l1 += l2
    return k1


def test():
    perm = [10, 1, 0.1]
    print(get_average(*perm))


if __name__ == '__main__':
    test()
