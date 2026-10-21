"""可运行的示例案例（``zmlx.demos``）.

⚠️ **本目录 2026-10-16 由 ``zmlx.demo`` 改名为 ``zmlx.demos``**
（与 ``algs`` / ``utils`` / ``fluids`` / ``reactions`` / ``geometries`` / ``meshes`` / ``seepage_meshes`` / ``scripts`` / ``krs`` 等一批包统一用**复数**目录名 ——
本目录装的是**一堆可运行的案例**，复数才是它实际的形态）。

⚠️ **旧名 ``zmlx.demo`` 只保留了「最小垫片」**（导入即发 :class:`DeprecationWarning`，
**2027-10-16 删除**）—— 那只是过渡，**将来一定会删**，所以来历记在这里（新家）。

⚠️ 为什么旧名是"**最小**"垫片：本目录下绝大多数是**顶层的可运行案例**，不是给人 import
的库代码 —— 实测 154 个模块里**只有 4 个**被 import 过。为一个没人 import 的包留 180 个
转发文件，只会让人误以为 demo 是被大量依赖的库；最终只给**确有外部引用**的模块留了转发。

Modified by DeepSeek, 2026-10-16: 包名由 ``zmlx.demo`` 改为 ``zmlx.demos``.
"""

import os

from zmlx.algs import code_config, list_files
from zmlx.exts import SelfPath

get_path = SelfPath(__file__)


def list_demo_files():
    """
    列出demo文件的路径和说明
    """
    files = list_files(get_path(), exts=['.py'])
    results = []
    for file in files:
        if '__Trash' in file or 'debugging' in file:
            continue
        cfg = code_config(path=file, encoding='utf-8')
        desc = cfg.get('desc', '')
        if isinstance(desc, str):
            if len(desc) > 0:
                results.append([file, desc])
    return results


def test():
    files = list_demo_files()
    folder = get_path()
    for idx in range(len(files)):
        file, desc = files[idx]
        print(idx, os.path.relpath(file, folder), desc)


if __name__ == '__main__':
    test()
