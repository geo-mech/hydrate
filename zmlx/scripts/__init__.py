"""直接执行的脚本，用于测试和验证 zmlx 的功能。**不可以在外部导入这些脚本。**

⚠️ **本目录 2026-10-16 由 ``zmlx/script/`` 改名为 ``zmlx/scripts/``**
（与 ``algs`` / ``utils`` / ``fluids`` / ``reactions`` / ``geometries`` / ``demos`` / ``meshes`` / ``seepage_meshes`` / ``krs`` 等一批包统一用**复数**目录名 —— 本目录装的是**多个**互不相关的独立脚本，
复数才是它的实际形态）。

⚠️ **旧的 ``zmlx/script/`` 已删除，没有留兼容垫片** —— 这是**有意**的：

- 本目录的脚本按设计就是**给人直接运行**的（``python zmlx/scripts/xxx.py``），
  **不该被 import**（见上面第一句）。既然没有代码会 ``import zmlx.script``，
  留一层转发垫片就没有意义，反而会让"这个包到底是库还是脚本"更含糊；
- 删除前实测确认过：**全仓 ``.py`` 零处** ``import zmlx.script``，
  **外部工作区 ``igg-hydrate-works`` 的 12 个项目也零处引用**；
- ⚠️ 但**删除任何"已弃用"的包之前都必须连外部工作区一起搜** ——
  「本仓没人 import」**不等于**「没人用」。本项目今天曾因此误删
  ``ui/GuiBuffer.py`` 与 ``zmlx/demo``（核对外部 12 个项目、432 条导入语句后
  才发现确有引用，只能恢复）。本次是**先查证、后删除**。

⚠️ 注意区分：**删掉的是旧名垫片 ``script/``，不是本目录**。
本目录的 5 个脚本（``install_dep`` / ``open_ui_safe`` / ``write_pip_config`` /
``export_time_to_pressure`` / ``create_ui_lnk_on_desktop``）**全部保留**，
其中 ``install_dep.py`` 还写在 README 里作为装机指引。

Modified by DeepSeek, 2026-10-17: 记录 ``script`` -> ``scripts`` 的改名与旧垫片的删除.
"""


from zmlx.exts import SelfPath

get_path = SelfPath(__file__)

if __name__ == "__main__":
    print(get_path())
