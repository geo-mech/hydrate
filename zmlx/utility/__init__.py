"""
在上一个版本中，类的名字和模块的名字是相同的，这容易产生问题。后续，模块的名字将采用Python建议
的小写，并逐渐（2026-4-16之后）弃用之前的模块名字。
"""

from zmlx.exts import SelfPath
from zmlx.utility.attr_keys import AttrKeys, add_keys
from zmlx.utility.capillary_effect import CapillaryEffect
from zmlx.utility.fields import Field, LinearField
from zmlx.utility.gui_iterator import GuiIterator
from zmlx.utility.interp import load_field3, Interp2, Interp3
from zmlx.utility.pressure_controller import PressureController
from zmlx.utility.runtime_fn import RuntimeFunc
from zmlx.utility.save_manager import SaveManager
from zmlx.utility.seepage_cell_monitor import SeepageCellMonitor
from zmlx.utility.frame_rate_ctrl import FrameRateCtrl
from zmlx.utility.heat_injector import HeatInjector

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
