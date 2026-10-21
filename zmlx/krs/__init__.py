"""相对渗透率（Kr）模型定义与创建.

Modified by Claude, 2026-08-12

⚠️ **本目录 2026-10-16 由 ``zmlx.kr`` 改名为 ``zmlx.krs``**
（与 ``algs`` / ``utils`` / ``fluids`` / ``reactions`` / ``geometries`` / ``demos`` / ``meshes`` / ``seepage_meshes`` / ``scripts`` 等一批包统一用**复数**目录名 ——
``相对渗透率（Kr）相关工具``，复数才是它实际的形态）。

⚠️ **旧名 ``zmlx.kr`` 保留为兼容垫片**（导入即发 :class:`DeprecationWarning`，
**2027-10-16 删除**）—— 那只是过渡，**将来一定会删**，所以来历记在这里（新家）。

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.kr`` 改为 ``zmlx.krs``.
"""
from zmlx.exts import SelfPath
from zmlx.krs.base import *

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
