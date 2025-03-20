from zmlx.alg.code_config import code_config


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
