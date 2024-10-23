import unittest


def less(x, y):
    """
    比较两个数的大小

    参数:
    x: 要比较的第一个数。
    y: 要比较的第二个数。

    返回:
    bool: 如果 x 小于 y，则返回 True，否则返回 False。
    """
    return x < y


def is_sorted(vx, compare=None):
    """
    检查列表是否已排序

    参数:
    vx (list): 要检查的列表。
    compare (function, 可选): 用于比较列表元素的函数。如果未提供，则使用默认的小于比较。

    返回:
    bool: 如果列表已排序则返回 True，否则返回 False。

    异常:
    ValueError: 如果 compare 参数不是一个函数。
    """
    if compare is not None and not callable(compare):
        raise ValueError("compare should be a function")
    if compare is None:
        compare = less
    for i in range(len(vx) - 1):
        if not compare(vx[i], vx[i + 1]):
            return False
    return True


class TestIsSorted(unittest.TestCase):

    def test_sorted_list(self):
        # 测试已排序的列表
        vx = [1, 2, 3, 4, 5]
        self.assertTrue(is_sorted(vx))

    def test_unsorted_list(self):
        # 测试未排序的列表
        vx = [5, 4, 3, 2, 1]
        self.assertFalse(is_sorted(vx))

    def test_custom_compare_function(self):
        # 测试自定义比较函数
        def custom_compare(a, b):
            return a % 2 == b % 2

        vx = [2, 4, 6, 8, 10]
        self.assertTrue(is_sorted(vx, custom_compare))

    def test_invalid_compare_parameter(self):
        # 测试无效的比较参数
        vx = [1, 2, 3]
        with self.assertRaises(ValueError):
            is_sorted(vx, 123)


if __name__ == '__main__':
    unittest.main()

