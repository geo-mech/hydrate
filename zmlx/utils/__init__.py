"""通用工具包（``zmlx.utils``）.

⚠️ **目录名是 ``utils``（不是 ``utility``）**。2026-10-16 由 ``zmlx.utility`` 改名而来；
旧包名 ``zmlx.utils`` 保留为**兼容垫片**（导入即发 :class:`DeprecationWarning`，
**2027-10-16 删除**），zmlx 内部代码一律只用 ``zmlx.utils``。

为什么改名
----------

与 ``zmlx/ui/utils`` 一致，全仓统一用 **``utils``** 这个拼写（``utility`` 只是它的同义词，
两种写法在同一棵树里并存只会让人犹豫该用哪个）。

⚠️ **与 ``zmlx.ui.utils`` 的区别**（两个都叫 utils，别混）：

======================  ==========================================================
包                       内容
======================  ==========================================================
``zmlx.utils``           通用工具：字段 / 插值 / 存盘 / 迭代器控制 / 物性……
                         （**与界面无关**，纯计算与 IO）
``zmlx.ui.utils``        界面工具：``GuiApi`` / ``BreakPoint`` / ``TaskProc`` /
                         ``FileHandler`` / ``BackgroundTask`` / 许可答复解析
======================  ==========================================================

本包内部的「大小写模块名」
--------------------------

⚠️ 本包里还有一层**更早的**兼容：历史上类名与模块名相同（``GuiIterator.py`` 里放
``GuiIterator`` 类），后来改成 Python 建议的小写模块名（``gui_iterator.py``）。
那些大写模块名（``AttrKeys`` / ``CapillaryEffect`` / …）**当时**就留了弃用转发，
它们与本包改名是两回事 —— 本包改名时**原样保留**了它们（各自仍指向自己的小写兄弟）。

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.utility`` 改为 ``zmlx.utils``.

⚠️ **本目录 2026-10-16 由 ``zmlx.utility`` 改名为 ``zmlx.utils``**
（与 ``algs`` / ``fluids`` / ``reactions`` / ``geometries`` / ``demos`` / ``meshes`` / ``seepage_meshes`` / ``scripts`` / ``krs`` 等一批包统一用**复数**目录名 ——
``通用工具：字段 / 插值 / 存盘 / 迭代器控制 / 物性``，复数才是它实际的形态）。

⚠️ **旧名 ``zmlx.utility`` 保留为兼容垫片**（导入即发 :class:`DeprecationWarning`，
**2027-10-16 删除**）—— 那只是过渡，**将来一定会删**，所以来历记在这里（新家）。

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.utility`` 改为 ``zmlx.utils``.
"""

from zmlx.exts import SelfPath
from zmlx.utils.attr_keys import AttrKeys, add_keys
from zmlx.utils.capillary_effect import CapillaryEffect
from zmlx.utils.fields import Field, LinearField
from zmlx.utils.frame_rate_ctrl import FrameRateCtrl
from zmlx.utils.gui_iterator import GuiIterator, get_gui_iter
from zmlx.utils.heat_injector import HeatInjector
from zmlx.utils.interp import load_field3, Interp2, Interp3
from zmlx.utils.pressure_controller import PressureController
from zmlx.utils.runtime_fn import RuntimeFunc
from zmlx.utils.save_manager import SaveManager
from zmlx.utils.seepage_cell_monitor import SeepageCellMonitor

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
