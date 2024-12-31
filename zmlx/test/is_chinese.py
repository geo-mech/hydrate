import unittest

from zml import is_chinese


class TestIsChinese(unittest.TestCase):

    def test_is_chinese(self):
        # 包含中文的字符串
        self.assertTrue(is_chinese("你好"))
        # 不包含中文的字符串
        self.assertFalse(is_chinese("hello"))
        # 空字符串
        self.assertFalse(is_chinese(""))
        # 只有中文的字符串
        self.assertTrue(is_chinese("中国"))
        # 包含中文和其他字符的字符串
        self.assertTrue(is_chinese("中文 123"))


if __name__ == '__main__':
    unittest.main()
