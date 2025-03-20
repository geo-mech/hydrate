from zml import is_chinese

if __name__ == '__main__':
    ret1 = is_chinese("刘亦菲222")
    print(ret1)

    ret2 = is_chinese("123")
    print(ret2)
