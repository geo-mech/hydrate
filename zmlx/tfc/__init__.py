"""
基于流动(渗流)、传热、化学相关的功能 (TFC耦合基础)
"""

import zmlx.tfc._cap as capillary
import zmlx.tfc._cond as cond
import zmlx.tfc._diff as diffusion
import zmlx.tfc._keys as attr_keys
import zmlx.tfc._main as seepage
import zmlx.tfc._sand as sand
import zmlx.tfc._step as step_iteration
import zmlx.tfc._time as timer
import zmlx.tfc._time as timer_cfg
import zmlx.tfc._vis as adjust_vis
from zmlx.exts import SelfPath
from zmlx.tfc._keys import *
from zmlx.tfc._main import *
from zmlx.tfc._plt import show_cells

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
