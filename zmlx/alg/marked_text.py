import re


def get_value(text, start_marker, end_marker):
    """
    获取两个标记之间的匹配内容
    Args:
        text: 原始文本字符串
        start_marker: 起始标记字符串
        end_marker: 结束标记字符串
    Returns:
        匹配到的字符串（无内容时返回None）
    Raises:
        ValueError: 当存在多个匹配时抛出异常
    """
    # 转义特殊字符，构建正则表达式模式
    pattern = re.escape(start_marker) + r'(.*?)' + re.escape(end_marker)
    matches = re.findall(pattern, text)

    if len(matches) == 0:
        return None
    elif len(matches) > 1:
        raise ValueError("Multiple matches found between '{}' and '{}'".format(start_marker, end_marker))
    else:
        return matches[0]


def set_value(text, start_marker, end_marker, new_value):
    """
    替换两个标记之间的第一个匹配内容
    Args:
        text: 原始文本字符串
        start_marker: 起始标记字符串
        end_marker: 结束标记字符串
        new_value: 要替换的新内容字符串
    Returns:
        替换后的完整文本字符串
    Raises:
        ValueError: 未找到匹配或多个匹配时抛出异常
    """
    # 转义特殊字符，构建正则表达式模式
    pattern = re.escape(start_marker) + r'(.*?)' + re.escape(end_marker)
    matches = re.findall(pattern, text)

    # 校验匹配数量
    if len(matches) == 0:
        raise ValueError("No match found between '{}' and '{}'".format(start_marker, end_marker))
    elif len(matches) > 1:
        raise ValueError("Multiple matches found between '{}' and '{}'".format(start_marker, end_marker))

    # 替换唯一匹配的内容
    replaced_text = re.sub(
        pattern,
        re.escape(start_marker) + re.escape(new_value) + re.escape(end_marker),  # 避免 new_value 含特殊字符干扰
        text,
        count=1  # 只替换第一个匹配（逻辑上此时只有一个匹配）
    )

    # 恢复 before 和 after 的原始字符（非转义形式）
    replaced_text = replaced_text.replace(re.escape(start_marker), start_marker, 1)
    replaced_text = replaced_text.replace(re.escape(end_marker), end_marker, 1)

    return replaced_text


def test_1():
    # 示例 1：正常匹配
    text = "姓名：张三，年龄：25，职业：工程师"
    print(get_value(text, "年龄：", "，"))  # 输出: 25

    # 示例 2：无匹配
    text = "无标记的文本"
    print(get_value(text, "【", "】"))  # 输出: None

    # 示例 3：多匹配报错
    text = "startAendstartBend"
    try:
        get_value(text, "start", "end")
    except ValueError as e:
        print(e)  # 输出: Multiple matches found between 'start' and 'end'


def test_2():
    # 示例 1：正常替换
    text = "姓名：张三，年龄：25，职业：工程师"
    new_text = set_value(text, "年龄：", "，", "30")
    print(new_text)  # 输出: "姓名：张三，年龄：30，职业：工程师"

    # 示例 2：无匹配报错
    text = "无标记的文本"
    try:
        set_value(text, "【", "】", "新内容")
    except ValueError as e:
        print(e)  # 输出: No match found between '【' and '】'

    # 示例 3：多匹配报错
    text = "startAendstartBend"
    try:
        set_value(text, "start", "end", "C")
    except ValueError as e:
        print(e)  # 输出: Multiple matches found between 'start' and 'end'


if __name__ == '__main__':
    test_1()
