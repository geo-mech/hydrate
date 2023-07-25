def is_chinese(string):
    """
    检查整个字符串是否包含中文:
        https://blog.csdn.net/qdPython/article/details/110231244
    """
    for ch in string:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False


if __name__ == '__main__':
    ret1 = is_chinese("刘亦菲222")
    print(ret1)

    ret2 = is_chinese("123")
    print(ret2)
