import zmlx.alg.sys as warnings

warnings.warn(
    f'The {__name__} is deprecated, please use the "path.py" in the '
    f'same folder instead. This file will be removed after 2027-5-25',
    DeprecationWarning, stacklevel=2)

from zmlx.exts import SelfPath

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
