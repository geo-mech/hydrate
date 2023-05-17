# -*- coding: utf-8 -*-


def clamp(value, left=None, right=None):
    """
    对于给定值，将它限定在给定的范围内
    """
    if left is None and right is None:
        return value
    if left is None:
        return min(value, right)
    if right is None:
        return max(value, left)
    if left < right:
        return max(left, min(right, value))
    else:
        return max(right, min(left, value))


if __name__ == '__main__':
    print(clamp(3, 4, 5))
    print(clamp(3, 5, 4))
    print(clamp(6, 5, 4))
    print(clamp(4, 5, 4))
    print(clamp(4.5, 5, 4))
