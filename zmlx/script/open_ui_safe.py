import sys
from os.path import dirname, abspath

sys.path.append(dirname(dirname(dirname(abspath(__file__)))))

if __name__ == "__main__":
    from zmlx import open_gui_without_setup

    open_gui_without_setup(sys.argv)
