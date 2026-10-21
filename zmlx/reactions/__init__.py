"""化学反应模块（水合物、相变、燃烧、溶解等反应定义）.

Modified by Claude, 2026-08-12

⚠️ **本目录 2026-10-16 由 ``zmlx.react`` 改名为 ``zmlx.reactions``**
（与 ``algs`` / ``utils`` / ``fluids`` / ``geometries`` / ``demos`` / ``meshes`` / ``seepage_meshes`` / ``scripts`` / ``krs`` 等一批包统一用**复数**目录名 ——
``各种反应定义（水合物、相变、燃烧、溶解……）``，复数才是它实际的形态）。

⚠️ **旧名 ``zmlx.react`` 保留为兼容垫片**（导入即发 :class:`DeprecationWarning`，
**2027-10-16 删除**）—— 那只是过渡，**将来一定会删**，所以来历记在这里（新家）。

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.react`` 改为 ``zmlx.reactions``.
"""
from zmlx.exts import SelfPath
from zmlx.reactions.alg import load_reactions, add_reaction, create_reaction
from zmlx.reactions.inh import create_inh, add_inh

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
