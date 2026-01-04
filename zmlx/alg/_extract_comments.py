import tokenize
from io import StringIO
from typing import List


def extract_comments(text: str) -> List[str]:
    """
    从Python代码字符串中提取所有注释

    Args:
        text: 包含Python代码的字符串

    Returns:
        包含所有注释内容的列表，每个元素是一个字符串
    """
    code_io = StringIO(text)
    tokens = tokenize.generate_tokens(code_io.readline)
    res = []
    for tok_type, tok_string, start, end, line_text in tokens:
        if tok_type == tokenize.COMMENT:
            res.append(tok_string)
    return res


def test():
    code = '''
    # 这是一个单行注释
    def example():
        """这是一个文档字符串
        可以跨多行"""
        x = 1       # 行尾注释
        y = "# 这不是注释，是字符串"
        return x + y

        #  ddd
    '''

    comments = extract_comments(code)
    for comment in comments:
        print(comment)


if __name__ == '__main__':
    test()
