from zmlx.exts import SelfPath
from zmlx.geometry.base import *

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
