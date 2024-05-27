def less(x, y):
    return x < y


def is_sorted(vx, compare=None):
    if compare is None:
        compare = less
    for i in range(len(vx) - 1):
        if not compare(vx[i], vx[i + 1]):
            return False
    return True


def test():
    x = [1, 2, 3]
    print(is_sorted(x))

    y = [2, 3, 1]
    print(is_sorted(y))

    z = [3, 2, 1]
    print(is_sorted(z, compare=lambda a, b: a > b))


if __name__ == '__main__':
    test()

