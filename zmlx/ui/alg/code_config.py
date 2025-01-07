from zml import read_text


def code_config(path=None, encoding=None):
    """
    获取脚本中的配置信息
    """
    try:
        text = read_text(path=path,
                         encoding='utf-8' if encoding is None else encoding,
                         default=None)
        config = {}
        if text is not None:
            for line in text.splitlines():
                if len(line) >= 4:
                    if line[0: 4] == '# **':
                        try:
                            exec(line[4:].strip(), None, config)
                        except Exception as err:
                            print(err)
        return config
    except:
        return {}
