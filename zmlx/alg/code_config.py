from zml import read_text


def code_config(path=None, encoding=None, text=None):
    """
    获取脚本中的配置信息.
    """
    try:
        if text is None:
            text = read_text(path=path,
                             encoding='utf-8' if encoding is None else encoding,
                             default=None)
        config = {}
        if text is not None:
            code = ""
            for line in text.splitlines():
                line = line.strip()
                if len(line) >= 4:
                    if line[0: 4] == '# **':
                        code += line[4:].strip() + '\n'
            if len(code) > 0:
                try:
                    exec(code, None, config)
                except Exception as e:
                    print(e)
        return config
    except Exception as e2:
        print(e2)
        return {}


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
