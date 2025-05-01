import unittest
import warnings

from zmlx.alg.utils import is_sorted

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)




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
