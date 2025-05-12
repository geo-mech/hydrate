import warnings

from zmlx.alg.utils import code_config

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)


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
