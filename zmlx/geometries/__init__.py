"""几何计算工具（点、线段、矩形、三角形、裂缝网络）.

Modified by Claude, 2026-08-12

⚠️ **本目录 2026-10-16 由 ``zmlx.geometry`` 改名为 ``zmlx.geometries``**
（与 ``algs`` / ``utils`` / ``fluids`` / ``reactions`` / ``demos`` / ``meshes`` / ``seepage_meshes`` / ``scripts`` / ``krs`` 等一批包统一用**复数**目录名 ——
``几何计算（点、线段、矩形、三角形、裂缝网络）``，复数才是它实际的形态）。

⚠️ **旧名 ``zmlx.geometry`` 保留为兼容垫片**（导入即发 :class:`DeprecationWarning`，
**2027-10-16 删除**）—— 那只是过渡，**将来一定会删**，所以来历记在这里（新家）。

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.geometry`` 改为 ``zmlx.geometries``.
"""
from zmlx.exts import SelfPath
from zmlx.geometries.base import *
from zmlx.geometries.base import point_distance as get_distance

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
