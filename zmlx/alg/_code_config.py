from typing import List, Optional, Dict, Any

from zmlx.alg._extract_comments import extract_comments


def code_config(path: Optional[str] = None, encoding: Optional[str] = None, text: Optional[str] = None,
                line_by_line: bool = False) -> Dict[str, Any]:
    """
    获取脚本中的配置信息.
    脚本中的配置信息以 # ** 开头，后面的内容为python代码.
    Args:
        path: 脚本路径
        encoding: 脚本编码
        text: 脚本内容
        line_by_line: 是否按行处理注释，默认True
    Returns:
        配置信息
    """
    if text is None and path is not None:
        from zmlx.io.text import read_text
        text = read_text(
            path=path,
            encoding='utf-8' if encoding is None else encoding,
            default=None)

    if text is None:
        return {}

    comments: List[str] = extract_comments(text)
    config = {}

    code_text = ""
    for line in comments:
        line = line.strip()
        if len(line) >= 4:
            if line[0: 4] == '# **':
                if line_by_line:
                    try:
                        exec(line[4:].strip(), None, config)
                    except Exception as e:
                        print(e)
                else:
                    code_text += line[4:].strip() + '\n'

    if not line_by_line and len(code_text) > 0:
        try:
            exec(code_text, None, config)
        except Exception as e:
            print(e)

    return config


def test():
    text = """
    # ** desc = 'The description'
    # ** area = 1
    # ** text = ("x"
    # **        "y")
    """
    cfg = code_config(text=text)
    print(cfg)


if __name__ == '__main__':
    test()
