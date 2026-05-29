from zmlx.exts import SelfPath
from zmlx.geometry.base import *
from zmlx.geometry.base import point_distance as get_distance

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
