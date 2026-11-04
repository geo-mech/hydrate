# ** desc = '井截面取热：水平井一个横截面附近的取热模拟（岩石向井筒传热，统计采热功率）'
# ** highlight = '#e31a1c'
"""井截面取热算例：水平井一个横截面附近的取热模拟.

⚠️ 上面两行 ``# **`` 是给插件/算例列表读的元数据，本 docstring 是给人读的。

几何
----

一个矩形 x–z 剖面（x、z 各 ``[-50, 50]`` m，y 方向只有一层薄壳，
见 :func:`zmlx.scen.geothermal._mesh.mesh_xz`）。井位于剖面中心 ``(0, 0)``，
取离它最近的那个单元作为井单元，并按井筒直径把该单元与相邻单元的导流面积收窄
（见 :func:`zmlx.scen.geothermal._well_cross_section.create`）。

物理设置
--------

- **初始温度**：井单元 280 K，其余岩石 320 K；
- **岩石物性**：花岗岩典型值 —— 密度 2650 kg/m³、比热 790 J/(kg·K)、
  热导率 3.0 W/(m·K)；
- **井单元**的体积热容放大 1e6 倍，当作恒温储热体；岩石中的热量通过导热
  与流体对流不断补充给它，形成持续取热。

输出
----

:func:`zmlx.scen.geothermal._well_cross_section.update_power` 每步记录井单元的
能量变化并换算成采热功率；``solve`` 的绘图回调除了画四张状态子图
（岩石温度 / 流体温度 / 密度 / 流体 z0），还会画出「采热功率 ~ 时间」曲线。

两个工况（只有渗透率不同）
--------------------------

- :func:`test`：``perm = 1e-11`` m² —— 高渗，对流补热明显；
- :func:`test_02`：``perm = 1e-20`` m² —— 近不可渗，基本只靠导热；
  ``__main__`` 分支默认运行它。
"""

from zmlx import gui
from zmlx.scen.geothermal._well_cross_section import create, solve


def test():
    """跑一遍**高渗**工况（``perm = 1e-11`` m²），最大时间步 1 天."""
    jx, jz = 100, 100
    model = create(jx=jx, jz=jz, perm=1.0e-11, dt_max=3600 * 24 * 7)
    solve(model, jx=jx, jz=jz)


def test_02():
    """跑一遍**近不可渗**工况（``perm = 1e-20`` m²），最大时间步 1 天.

    与 :func:`test` 只差渗透率：渗透率极低时介质内几乎没有对流，
    岩石向井的补热基本只靠导热，可与高渗工况对比看对流的影响。
    """
    jx, jz = 100, 100
    model = create(jx=jx, jz=jz, perm=1.0e-20, dt_max=3600 * 24 * 7)
    solve(model, jx=jx, jz=jz)


if __name__ == "__main__":
    # 通过GUI执行主函数；--no-gui参数用于无图形界面运行
    gui.execute(test, close_after_done=False)
