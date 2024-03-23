def divide_list(lst, n):
    # 计算列表长度
    total_elements = len(lst)
    # 使用整除得到每个子列表的基本元素数量
    base_size = total_elements // n
    # 使用取余得到剩余的元素数量
    remainder = total_elements % n

    # 初始化结果列表
    result = []
    # 初始化当前索引
    start_index = 0

    # 循环创建子列表
    for i in range(n):
        # 确定当前子列表的大小，前remainder个子列表会多一个元素
        if i < remainder:
            end_index = start_index + base_size + 1
        else:
            end_index = start_index + base_size
            # 切片操作获取子列表
        sub_list = lst[start_index:end_index]
        # 将子列表添加到结果列表中
        result.append(sub_list)
        # 更新下一个子列表的起始索引
        start_index = end_index

    return result


def test1():
    # 示例用法
    original_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    n = 3
    divided_lists = divide_list(original_list, n)
    print(divided_lists)


def test2():
    # 示例用法
    original_list = []
    n = 3
    divided_lists = divide_list(original_list, n)
    print(divided_lists)


def test3():
    # 示例用法
    original_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    n = 20
    divided_lists = divide_list(original_list, n)
    print(divided_lists)


if __name__ == '__main__':
    test3()
