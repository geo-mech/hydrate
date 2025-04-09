import zmlx.alg.sys as warnings

from zmlx.alg.base import code_config

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)


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
