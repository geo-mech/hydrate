"""流体属性定义（水、甲烷、CO2、水合物等）。

提供各种流体的 FluDef 创建函数，支持 cp/（CoolProp）和 rkt/（Reaktoro）两种计算引擎。

Modified by Claude, 2026-08-12

⚠️ **本目录 2026-10-16 由 ``zmlx.fluid`` 改名为 ``zmlx.fluids``**
（与 ``algs`` / ``utils`` / ``reactions`` / ``geometries`` / ``demos`` / ``meshes`` / ``seepage_meshes`` / ``scripts`` / ``krs`` 等一批包统一用**复数**目录名 ——
``各种流体（水、甲烷、CO2、水合物……）``，复数才是它实际的形态）。

⚠️ **旧名 ``zmlx.fluid`` 保留为兼容垫片**（导入即发 :class:`DeprecationWarning`，
**2027-10-16 删除**）—— 那只是过渡，**将来一定会删**，所以来历记在这里（新家）。

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.fluid`` 改为 ``zmlx.fluids``.
"""

from zmlx.exts import SelfPath
from zmlx.fluids._aqueous import create_aqueous
from zmlx.fluids._mixture import create_mixture
from zmlx.fluids.alg import from_data, from_file
from zmlx.fluids.alg import load_fludefs
from zmlx.fluids.ch4 import create as create_ch4
from zmlx.fluids.ch4_hydrate import create as create_ch4_hydrate
from zmlx.fluids.co2 import create as create_co2
from zmlx.fluids.co2_hydrate import create as create_co2_hydrate
from zmlx.fluids.h2o import create as create_h2o
from zmlx.fluids.h2o_gas import create as create_h2o_gas
from zmlx.fluids.h2o_ice import create as create_h2o_ice
from zmlx.fluids.solution import create_solute

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
