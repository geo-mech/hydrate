# ** name = '经典分形'
# ** desc = '「演示 → 经典分形」：裂缝分形图案逐代演化的可视化演示（默认不加载）'
# ** enabled = False
"""
分形演化 · 多图案查看器（:class:`FractalEvolutionView`）
========================================================

左侧选一种分形，右侧按【空格】一代一代看它怎么演化出来。

包含 10 种常见分形，分四类演化方式：

  挖洞型（每代在实心块里挖掉中心，剩下的继续挖）
      1. 谢尔宾斯基三角形      三角形挖中心倒三角        ×3
      2. 谢尔宾斯基地毯        正方形九宫格挖正中        ×8
      3. 谢尔宾斯基五边形      正五边形挖中心            ×5
      4. 康托尔方块            九宫格只留四角            ×4
      5. 维克塞克分形          九宫格留十字形            ×5

  生长型（每代往上长出新的小方块）
      6. 毕达哥拉斯树          正方形顶上长两个斜方块    ×2

  曲线型（每代把每条线段折得更细，只增不减）
      7. 科赫雪花              线段中间长出小山尖        ×4
      8. 莱维 C 曲线           每段折成直角等腰          ×2
      9. 龙形曲线              反复对折纸带              ×2

  分层型（每代单独占一行，看"越来越稀疏"的过程）
     10. 康托尔尘埃            线段挖掉中间三分之一      ×2

尺寸：控件自己会缩，绝不撑大父窗口
----------------------------------

顶部标题带、底部状态带、左侧列表宽度、字号都按控件**当前**尺寸按比例收缩
（:meth:`FractalEvolutionView._bands`），最小尺寸只有
:data:`FractalEvolutionView.MIN_W` × :data:`FractalEvolutionView.MIN_H`。
⚠️ 这一条是硬要求：控件放进 ``QTabWidget`` 后，它的 ``minimumSizeHint`` 会
一路顶到主窗口，最小值设大了就会「一打开这个标签页，整个窗口被迫变高」。

配色：跟随主题，暗色 / 亮色都好看
----------------------------------

界面颜色（背景、文字、进度条、列表与参数面板、滚动条）**一个都不写死**，全部
从当前主题的 ``QPalette`` 推导（:class:`_Theme`）：暗色主题给出深底浅字、亮色
主题给出浅底深字，用户自定义的 ``zml_window_style.qss`` 也能跟上；主题切换时
Qt 会发 ``PaletteChange``，控件当场重取配色、重套样式并重画（:meth:`_sync_theme`）。
图案自身的颜色是每种分形自带的，只按主题微调亮度（亮色底上压暗一点，免得浅黄、
浅青糊在白底里）。

运行方式
--------
直接跑（需要装了 PyQt 的解释器）::

    python -m zmlx.ui.plugins.builtin.fractal_demo

作为 zmlx GUI 的标签页控件::

    from zmlx.ui.plugins.builtin.fractal_demo import FractalEvolutionView
    gui.get_widget(FractalEvolutionView, caption="经典分形")

（现成入口：「设置 → 插件」里启用「经典分形」后，菜单「演示 → 经典分形」；
挂载点就是本文件 ``zmlx/ui/plugins/builtin/fractal_demo.py``。）

快捷键
------
    空格        演化到下一代（核心操作）
    ↑ / ↓       切换左侧的分形图案
    A           自动播放 开 / 关
    ←  /  →     后退 / 前进一代
    R           重来（回到第 0 代）
    S           保存当前画面为 PNG 图片
    Esc / Q     退出（只对独立窗口有效；在标签页里请用标签上的关闭按钮）

另外支持命令行参数 --benchmark，用来测每种分形的生成和绘制耗时。

作者: 张召彬
Modified by DeepSeek, 2026-10-11: 由 fractal/widgets/fractal.py 更名（FractalWindow →
FractalEvolutionView），Qt 导入改走 zmlx.ui.pyqt，尺寸改为自适应（去掉 940×700 的硬下限）。
本文件**既是插件、也是控件本体**（单文件自足，只依赖 ``zmlx.ui.pyqt``）。
作为插件被 ``load_all`` 执行时，它只注册命令 ``gui.show_classic_fractal()`` 与
菜单「演示 → 经典分形」；``# ** enabled = False`` 表示**默认不加载** —— 在
「设置 → 插件」里勾上、重启后菜单才会出现。直接运行本文件
（``python zmlx/ui/plugins/builtin/fractal_demo.py``）则单独开一个窗口自测。

来源：``fractal-crack`` 项目（``igg-hydrate-works/fractal-crack/fractal/widgets/
fractal_evolution_view.py``）的控件，2026-10-19 整体搬入并挂成插件；控件代码
未改，只更新了文档里的入口路径。那个项目里的**求解部分**（``_mechanics.py`` 等
分形扩展 / 力学计算）与本演示无关，没有搬。
"""

from __future__ import annotations

import math
import os
import sys
import time
from typing import Dict, List, Optional, Sequence, Tuple

from zmlx.system import execute_once

from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets

# --------------------------------------------------------------------------
# 图案库（分形本身）的常量
# --------------------------------------------------------------------------

# 两道数量闸门里的第一道，在"生成"这一层：单代对象数不许超过这个数。
# 正常分形最深一代最多 3 万出头（地毯 32,768），离这条线很远，
# 所以平时永远碰不到；它只防 max_gen 被设错、或以后新加的分形写错倍数，
# 一次生成上千万个对象 —— 到那时候连给它们排序都会把界面卡死，
# 所以必须在对象还没造出来的时候就截住。
# （第二道闸门在"绘制"那一层，见 FractalEvolutionView.MAX_SHAPES_DRAWN。）
HARD_MAX_SHAPES = 100_000

Point = Tuple[float, float]
Poly = List[Point]

# 演化方式
MODE_AREA = "area"      # 挖洞：填实心块，逐代挖掉
MODE_ADD = "add"        # 生长：逐代往上加形状
MODE_CURVE = "curve"    # 曲线：逐代把线段折细
MODE_ROWS = "rows"      # 分层：每代占一行


# --------------------------------------------------------------------------
# 几何工具
# --------------------------------------------------------------------------

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def mix_color(c1: QtGui.QColor, c2: QtGui.QColor, t: float) -> QtGui.QColor:
    t = max(0.0, min(1.0, t))
    return QtGui.QColor(
        int(lerp(c1.red(), c2.red(), t)),
        int(lerp(c1.green(), c2.green(), t)),
        int(lerp(c1.blue(), c2.blue(), t)),
    )


def regular_polygon(n: int, r: float = 1.0, rot: float = math.pi / 2) -> Poly:
    """正 n 边形，外接圆半径 r，rot 是第一个顶点的角度（默认朝上）。"""
    return [(r * math.cos(rot + 2 * math.pi * k / n),
             r * math.sin(rot + 2 * math.pi * k / n)) for k in range(n)]


def rect_poly(x0: float, y0: float, x1: float, y1: float) -> Poly:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def poly_bbox(polys: Sequence[Poly]) -> Tuple[float, float, float, float]:
    xs_min = ys_min = float("inf")
    xs_max = ys_max = float("-inf")
    for poly in polys:
        for x, y in poly:
            if x < xs_min:
                xs_min = x
            if x > xs_max:
                xs_max = x
            if y < ys_min:
                ys_min = y
            if y > ys_max:
                ys_max = y
    if xs_min == float("inf"):
        return (0.0, 0.0, 1.0, 1.0)
    return (xs_min, ys_min, xs_max, ys_max)


def union_bbox(boxes: Sequence[Tuple[float, float, float, float]]):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def square_from_base(b0: Point, b1: Point) -> Poly:
    """以 b0→b1 为底边，向左立起一个正方形（数学坐标系，y 向上）。"""
    dx, dy = b1[0] - b0[0], b1[1] - b0[1]
    length = math.hypot(dx, dy)
    if length < 1e-12:
        return [b0, b1, b1, b0]
    nx, ny = -dy / length, dx / length      # 左法线
    return [b0, b1,
            (b1[0] + nx * length, b1[1] + ny * length),
            (b0[0] + nx * length, b0[1] + ny * length)]


# --------------------------------------------------------------------------
# L 系统（画曲线型分形用）
# --------------------------------------------------------------------------

def lsystem_points(axiom: str, rules: Dict[str, str], iters: int,
                   angle_deg: float, step: float = 1.0) -> List[Point]:
    """把 L 系统展开，再用海龟走一遍，返回折线的顶点。"""
    s = axiom
    for _ in range(iters):
        s = "".join(rules.get(ch, ch) for ch in s)

    a = math.radians(angle_deg)
    x = y = 0.0
    heading = 0.0
    pts: List[Point] = [(0.0, 0.0)]
    stack: List[Tuple[float, float, float]] = []

    for ch in s:
        if ch == "F":
            x += step * math.cos(heading)
            y += step * math.sin(heading)
            pts.append((x, y))
        elif ch == "+":
            heading += a
        elif ch == "-":
            heading -= a
        elif ch == "[":
            stack.append((x, y, heading))
        elif ch == "]":
            x, y, heading = stack.pop()
    return pts


# --------------------------------------------------------------------------
# 分形定义
# --------------------------------------------------------------------------

class Fractal:
    """
    一种分形图案。

    subdivide(poly) 返回 (存活的多边形, 被挖掉的洞)。
    洞可以留空 —— 树和曲线根本没有"洞"。

    坐标一律用数学坐标系（y 向上），绘制时再翻过来。
    每一代都是懒加载 + 缓存，只有真的按到这个代数才算，避免一开局就卡住。
    """

    def __init__(self, key: str, name: str, rule: str, mode: str,
                 max_gen: int, color_a: QtGui.QColor, color_b: QtGui.QColor,
                 unit: str = "图形") -> None:
        self.key = key
        self.name = name
        self.rule = rule
        self.mode = mode
        self._max_gen = max_gen
        self.color_a = color_a
        self.color_b = color_b
        self.unit = unit

        self._gens: List[List[Poly]] = []
        self._hole_counts: List[int] = []
        self._bbox: Optional[Tuple[float, float, float, float]] = None

    # max_gen 做成属性，参数树要根据分叉数量动态决定最深能到第几代
    @property
    def max_gen(self) -> int:
        return self._max_gen

    @max_gen.setter
    def max_gen(self, value: int) -> None:
        self._max_gen = value

    def invalidate(self) -> None:
        """参数变了：丢掉已经算好的各代，下次绘制时重算。"""
        self._gens = []
        self._hole_counts = []
        self._bbox = None

    def tip_points(self, g: int) -> List[Tuple[float, float, float]]:
        """第 g 代每个形状的"末端"（x, y, 半径），用来画树梢的小圆点。"""
        return []

    # ---- 子类实现 --------------------------------------------------------

    def seed(self) -> List[Poly]:
        raise NotImplementedError

    def subdivide(self, poly: Poly) -> Tuple[List[Poly], List[Poly]]:
        raise NotImplementedError

    # ---- 代际生成 --------------------------------------------------------

    def ensure(self, g: int) -> None:
        """
        把第 0..g 代都算出来（懒加载 + 缓存）。

        这里有两道保险，缺一个都可能把界面卡死：

        1) g 夹到 max_gen。少了它，任何一处 `shapes(9)` 碰上 6 分叉的树，
           就会老老实实去算是 6^9 = 1000 万根树枝。夹在这里，所有调用方
           都安全，而不是指望每个调用点都记得先判断。

        2) 单代对象数超过 HARD_MAX_SHAPES 就**中途放弃**这一代（边生成边
           检查，一超就 break），而不是先造完再判断 —— 造完再判断的话，
           上千万个对象已经躺在内存里了，光排序就能把界面卡死。

        放弃时把 max_gen 收到真正算得出来的那一代，界面也就不会显示到
        一个其实不存在的代上。
        """
        g = max(0, min(int(g), self.max_gen))
        if not self._gens:
            self._gens.append(self.seed())
            self._hole_counts.append(0)
        while len(self._gens) <= g:
            kept_all: List[Poly] = []
            holes = 0
            overflow = False
            for poly in self._gens[-1]:
                kept, dug = self.subdivide(poly)
                kept_all.extend(kept)
                holes += len(dug)
                if len(kept_all) > HARD_MAX_SHAPES:
                    overflow = True
                    break          # 越算越多，别算了
            if overflow:
                self._max_gen = max(0, len(self._gens) - 1)
                break
            self._gens.append(kept_all)
            self._hole_counts.append(holes)

    def shapes(self, g: int) -> List[Poly]:
        self.ensure(g)
        return self._gens[max(0, min(int(g), self.max_gen))]

    def holes_upto(self, g: int) -> int:
        self.ensure(g)
        return sum(self._hole_counts[1:g + 1])

    # ---- 取景包围盒 ------------------------------------------------------

    def fit_bbox(self) -> Tuple[float, float, float, float]:
        """
        取景用的包围盒。

        挖洞型的子块永远在父块内部，所以第 0 代就决定了范围；
        生长型和曲线型会越画越大，必须算到最后一代，否则每按一次空格
        画面就会重新缩放、图案乱跳。
        """
        if self._bbox is not None:
            return self._bbox
        if self.mode == MODE_AREA:
            self._bbox = poly_bbox(self.shapes(0))
        else:
            boxes = [poly_bbox(self.shapes(g)) for g in range(self.max_gen + 1)
                     if self.shapes(g)]
            self._bbox = union_bbox(boxes) if boxes else (0.0, 0.0, 1.0, 1.0)
        return self._bbox

    def bbox_upto(self, g: int) -> Tuple[float, float, float, float]:
        """
        第 0..g 代的包围盒（生长型用：树长到第 g 代时的整体范围）。
        """
        boxes = [poly_bbox(self.shapes(i)) for i in range(g + 1) if self.shapes(i)]
        return union_bbox(boxes) if boxes else (0.0, 0.0, 1.0, 1.0)

    def view_bbox(self, g: int) -> Tuple[float, float, float, float]:
        """
        画第 g 代时该用什么取景框。

        挖洞型：子块永远在父块里，用第 0 代定死，画面绝不跳动。
        生长型：用整棵树的最大范围，这样能真的看到"越长越高"。
        曲线型：每代单独取景。L 系统里每折一次整条曲线都会变大
                （科赫雪花边长每代 ×4/3），若按最大范围取景，
                第 1、2 代就只剩画面中间一个小点，完全看不清。
                曲线型要看的是"细节越来越多"，所以固定大小、逐代变细。
        """
        if self.mode == MODE_CURVE:
            return poly_bbox(self.shapes(g))
        return self.fit_bbox()

    # ---- 统计 ------------------------------------------------------------

    def count(self, g: int) -> int:
        shapes = self.shapes(g)
        if self.mode == MODE_CURVE:
            return max(0, len(shapes[0]) - 1) if shapes else 0
        return len(shapes)

    def stat_text(self, g: int) -> str:
        n = self.count(g)
        if self.mode == MODE_AREA:
            return f"存活{self.unit} {n:,}      已挖掉 {self.holes_upto(g):,} 个洞"
        if self.mode == MODE_ADD:
            total = sum(self.count(i) for i in range(g + 1))
            return f"{self.unit} {n:,} 个      累计 {total:,} 个"
        if self.mode == MODE_CURVE:
            return f"线段 {n:,} 条"
        return f"区间 {n:,} 段"


class CornerFractal(Fractal):
    """
    正多边形"角上缩放"构造：

        子块 = 整体按 r 缩小后，平移到第 k 个顶点上

    对三角形取 r = 1/2，正好就是"三角形挖掉中心倒三角"；
    对正 n 边形取 r = 1/(1+2cos(π/n))，相邻子块恰好相接。
    所以三角形和五边形共用这一套公式。
    """

    def __init__(self, n: int, key: str, name: str, rule: str, max_gen: int,
                 color_a: QtGui.QColor, color_b: QtGui.QColor, unit: str) -> None:
        super().__init__(key, name, rule, MODE_AREA, max_gen, color_a, color_b,
                         unit=unit)
        self.n = n
        self.r = 1.0 / (1.0 + 2.0 * math.cos(math.pi / n))

    def seed(self) -> List[Poly]:
        return [regular_polygon(self.n, 1.0)]

    def subdivide(self, poly: Poly) -> Tuple[List[Poly], List[Poly]]:
        r = self.r
        kept: List[Poly] = []
        for k in range(len(poly)):
            vx, vy = poly[k]
            kept.append([(r * px + (1 - r) * vx, r * py + (1 - r) * vy)
                         for (px, py) in poly])
        # 中间的洞不画就自然露出来了，不需要单独构造多边形
        return kept, []

    def holes_upto(self, g: int) -> int:
        """
        中间的洞不靠"画出来"而是靠"不画"，所以没法用子块的洞来数。
        但每个父块中心正好挖掉一个洞，于是累计洞数 = 前 g 代父块数量之和。
        三角形：1+3+9+… = (3^g-1)/2，正好是经典数目。
        """
        return sum(len(self.shapes(i)) for i in range(0, g))


class GridFractal(Fractal):
    """把方块切成 3×3 九宫格，保留指定的格子，其余算作挖掉。"""

    def __init__(self, key: str, name: str, rule: str, max_gen: int,
                 keep: Sequence[Tuple[int, int]], unit: str,
                 color_a: QtGui.QColor, color_b: QtGui.QColor) -> None:
        super().__init__(key, name, rule, MODE_AREA, max_gen, color_a, color_b,
                         unit=unit)
        self.keep = set(keep)

    def seed(self) -> List[Poly]:
        return [rect_poly(0.0, 0.0, 1.0, 1.0)]

    def subdivide(self, poly: Poly) -> Tuple[List[Poly], List[Poly]]:
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        w = (x1 - x0) / 3.0
        h = (y1 - y0) / 3.0

        def cell(i: int, j: int) -> Poly:
            return rect_poly(x0 + i * w, y0 + j * h, x0 + (i + 1) * w, y0 + (j + 1) * h)

        kept = [cell(i, j) for (i, j) in self.keep]
        holes = [cell(i, j) for i in range(3) for j in range(3)
                 if (i, j) not in self.keep]
        return kept, holes


class CantorDust(Fractal):
    """一维康托尔集：线段挖掉中间三分之一，剩下的两段继续挖。"""

    def __init__(self, max_gen: int, color_a: QtGui.QColor,
                 color_b: QtGui.QColor) -> None:
        super().__init__(
            "cantor_dust", "康托尔尘埃",
            "线段挖掉中间三分之一，剩下的两段再挖 —— 每代单独占一行",
            MODE_ROWS, max_gen, color_a, color_b, unit="线段")

    def seed(self) -> List[Poly]:
        return [rect_poly(0.0, 0.0, 1.0, 1.0)]

    def subdivide(self, poly: Poly) -> Tuple[List[Poly], List[Poly]]:
        xs = [p[0] for p in poly]
        x0, x1 = min(xs), max(xs)
        third = (x1 - x0) / 3.0
        left = rect_poly(x0, 0.0, x0 + third, 1.0)
        mid = rect_poly(x0 + third, 0.0, x0 + 2 * third, 1.0)
        right = rect_poly(x0 + 2 * third, 0.0, x1, 1.0)
        return [left, right], [mid]


class PythagorasTree(Fractal):
    """正方形顶边上立一个等腰直角三角形，两腰上各长出一个新正方形。"""

    def __init__(self, max_gen: int, color_a: QtGui.QColor,
                 color_b: QtGui.QColor) -> None:
        super().__init__(
            "pythagoras", "毕达哥拉斯树",
            "正方形顶上长出两个斜着的小正方形，每代翻一倍 —— 树越长越高",
            MODE_ADD, max_gen, color_a, color_b, unit="正方形")

    def seed(self) -> List[Poly]:
        return [square_from_base((0.0, 0.0), (1.0, 0.0))]

    def subdivide(self, poly: Poly) -> Tuple[List[Poly], List[Poly]]:
        p0, p1, p2, p3 = poly[0], poly[1], poly[2], poly[3]
        top_a, top_b = p3, p2          # 顶边（p0→p1 是底边）
        dx, dy = top_b[0] - top_a[0], top_b[1] - top_a[1]
        length = math.hypot(dx, dy)
        nx, ny = -dy / length, dx / length
        apex = ((top_a[0] + top_b[0]) / 2 + nx * length / 2,
                (top_a[1] + top_b[1]) / 2 + ny * length / 2)
        return [square_from_base(top_a, apex), square_from_base(apex, top_b)], []


def fit_margin(rect: QtCore.QRectF) -> float:
    """
    取景留白：主画面留 8px 舒服，但 44px 的缩略图留 8px 就只剩中间一小块了。
    """
    return 8.0 if rect.width() > 200.0 else 1.0


def unit_noise(a: float, b: float) -> float:
    """
    由任意两个数生成一个 -1..1 之间的"伪随机"数，而且是**稳定**的：
    同样的输入永远得到同样的输出。

    参数树必须用它而不是 random 模块 —— 每次改参数、改窗口大小都会把
    各代重算一遍，真随机的话整棵树会不停抖动变形，看着像坏了。
    这里把随机性绑在树枝自己的坐标上，于是同一组参数永远长出同一棵树。
    """
    h = math.sin(a * 12.9898 + b * 78.233) * 43758.5453
    return (h - math.floor(h)) * 2.0 - 1.0


def branch_poly(base_c: Point, tip_c: Point, width: float) -> Poly:
    """
    把一根树枝表示成一个细长四边形，好复用现有的多边形渲染。

    点序固定为 [根部左, 根部右, 梢部右, 梢部左]，
    所以 subdivide 能反过来从多边形里还原出根点、方向、长度和粗细。
    """
    dx, dy = tip_c[0] - base_c[0], tip_c[1] - base_c[1]
    length = math.hypot(dx, dy)
    if length < 1e-12:
        length = 1e-12
    nx, ny = -dy / length, dx / length          # 垂直方向
    hw = width / 2.0
    return [(base_c[0] + nx * hw, base_c[1] + ny * hw),
            (base_c[0] - nx * hw, base_c[1] - ny * hw),
            (tip_c[0] - nx * hw, tip_c[1] - ny * hw),
            (tip_c[0] + nx * hw, tip_c[1] + ny * hw)]


class ParametricTree(Fractal):
    """
    参数可调的分叉树：每根树枝的末端再长出若干根更短的新枝。

    五个参数就是它全部的自由度（界面左侧面板可实时拖动）：
        分叉数量 n —— 每根枝末端长出几根新枝
        缩小比例 r —— 新枝长度 = 母枝长度 × r
        分叉张角 θ —— 最外侧两根新枝之间的夹角
        枝干粗细 w —— 枝的宽度 = 该枝长度 × w
        随机扰动 j —— 每根新枝歪一点、长短不一，看起来更像真树
    """

    # 最深一代的枝数上限。分叉数量一调大，代数就得自动降下来，否则会爆炸
    # （n=6 时 6^8 是 167 万根，光算坐标就要几秒，屏幕上也早糊成一片了）
    BUDGET = 8000

    # 扰动拉满时，单根枝最多歪多少（相对张角）／长度最多差多少
    JITTER_ANGLE = 0.6
    JITTER_LEN = 0.18

    def __init__(self, color_a: QtGui.QColor, color_b: QtGui.QColor) -> None:
        super().__init__(
            "param_tree", "参数分叉树（可调）",
            "每根树枝末端再分出几根新枝 —— 分叉数、缩小比例、张角、扰动都能在左边调",
            MODE_ADD, 12, color_a, color_b, unit="树枝")
        self.branches = 2
        self.ratio = 0.72
        self.spread = 50.0          # 度
        self.width_ratio = 0.12
        self.jitter = 0.25          # 0..1，0 就是完全对称
        self.tip_dots = True        # 树梢画小圆点，看起来像发芽

    @property
    def max_gen(self) -> int:
        """按分叉数量反推安全的代数上限（保证最深一代不超过 BUDGET 根）。"""
        n = max(1, int(self.branches))
        g = 1
        while n ** (g + 1) <= self.BUDGET and g < 14:
            g += 1
        return g

    @max_gen.setter
    def max_gen(self, value: int) -> None:
        self._max_gen = value        # 基类 __init__ 会写这个，这里收下但不使用

    def set_params(self, branches: Optional[int] = None,
                   ratio: Optional[float] = None,
                   spread: Optional[float] = None,
                   width_ratio: Optional[float] = None,
                   jitter: Optional[float] = None) -> bool:
        """改参数并作废已算好的各代。返回是否真的有变化。"""
        changed = False
        if branches is not None and int(branches) != self.branches:
            self.branches = max(1, int(branches))
            changed = True
        if ratio is not None and abs(ratio - self.ratio) > 1e-6:
            self.ratio = min(0.92, max(0.2, ratio))
            changed = True
        if spread is not None and abs(spread - self.spread) > 1e-6:
            self.spread = min(175.0, max(0.0, spread))
            changed = True
        if width_ratio is not None and abs(width_ratio - self.width_ratio) > 1e-6:
            self.width_ratio = min(0.35, max(0.02, width_ratio))
            changed = True
        if jitter is not None and abs(jitter - self.jitter) > 1e-6:
            self.jitter = min(1.0, max(0.0, jitter))
            changed = True
        if changed:
            self.invalidate()
        return changed

    def seed(self) -> List[Poly]:
        # 树干：从原点竖直向上，长度 1
        return [branch_poly((0.0, 0.0), (0.0, 1.0), self.width_ratio)]

    def subdivide(self, poly: Poly) -> Tuple[List[Poly], List[Poly]]:
        p0, p1, p2, p3 = poly[0], poly[1], poly[2], poly[3]
        base_c = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0)
        tip_c = ((p2[0] + p3[0]) / 2.0, (p2[1] + p3[1]) / 2.0)
        dx, dy = tip_c[0] - base_c[0], tip_c[1] - base_c[1]
        length = math.hypot(dx, dy)
        if length < 1e-12:
            return [], []
        ux, uy = dx / length, dy / length

        child_len = length * self.ratio
        n = max(1, int(self.branches))
        if n == 1:
            offsets = [0.0]
        else:
            # 以母枝方向为中心，把 n 根新枝均匀铺在 ±θ/2 之间
            half = math.radians(self.spread) / 2.0
            offsets = [-half + i * (2 * half) / (n - 1) for i in range(n)]

        out: List[Poly] = []
        half_spread = math.radians(self.spread) / 2.0
        for i, a in enumerate(offsets):
            blen = child_len
            if self.jitter > 0.0:
                # 随机性绑在"这根枝的根点 + 它是第几个孩子"上，所以完全可复现：
                # 同一组参数每次重算都长出同一棵树（改窗口大小也不会变样）。
                jx = tip_c[0] * 7.31 + i * 13.77
                jy = tip_c[1] * 5.17 - i * 8.93
                a += (half_spread * self.JITTER_ANGLE * self.jitter
                      * unit_noise(jx, jy))
                blen *= 1.0 + (self.JITTER_LEN * self.jitter
                               * unit_noise(jy + 31.4, jx - 17.2))
            ca, sa = math.cos(a), math.sin(a)
            rx, ry = ux * ca - uy * sa, ux * sa + uy * ca
            tip = (tip_c[0] + rx * blen, tip_c[1] + ry * blen)
            out.append(branch_poly(tip_c, tip, blen * self.width_ratio))
        return out, []

    def tip_points(self, g: int) -> List[Tuple[float, float, float]]:
        out = []
        for poly in self.shapes(g):
            p2, p3 = poly[2], poly[3]
            cx, cy = (p2[0] + p3[0]) / 2.0, (p2[1] + p3[1]) / 2.0
            dx, dy = p3[0] - p2[0], p3[1] - p2[1]
            out.append((cx, cy, math.hypot(dx, dy) * 0.85))
        return out


class LSystemFractal(Fractal):
    """曲线型：每代是一条完整的折线，直接按代数重新生成，不是从上一代切出来的。"""

    def __init__(self, key: str, name: str, rule: str, max_gen: int,
                 axiom: str, rules: Dict[str, str], angle_deg: float,
                 color_a: QtGui.QColor, color_b: QtGui.QColor) -> None:
        super().__init__(key, name, rule, MODE_CURVE, max_gen, color_a, color_b,
                         unit="线段")
        self.axiom = axiom
        self.rules = rules
        self.angle_deg = angle_deg

    def seed(self) -> List[Poly]:
        return [lsystem_points(self.axiom, self.rules, 0, self.angle_deg)]

    def ensure(self, g: int) -> None:
        while len(self._gens) <= g:
            self._gens.append([lsystem_points(self.axiom, self.rules,
                                              len(self._gens), self.angle_deg)])
            self._hole_counts.append(0)

    def subdivide(self, poly: Poly) -> Tuple[List[Poly], List[Poly]]:
        raise NotImplementedError("曲线型分形不走 subdivide")


# --------------------------------------------------------------------------
# 注册所有分形
# --------------------------------------------------------------------------

def build_fractals() -> List[Fractal]:
    return [
        CornerFractal(
            3, "sierpinski_tri", "谢尔宾斯基三角形",
            "三角形中间挖掉一个倒三角，剩下的三个再各自挖 —— 最经典的分形",
            9, QtGui.QColor(64, 226, 190), QtGui.QColor(190, 110, 255), "三角形"),

        GridFractal(
            "carpet", "谢尔宾斯基地毯",
            "正方形九等分，挖掉正中那块，剩下 8 块再各自九等分",
            5, [(i, j) for i in range(3) for j in range(3) if (i, j) != (1, 1)],
            "方块", QtGui.QColor(255, 176, 74), QtGui.QColor(255, 86, 140)),

        CornerFractal(
            5, "sierpinski_pent", "谢尔宾斯基五边形",
            "正五边形在每个角上缩出一个小五边形，中间留空 —— 三角形的推广",
            6, QtGui.QColor(120, 210, 255), QtGui.QColor(120, 118, 255), "五边形"),

        CantorDust(6, QtGui.QColor(150, 235, 140), QtGui.QColor(60, 190, 210)),

        GridFractal(
            "cantor_square", "康托尔方块",
            "九宫格里只留四个角 —— 比地毯稀疏得多，几乎透明",
            7, [(0, 0), (2, 0), (0, 2), (2, 2)],
            "方块", QtGui.QColor(190, 160, 255), QtGui.QColor(90, 130, 255)),

        GridFractal(
            "vicsek", "维克塞克分形",
            "九宫格留一个十字形，像窗棂 —— 每代长出四个小十字",
            6, [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)],
            "方块", QtGui.QColor(255, 214, 102), QtGui.QColor(255, 132, 64)),

        PythagorasTree(12, QtGui.QColor(120, 230, 140), QtGui.QColor(230, 200, 90)),

        ParametricTree(QtGui.QColor(140, 225, 130), QtGui.QColor(255, 190, 90)),

        LSystemFractal(
            "koch", "科赫雪花",
            "每条边中间顶出一个尖，边数每代翻四倍 —— 面积有限，周长无限",
            5, "F--F--F", {"F": "F+F--F+F"}, 60.0,
            QtGui.QColor(150, 225, 255), QtGui.QColor(120, 140, 255)),

        LSystemFractal(
            "levy", "莱维 C 曲线",
            "每段折成一个直角等腰三角形的两条直角边 —— 越折越像羽毛",
            12, "F", {"F": "+F--F+"}, 45.0,
            QtGui.QColor(255, 170, 220), QtGui.QColor(150, 110, 255)),

        LSystemFractal(
            "dragon", "龙形曲线",
            "把纸条反复对折再展开 —— 折痕走出来的就是一条龙",
            12, "FX", {"X": "X+YF+", "Y": "-FX-Y"}, 90.0,
            QtGui.QColor(255, 150, 110), QtGui.QColor(255, 80, 160)),
    ]


# --------------------------------------------------------------------------
# 取景：把分形坐标映射到画布像素
# --------------------------------------------------------------------------

class Fit:
    """数学坐标（y 向上）→ 画布像素（y 向下）。"""

    def __init__(self, bbox, rect: QtCore.QRectF, margin: float = 10.0) -> None:
        x0, y0, x1, y1 = bbox
        bw = max(1e-9, x1 - x0)
        bh = max(1e-9, y1 - y0)
        self.s = min(max(1.0, rect.width() - 2 * margin) / bw,
                     max(1.0, rect.height() - 2 * margin) / bh)
        self.cx = rect.left() + rect.width() / 2
        self.cy = rect.top() + rect.height() / 2
        self.bx = (x0 + x1) / 2
        self.by = (y0 + y1) / 2

    def pt(self, p: Point) -> QtCore.QPointF:
        return QtCore.QPointF(self.cx + (p[0] - self.bx) * self.s,
                       self.cy - (p[1] - self.by) * self.s)     # y 翻转

    def poly(self, poly: Poly) -> QtGui.QPolygonF:
        q = QtGui.QPolygonF()
        for p in poly:
            q.append(self.pt(p))
        return q


# --------------------------------------------------------------------------
# 配色：跟着当前主题走
# --------------------------------------------------------------------------

class _Theme:
    """
    一套界面配色，全部从当前 ``QPalette`` 推导。

    取色规则与 zmlx 其它控件一致（见 ``_BarChart._colors``）：背景取
    ``Base`` / ``Window`` 里**较亮**的那个（暗色主题下 ``Base`` 可能比
    ``Window`` 还暗），文字取 ``WindowText``，强调色取 ``Highlight``；这样
    暗色主题、亮色主题以及用户自定义的 ``zml_window_style.qss`` 都能跟上，
    控件里不再写死任何界面色值。

    ⚠️ 这里只管**界面**（背景 / 文字 / 进度条 / 分隔线…）；图案本身的颜色是
    每种分形自带的，只按主题微调亮度 —— 见 :meth:`shape`。
    """

    # 推导用的比例（都相对当前主题的背景 / 文字色）
    BG_SHIFT = 0.06        # 底边往文字色偏这么多，做出上浅下深的渐变
    PANEL_SHIFT = 0.05     # 参数面板底色
    MUTED = 0.42           # 副标题（图案规则）
    STAT = 0.26            # 底部统计文字
    HINT = 0.46            # 快捷键提示行
    SIDE_HINT = 0.56       # 左侧栏底部"↑↓ 切换图案"
    TRACK_ALPHA = 24       # 进度条底槽
    DOT_ALPHA = 48         # 还没走到的小圆点
    LINE_ALPHA = 16        # 分隔线 / 悬停底色
    SEL_ALPHA = 46         # 列表选中底色
    SHAPE_DARKEN = 118     # 亮色主题下图案压暗的比例（浅黄/浅青在亮底上会发白）

    def __init__(self, palette: QtGui.QPalette) -> None:
        base = palette.color(QtGui.QPalette.ColorRole.Base)
        window = palette.color(QtGui.QPalette.ColorRole.Window)
        text = palette.color(QtGui.QPalette.ColorRole.WindowText)
        highlight = palette.color(QtGui.QPalette.ColorRole.Highlight)

        self.key = palette.cacheKey()     # 调色板指纹：变了就说明主题换了
        self.bg_top = QtGui.QColor(
            base if base.lightness() >= window.lightness() else window)
        self.dark = self.bg_top.lightness() < 128
        self.bg_bottom = mix_color(self.bg_top, text, self.BG_SHIFT)
        self.panel = mix_color(self.bg_top, text, self.PANEL_SHIFT)
        self.text = QtGui.QColor(text)
        self.highlight = QtGui.QColor(highlight)

        self.rule = mix_color(text, self.bg_top, self.MUTED)
        self.stat = mix_color(text, self.bg_top, self.STAT)
        self.hint = mix_color(text, self.bg_top, self.HINT)
        self.side_hint = mix_color(text, self.bg_top, self.SIDE_HINT)

        # 这几样用"文字色 + 透明度"表达，两种主题下都自然
        self.track = self._alpha(text, self.TRACK_ALPHA)
        self.dot_off = self._alpha(text, self.DOT_ALPHA)
        self.line = self._alpha(text, self.LINE_ALPHA)
        self.sel_bg = self._alpha(highlight, self.SEL_ALPHA)
        self.handle = self._alpha(text, 110)
        self.msg_ok = QtGui.QColor(highlight)          # 临时提示（跟着强调色）
        self.msg_warn = (QtGui.QColor(255, 205, 120) if self.dark
                         else QtGui.QColor(170, 102, 0))   # 已到最细一代

    @staticmethod
    def _alpha(color: QtGui.QColor, alpha: int) -> QtGui.QColor:
        """同一颜色、换个透明度（0-255）。"""
        c = QtGui.QColor(color)
        c.setAlpha(alpha)
        return c

    def shape(self, color: QtGui.QColor) -> QtGui.QColor:
        """图案颜色按主题微调：亮色底上压暗一点，免得浅黄/浅青糊在白底里。"""
        c = QtGui.QColor(color)
        return c if self.dark else c.darker(self.SHAPE_DARKEN)


# --------------------------------------------------------------------------
# 主控件
# --------------------------------------------------------------------------

class FractalEvolutionView(QtWidgets.QWidget):
    """
    分形演化查看器：左侧选图案，右侧按【空格】一代一代看它怎么长出来。

    独立窗口（:func:`test_1`）和 zmlx 标签页控件（``gui.get_widget``）两种用法
    都可以，因此有两条硬要求：

    - **最小尺寸很小**（:data:`MIN_W` × :data:`MIN_H`）：标签页里的控件会把
      ``minimumSizeHint`` 一路顶到主窗口，最小值设大了就会「一打开这个标签页，
      整个窗口被迫变高」；
    - **画面自己会缩**：顶部标题带、底部状态带、左侧列表宽度、字号都按当前
      尺寸推导（:meth:`_bands` / :meth:`_relayout`），不假设任何固定尺寸。

    配色**不写死**：界面颜色全部由当前主题的 ``QPalette`` 推导（:class:`_Theme`），
    暗色 / 亮色 / 用户自定义样式表都能跟上（主题切换时自动重取，见
    :meth:`_sync_theme`）；图案自身的颜色只按主题微调亮度。

    绘图全部是原生 ``QPainter``，各代图案按需生成 + 缓存，动画期间只贴两层
    缓存位图。快捷键见模块 docstring。
    """

    # ---- 时序常量 --------------------------------------------------------
    ANIM_MS = 380          # 单次演化动画时长（毫秒）
    AUTO_MS = 900          # 自动播放时两代之间的间隔（毫秒）

    # 第二道数量闸门，在"绘制"这一层：一帧最多画这么多个图形，超了按尺寸
    # 从大到小保留。同样设在正常规模之上（最大 32,768），平时不排序、不掉
    # 质量，纯保险。（第一道在"生成"那一层，见 HARD_MAX_SHAPES。）
    MAX_SHAPES_DRAWN = 40_000

    # ---- 尺寸常量 --------------------------------------------------------
    MIN_W, MIN_H = 480, 320        # 最小尺寸：小到能塞进任何标签页
    PREF_W, PREF_H = 1040, 720     # sizeHint：独立打开时的建议大小
    LIST_W = 232                   # 左侧列表的理想宽度（控件窄时自动收窄）
    LIST_MIN_W = 168               # 再窄就不成样子了
    LIST_MIN_H = 150               # 参数面板展开时，列表至少要留这么高
    HINT_H = 26                    # 左侧栏底部"↑↓ 切换图案"那一行
    HEADER_H = 168.0               # 顶部标题带的理想高度
    FOOTER_H = 176.0               # 底部状态带的理想高度
    BODY_MIN_RATIO = 0.45          # 画面至少要占控件高度的这个比例
    BODY_MIN_H = 120.0             # 画面高度的绝对下限（很矮时按这个兜底）

    # 子控件建好之前不响应主题事件。⚠️ 必须是**类属性**：StyleChange 在
    # __init__ 里（甚至 super().__init__ 期间）就会到达，那时实例属性还没赋值
    _ready = False

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("分形演化 · 多图案查看器")
        self.setMinimumSize(self.MIN_W, self.MIN_H)
        self.resize(self.PREF_W, self.PREF_H)

        self.font_family = self._pick_font()

        self.fractals = build_fractals()
        self.fi = 0
        self._gen = 0
        self.t = 1.0
        self.animating = False
        self.anim_started = 0.0

        self.list_w = self.LIST_W
        self.canvas = QtCore.QRectF(self.list_w, 0, 1, 1)
        self._pmcache: Dict[tuple, QtGui.QPixmap] = {}
        self._theme_cache: Optional[_Theme] = None
        self._theme_key: Optional[int] = None

        # ---- 左侧列表 ----------------------------------------------------
        self.listw = QtWidgets.QListWidget(self)
        self.listw.setGeometry(0, 0, self.list_w, self.height())
        # 按键统一由窗口处理，列表不抢焦点，这样空格/方向键的行为永远一致
        self.listw.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.listw.setIconSize(QtCore.QSize(22, 22))
        self.listw.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for f in self.fractals:
            item = QtWidgets.QListWidgetItem(f.name)
            item.setToolTip(f.rule)
            self.listw.addItem(item)
        self.listw.setCurrentRow(0)
        self.listw.itemClicked.connect(
            lambda item: self.select_fractal(self.listw.row(item)))

        # ---- 左下角的参数面板（只有参数树会显示）---------------------------
        # 面板比列表长，高度不够时套在滚动区里（滚动区自己很矮，不会顶尺寸）
        self.param_rows: Dict[str, Tuple[object, object]] = {}
        self.panel = self._build_param_panel()
        self.panel_box = QtWidgets.QScrollArea(self)
        self.panel_box.setWidget(self.panel)
        self.panel_box.setWidgetResizable(True)
        self.panel_box.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.panel_box.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.panel_box.viewport().setAutoFillBackground(False)
        self.panel_box.hide()

        # ---- 演化动画 ----------------------------------------------------
        self.anim = QtCore.QVariantAnimation(self)
        self.anim.setDuration(self.ANIM_MS)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._on_anim)
        self.anim.finished.connect(self._on_anim_done)

        # ---- 自动播放 ----------------------------------------------------
        self.auto = False
        self.auto_timer = QtCore.QTimer(self)
        self.auto_timer.setInterval(self.AUTO_MS)
        self.auto_timer.timeout.connect(self._auto_step)

        # ---- 临时提示 ----------------------------------------------------
        self.toast = ""
        self.toast_timer = QtCore.QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self._clear_toast)

        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self._sync_theme(force=True)     # 样式 + 缩略图都要按主题来
        self._ready = True
        self._relayout()

    # ------------------------------------------------------------------
    # 主题（配色 / 样式）
    # ------------------------------------------------------------------

    def _theme(self) -> _Theme:
        """当前主题配色（按调色板指纹缓存，主题没变就直接复用）。"""
        key = self.palette().cacheKey()
        if self._theme_cache is None or self._theme_cache.key != key:
            self._theme_cache = _Theme(self.palette())
        return self._theme_cache

    def _sync_theme(self, force: bool = False) -> None:
        """
        跟着当前主题刷新配色、子控件样式与缩略图。

        Args:
            force: 无视"主题没变"直接重刷（构造时用一次）。
        """
        theme = self._theme()
        if not force and theme.key == self._theme_key:
            return
        self._theme_key = theme.key
        self._apply_style(theme)
        self._pmcache.clear()        # 底图是按旧配色画的
        self.update()

    def changeEvent(self, event) -> None:  # noqa: N802
        # 系统/zmlx 切主题（含重新加载用户样式表）时 Qt 会发 PaletteChange 或
        # StyleChange；_sync_theme 自带"主题没变就返回"，多喊一次没有代价
        if self._ready and event.type() in (QtCore.QEvent.Type.PaletteChange,
                                            QtCore.QEvent.Type.StyleChange):
            self._sync_theme()
        super().changeEvent(event)

    @staticmethod
    def _rgba(color: QtGui.QColor) -> str:
        """QSS 里的 ``rgba()`` 文本（Qt 样式表的 alpha 是 0-255 的整数）。"""
        return (f"rgba({color.red()},{color.green()},{color.blue()},"
                f"{color.alpha()})")

    def _scroll_qss(self, theme: _Theme) -> str:
        """列表 / 面板的竖直滚动条（默认皮肤在自绘画面上很扎眼）。"""
        return f"""
            QScrollBar:vertical {{
                background: transparent; width: 8px; margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {self._rgba(theme.handle)};
                border-radius: 4px; min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self._rgba(theme.text)};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """

    def _apply_style(self, theme: _Theme) -> None:
        """
        把配色套到子控件上：列表、参数面板、滚动条，并重画 11 个缩略图。

        ⚠️ 只在主题真的变了时调（见 :meth:`_sync_theme`）：每次都重建缩略图。
        """
        self.listw.setStyleSheet(f"""
            QListWidget {{
                background: {theme.panel.name()};
                border: none;
                border-right: 1px solid {self._rgba(theme.line)};
                outline: none;
                padding: 8px 4px;
                font-family: "{self.font_family}";
                font-size: 13px;
            }}
            QListWidget::item {{
                color: {theme.rule.name()};
                padding: 8px 6px;
                border-radius: 8px;
                margin: 2px 4px;
            }}
            QListWidget::item:hover    {{ background: {self._rgba(theme.line)}; }}
            QListWidget::item:selected {{
                background: {self._rgba(theme.sel_bg)};
                color: {theme.text.name()};
            }}
        """ + self._scroll_qss(theme))

        self.panel.setStyleSheet(f"""
            QWidget#paramPanel {{
                background: {theme.panel.name()};
                border-top: 1px solid {self._rgba(theme.line)};
            }}
            QLabel {{
                color: {theme.rule.name()};
                font-family: "{self.font_family}";
                font-size: 11px;
            }}
            QLabel#paramTitle {{ color: {theme.text.name()};
                                 font-size: 11px; font-weight: bold; }}
            QLabel#paramValue {{ color: {theme.highlight.name()};
                                 font-size: 11px; font-weight: bold; }}
            QSlider::groove:horizontal {{
                height: 4px; background: {self._rgba(theme.line)};
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {theme.highlight.name()}; border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                width: 11px; height: 11px; margin: -4px 0;
                border-radius: 5px; background: {theme.bg_top.name()};
                border: 1px solid {self._rgba(theme.line)};
            }}
            QSlider::handle:horizontal:hover {{ background: {theme.text.name()}; }}
        """)
        self.panel_box.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            + self._scroll_qss(theme))

        for i, f in enumerate(self.fractals):
            item = self.listw.item(i)
            if item is not None:
                item.setIcon(QtGui.QIcon(self._make_icon(f)))

    def _shape_color(self, color: QtGui.QColor) -> QtGui.QColor:
        """图案颜色（按当前主题微调亮度）。"""
        return self._theme().shape(color)

    def _shape_color_at(self, f: Fractal, t: float) -> QtGui.QColor:
        """第 g 代图案的颜色：在 ``color_a``→``color_b`` 之间按 t 取，再按主题压一下。"""
        return self._shape_color(mix_color(f.color_a, f.color_b, t))

    # ------------------------------------------------------------------
    # 初始化辅助
    # ------------------------------------------------------------------

    @staticmethod
    def _pick_font() -> str:
        """挑一个系统里存在的中文字体（都没有则交给 Qt 兜底）。"""
        wanted = ["Microsoft YaHei UI", "Microsoft YaHei", "SimHei",
                  "Noto Sans CJK SC", "PingFang SC", "Sans Serif"]
        try:
            families = QtGui.QFontDatabase.families()       # PyQt6：静态方法
        except Exception:
            families = QtGui.QFontDatabase().families()     # PyQt5：得先建实例
        available = set(families)
        for name in wanted:
            if name in available:
                return name
        return "Sans Serif"

    def font(self, size: float, bold: bool = False,   # type: ignore[override]
             scale: float = 1.0) -> QtGui.QFont:
        """
        按族名取字体。

        Args:
            size: 设计字号（按理想带宽算出来的大小）。
            bold: 是否加粗。
            scale: 带宽压缩比，字号同步缩小（见 :meth:`_band_scale`）。
        """
        f = QtGui.QFont(self.font_family, max(8, int(round(size * scale))))
        f.setBold(bold)
        return f

    # ---- 参数面板 --------------------------------------------------------

    # (键, 标题, 最小, 最大, 初始值, 值显示格式, 换算系数)
    PARAMS = [
        ("branches",    "分叉数量", 1,  6,   2,   "{} 根",  1),
        ("ratio",       "缩小比例", 35, 90,  72,  "{}%",    0.01),
        ("spread",      "分叉张角", 5,  170, 50,  "{}°",    1),
        ("width_ratio", "枝干粗细", 3,  30,  12,  "{}%",    0.01),
        ("jitter",      "随机扰动", 0,  100, 25,  "{}%",    0.01),
    ]

    def _build_param_panel(self) -> QtWidgets.QWidget:
        """参数滑块面板（配色由 :meth:`_apply_style` 统一套上，这里只管结构）。"""
        panel = QtWidgets.QWidget(self)
        panel.setObjectName("paramPanel")

        lay = QtWidgets.QVBoxLayout(panel)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)

        title = QtWidgets.QLabel("参数（拖动即时生效）", panel)
        title.setObjectName("paramTitle")
        lay.addWidget(title)
        lay.addSpacing(4)

        for key, name, lo, hi, val, fmt, scale in self.PARAMS:
            head = QtWidgets.QWidget(panel)
            hl = QtWidgets.QHBoxLayout(head)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setSpacing(4)
            lab = QtWidgets.QLabel(name, head)
            vlab = QtWidgets.QLabel(fmt.format(val), head)
            vlab.setObjectName("paramValue")
            hl.addWidget(lab)
            hl.addStretch(1)
            hl.addWidget(vlab)
            lay.addWidget(head)

            sld = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal, panel)
            sld.setRange(lo, hi)
            sld.setValue(val)
            sld.valueChanged.connect(
                lambda v, k=key, f=fmt, s=scale, l=vlab: self._on_param(k, v, f, s, l))
            lay.addWidget(sld)
            lay.addSpacing(4)
            self.param_rows[key] = (sld, vlab)

        lay.addStretch(1)
        panel.hide()
        return panel

    def _on_param(self, key: str, value: int, fmt: str, scale: float,
                  label) -> None:
        label.setText(fmt.format(value))
        f = self.f
        if not isinstance(f, ParametricTree):
            return
        real = value * scale
        if not f.set_params(**{key: real}):
            return
        # 分叉数量变了，代数上限也跟着变，别让当前代数越界
        if self.gen > f.max_gen:
            self.gen = f.max_gen
        self._pmcache.clear()
        self.update()

    def _sync_param_panel(self) -> None:
        """把面板上的滑块对齐到当前分形保存的参数（切回来后保持原样）。"""
        f = self.f
        if not isinstance(f, ParametricTree):
            return
        for key, sld, val in (("branches", f.branches, None),
                              ("ratio", f.ratio, None),
                              ("spread", f.spread, None),
                              ("width_ratio", f.width_ratio, None),
                              ("jitter", f.jitter, None)):
            widget = self.param_rows.get(key)
            if not widget:
                continue
            slider, label = widget
            scale = dict((p[0], p[6]) for p in self.PARAMS)[key]
            fmt = dict((p[0], p[5]) for p in self.PARAMS)[key]
            shown = int(round(sld / scale))
            # ⚠️ try/finally 不可省：中途抛异常而没复位 ``blockSignals``，滑块会永久哑掉
            slider.blockSignals(True)
            try:
                slider.setValue(shown)
            finally:
                slider.blockSignals(False)
            label.setText(fmt.format(shown))

    def _relayout(self) -> None:
        """
        按当前尺寸重排：画面矩形 / 左侧列表 / 参数面板。

        本控件不用布局管理器（画面是一整块自绘的），所以尺寸一变就在这里算
        一次；所有位置都从当前的宽高推导出来，不假设任何固定尺寸：

        - 列表宽度随控件收窄（:data:`LIST_W` → :data:`LIST_MIN_W`）；
        - 参数面板放在提示行上方（否则一显示就会压住那行提示），至多占一半
          高度，且至少给列表留下 :data:`LIST_MIN_H`；面板内容比这块高时由
          外面的滚动区接管。
        """
        w, h = max(1, self.width()), max(1, self.height())
        self.list_w = int(min(self.LIST_W, max(self.LIST_MIN_W, w * 0.24)))
        self.canvas = QtCore.QRectF(self.list_w, 0, max(1, w - self.list_w), h)

        show = self.f.key == "param_tree"
        self.panel_box.setVisible(show)
        ph = 0
        if show:
            want = self.panel.sizeHint().height()                # 面板想要多高
            room = max(0.0, h - self.HINT_H - self.LIST_MIN_H)   # 列表至少要留的
            ph = int(max(0.0, min(want, h * 0.5, room)))         # 至多占一半
            if ph > 0:
                self.panel_box.setGeometry(0, h - self.HINT_H - ph,
                                           self.list_w, ph)
        self.listw.setGeometry(0, 0, self.list_w,
                               max(40, h - self.HINT_H - ph))

    def sizeHint(self) -> QtCore.QSize:  # noqa: N802
        """独立打开（或放进别的布局）时的建议大小；只是偏好，不撑大父窗口。"""
        return QtCore.QSize(self.PREF_W, self.PREF_H)

    # ------------------------------------------------------------------
    # 宿主（zmlx）钩子
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """
        GUI 刷新钩子（切回本标签页时会被调）：重排 + 重画，不重算图案。

        顺带对一次主题：zmlx 重新加载 ``zml_window_style.qss`` 时不一定发
        ``PaletteChange``，这里的 :meth:`_sync_theme` 在主题没变时是空操作。
        """
        self._sync_theme()
        self._relayout()
        self.update()

    def cleanup_before_tab_close(self) -> None:
        """标签页被关闭前的收尾：停掉所有定时器（都不阻塞）。"""
        self.anim.stop()
        self.auto_timer.stop()
        self.toast_timer.stop()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.setFocus()      # 切到本标签页后，空格/方向键立刻可用

    def hideEvent(self, event) -> None:  # noqa: N802
        super().hideEvent(event)
        if self.auto:
            # 切走就暂停自动播放：生成新一代可能很重，别在看不见的标签页里空转
            self.auto = False
            self.auto_timer.stop()

    # ---- 缩略图 ----------------------------------------------------------

    def _make_icon(self, f: Fractal) -> QtGui.QPixmap:
        """左侧列表的小示意图：用很低的代数画，10 个图标一起生成也很快。"""
        size = 44                                   # 先画大再缩小，边缘更干净
        pm = QtGui.QPixmap(size, size)
        pm.fill(QtCore.Qt.GlobalColor.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        rect = QtCore.QRectF(1, 1, size - 2, size - 2)
        try:
            if f.mode == MODE_ROWS:
                self._paint_rows(p, rect, f, min(f.max_gen, 2), 1.0, icon=True)
            else:
                g = min(f.max_gen, 6 if f.mode == MODE_CURVE else
                        (5 if f.mode == MODE_ADD else 3))
                # 生长型要按"长到第 g 代时的范围"取景；用 fit_bbox()（整棵树）
                # 的话缩略图里就只剩一棵小苗，占不满格子
                bb = f.bbox_upto(g) if f.mode == MODE_ADD else f.view_bbox(g)
                self._paint_any(p, rect, f, g, 1.0, icon=True, bbox=bb)
        except Exception:
            p.setBrush(self._theme().rule)      # 画不出来就画个灰点
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.drawEllipse(rect)
        p.end()
        return pm.scaled(size // 2, size // 2,
                         QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                         QtCore.Qt.TransformationMode.SmoothTransformation)

    def _paint_any(self, p: QtGui.QPainter, rect: QtCore.QRectF, f: Fractal, g: int,
                   t: float, icon: bool = False, bbox=None) -> None:
        """按分形自己的演化方式来画（缩略图和主画面共用这一套）。"""
        if f.mode == MODE_CURVE:
            self._paint_curve(p, rect, f, g, t, icon=icon, bbox=bbox)
        elif f.mode == MODE_ADD:
            self._paint_add(p, rect, f, g, t, icon=icon, bbox=bbox)
        else:
            self._paint_area(p, rect, f, g, t, icon=icon, bbox=bbox)

    # ------------------------------------------------------------------
    # 当前分形
    # ------------------------------------------------------------------

    @property
    def f(self) -> Fractal:
        return self.fractals[self.fi]

    @property
    def gen(self) -> int:
        return self._gen

    @gen.setter
    def gen(self, value: int) -> None:
        """
        代数只能落在 [0, max_gen] 里，在赋值这一处统一兜住。

        参数树的 max_gen 是随分叉数量变的（6 叉只有 5 代）。万一代数越界，
        shapes(g) 会老老实实去算 6^9 = 1000 万根树枝，界面直接卡死 ——
        与其指望每条调用路径都记得夹一下，不如在这一处夹死。
        """
        self._gen = max(0, min(int(value), self.f.max_gen))

    def select_fractal(self, idx: int) -> None:
        """切到第 idx 种图案（越界或原地不动则什么也不做）。"""
        if idx < 0 or idx >= len(self.fractals) or idx == self.fi:
            return
        self.anim.stop()
        self.animating = False
        self.auto = False
        self.auto_timer.stop()
        self.fi = idx
        self.gen = 0
        self.t = 1.0
        self._pmcache.clear()
        self.listw.setCurrentRow(idx)
        self._sync_param_panel()
        self._relayout()          # 参数树才显示面板，换图案要重排左侧栏
        self._flash(f"已切换到「{self.f.name}」")
        self.update()

    def move_selection(self, delta: int) -> None:
        """在图案列表里前后挪一格。"""
        self.select_fractal((self.fi + delta) % len(self.fractals))

    # ------------------------------------------------------------------
    # 交互
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # noqa: N802
        key = event.key()

        if key == QtCore.Qt.Key.Key_Space:
            self.step_forward()
        elif key == QtCore.Qt.Key.Key_Up:
            self.move_selection(-1)
        elif key == QtCore.Qt.Key.Key_Down:
            self.move_selection(1)
        elif key == QtCore.Qt.Key.Key_A:
            self.toggle_auto()
        elif key == QtCore.Qt.Key.Key_Right:
            self.step_forward()
        elif key == QtCore.Qt.Key.Key_Left:
            self.step_back()
        elif key == QtCore.Qt.Key.Key_R:
            self.restart()
        elif key == QtCore.Qt.Key.Key_S:
            self.save_png()
        elif key in (QtCore.Qt.Key.Key_Escape, QtCore.Qt.Key.Key_Q):
            # 在标签页里 close() 只会把页面藏起来（留一个空白页），所以只在
            # 独立窗口里退出，别的场合提示一句
            if self.isWindow():
                self.close()
            else:
                self._flash("在标签页里请用标签上的关闭按钮")
        else:
            super().keyPressEvent(event)

    # ---- 演化控制 --------------------------------------------------------

    def step_forward(self) -> None:
        if self.gen >= self.f.max_gen:
            self._flash(f"「{self.f.name}」到第 {self.f.max_gen} 代就是最细的了")
            return
        if self.animating:
            self._check_anim_lock()
        if self.animating:
            return
        self.gen += 1
        self._start_anim()

    def step_back(self) -> None:
        if self.gen == 0:
            self._flash("已经回到第 0 代了")
            return
        self._stop_anim()
        self.gen -= 1
        self.update()

    def restart(self) -> None:
        self._stop_anim()
        self.auto = False
        self.auto_timer.stop()
        self.gen = 0
        self._flash("已重来，回到第 0 代")
        self.update()

    def toggle_auto(self) -> None:
        self.auto = not self.auto
        if self.auto:
            if self.gen >= self.f.max_gen:
                self.gen = 0
                self.t = 1.0
            self.auto_timer.start()
            self._flash("自动播放中…")
        else:
            self.auto_timer.stop()
            self._flash("自动播放已暂停")
        self.update()

    def _auto_step(self) -> None:
        if self.gen >= self.f.max_gen:
            if self.auto:
                self.auto = False
                self.auto_timer.stop()
                self._flash(f"演化完成！共 {self.f.max_gen} 代")
                self.update()
            return
        self.gen += 1
        self._start_anim()

    def _start_anim(self) -> None:
        self.t = 0.0
        self.animating = True
        self.anim_started = time.monotonic()
        self.anim.stop()
        self.anim.start()
        self.update()

    def _stop_anim(self) -> None:
        self.anim.stop()
        self.animating = False
        self.t = 1.0
        self.update()

    def _on_anim(self, value: float) -> None:
        self.t = float(value)
        if self.t >= 1.0:
            self.animating = False
        self.update()

    def _on_anim_done(self) -> None:
        self.animating = False
        self.t = 1.0
        self.update()

    def _check_anim_lock(self) -> None:
        """
        兜底解锁。

        动画正常跑完会发 finished 信号，动画期间按空格是有意忽略的（防连按）。
        但万一动画卡住不发信号，按键就永久失灵了，所以超过 2 倍动画时长
        就强制解锁。
        """
        if not self.animating:
            return
        if self.t >= 1.0 or self.anim.state() != QtCore.QVariantAnimation.State.Running:
            self.animating = False
            return
        if time.monotonic() - self.anim_started > (self.ANIM_MS / 1000.0) * 2.0:
            self.anim.stop()
            self.animating = False
            self.t = 1.0

    # ---- 小提示 ----------------------------------------------------------

    def _flash(self, msg: str) -> None:
        self.toast = msg
        self.toast_timer.start(2600)
        self.update()

    def _clear_toast(self) -> None:
        self.toast = ""
        self.update()

    # ---- 保存图片 --------------------------------------------------------

    def save_png(self) -> None:
        import datetime
        name = (f"{self.f.key}_第{self.gen}代_"
                f"{datetime.datetime.now():%Y%m%d_%H%M%S}.png")
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
        self.grab().save(path, "PNG")
        self._flash(f"已保存图片：{name}")

    # ------------------------------------------------------------------
    # 尺寸
    # ------------------------------------------------------------------

    def resizeEvent(self, event) -> None:  # noqa: N802
        self._pmcache.clear()          # 尺寸变了，缓存的底图作废
        self._relayout()
        super().resizeEvent(event)

    def _bands(self) -> Tuple[float, float]:
        """
        顶部标题带、底部状态带的高度。

        够高时就是理想高度（:data:`HEADER_H` / :data:`FOOTER_H`）；不够高时
        两条带按比例一起压缩，把画面留在 :data:`BODY_MIN_RATIO` 以上
        （绝对下限 :data:`BODY_MIN_H`）—— 所以本控件永远不需要靠"撑大父窗口"
        来保证自己画得下，界面变矮时先缩的是标题和状态栏，不是图案。
        """
        h = float(self.height())
        hdr, ftr = self.HEADER_H, self.FOOTER_H
        room = max(h - max(h * self.BODY_MIN_RATIO, self.BODY_MIN_H), 0.0)
        if hdr + ftr > room:
            k = room / (hdr + ftr)
            hdr, ftr = hdr * k, ftr * k
        return hdr, ftr

    @staticmethod
    def _band_scale(band_h: float, ideal: float) -> float:
        """带宽压缩后带内文字跟着缩多少（不小于 0.5，再小就看不清了）。"""
        return max(0.5, min(1.0, band_h / ideal))

    def _body_rect(self) -> QtCore.QRectF:
        """画面矩形：控件高度扣掉上下两条带，剩下的就是画图案的地方。"""
        c = self.canvas
        hdr, ftr = self._bands()
        return QtCore.QRectF(c.left(), c.top() + hdr, c.width(),
                             max(40.0, c.height() - hdr - ftr))

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing, True)

        self._draw_background(p)

        f = self.f
        rect = self._body_rect()
        if f.mode == MODE_ROWS:
            self._paint_rows(p, rect, f, self.gen, self.t)
        else:
            self._paint_any(p, rect, f, self.gen, self.t,
                            bbox=f.view_bbox(self.gen))

        self._draw_header(p)
        self._draw_footer(p)

    def _draw_background(self, p: QtGui.QPainter) -> None:
        theme = self._theme()
        grad = QtGui.QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, theme.bg_top)
        grad.setColorAt(1.0, theme.bg_bottom)
        p.fillRect(self.rect(), grad)

    # 图层缓存：第 g 代的图案画一次就存成透明底图，动画时只要贴图 + 改透明度，
    # 这样即使最深一代有几十万个形状，动画也能保持流畅（每帧只是两次贴图）。
    def _layer(self, tag: str, g: int, render_fn, aa: bool = True) -> QtGui.QPixmap:
        key = (self.fi, tag, g, self.width(), self.height())
        cached = self._pmcache.get(key)
        if cached is not None:
            return cached
        if len(self._pmcache) > 16:
            self._pmcache.clear()
        pm = QtGui.QPixmap(self.size())
        pm.fill(QtCore.Qt.GlobalColor.transparent)
        p = QtGui.QPainter(pm)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, aa)
        render_fn(p)
        p.end()
        self._pmcache[key] = pm
        return pm

    # ---- 挖洞型 ----------------------------------------------------------

    # ---- 一帧画多少 ------------------------------------------------------

    @staticmethod
    def _px_size(poly: Poly, fit: "Fit") -> float:
        """这个图形画在屏幕上有多少像素（取外接矩形的长边）。"""
        x0 = x1 = poly[0][0]
        y0 = y1 = poly[0][1]
        for x, y in poly:
            if x < x0:
                x0 = x
            elif x > x1:
                x1 = x
            if y < y0:
                y0 = y
            elif y > y1:
                y1 = y
        return max(x1 - x0, y1 - y0) * fit.s

    def _cap_shapes(self, items: List[Tuple[int, Poly]], fit: "Fit",
                    cap: Optional[int] = None) -> List[Tuple[int, Poly]]:
        """
        一帧最多画 cap 个图形，超了按"屏幕尺寸从大到小"保留前面的。

        排序只在真的超过上限时才做 —— 正常最深一代 3 万出头，一次都不排，
        不会白白花时间（这也是不能把上限设得太低的原因：那样每帧都要排序，
        反而更慢，而且会把看得见的碎块也丢掉）。
        """
        cap = self.MAX_SHAPES_DRAWN if cap is None else cap
        if len(items) <= cap:
            return items
        sized = sorted(((-self._px_size(p, fit), i) for i, (_, p) in enumerate(items)))
        keep = sorted(i for _, i in sized[:cap])
        return [items[i] for i in keep]

    def _draw_area_layer(self, p: QtGui.QPainter, f: Fractal, g: int,
                         rect: QtCore.QRectF, bbox=None) -> None:
        theme = self._theme()
        fit = Fit(bbox or f.fit_bbox(), rect, margin=fit_margin(rect))
        shapes = f.shapes(g)
        if len(shapes) > self.MAX_SHAPES_DRAWN:  # 只有真超限才去包一层、排一次序
            shapes = [poly for _, poly in
                      self._cap_shapes([(g, q) for q in shapes], fit)]
        path = QtGui.QPainterPath()
        for poly in shapes:
            path.addPolygon(fit.poly(poly))

        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(self._shape_color_at(f, g / max(1, f.max_gen)))
        p.drawPath(path)

        # 最新一代描一圈细边，强调"又被切小了"。数量太多就不描了，太费时间。
        # 边色取背景色（半透明），亮色主题下就是白边，暗色主题下是深边。
        if g > 0 and len(shapes) <= 6000:
            edge = QtGui.QColor(theme.bg_top)
            edge.setAlpha(150)
            pen = QtGui.QPen(edge)
            pen.setWidthF(0.7)
            p.setPen(pen)
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            p.drawPath(path)

    def _paint_area(self, p: QtGui.QPainter, rect: QtCore.QRectF, f: Fractal,
                    g: int, t: float, icon: bool = False, bbox=None) -> None:
        if icon:
            self._draw_area_layer(p, f, g, rect, bbox=bbox)
            return

        # 形状多到一定程度，抗锯齿的收益就很小了（每个方块只有一两像素），
        # 但代价是 2~3 倍的绘制时间，所以这里直接关掉换流畅。
        aa = f.count(g) <= 8000
        p.drawPixmap(0, 0, self._layer(
            "area", g, lambda pp: self._draw_area_layer(pp, f, g, rect), aa))

        # 动画：把上一代的"大块"盖在新图案上慢慢淡出，
        # 中心的洞看起来就像从无到有被挖开。
        if g > 0 and t < 1.0:
            prev = self._layer(
                "area", g - 1,
                lambda pp: self._draw_area_layer(pp, f, g - 1, rect), aa)
            p.setOpacity(max(0.0, min(1.0, 1.0 - t)))
            p.drawPixmap(0, 0, prev)
            p.setOpacity(1.0)

    # ---- 生长型 ----------------------------------------------------------

    def _draw_add_layer(self, p: QtGui.QPainter, f: Fractal, g: int,
                        rect: QtCore.QRectF, older: bool, bbox=None) -> None:
        """older=True 画第 0..g-1 代（暗一些），False 只画第 g 代（亮）。"""
        fit = Fit(bbox or f.fit_bbox(), rect, margin=fit_margin(rect))
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        if older:
            gis, dim = list(range(0, g)), True
        else:
            gis, dim = [g], False

        # 生长型越老的枝越粗、越新的越细，所以把各代摊平了一起过闸门：
        # 真超限时保留的是屏幕上最大的那些（老枝），符合"从大到小"的取舍。
        # _cap_shapes 返回时保持原顺序，而 flat 是按代铺的，所以结果天然按代分段，
        # 可以一代合成一条路径再画 —— 一个图形一次 drawPath 会慢很多。
        flat = [(gi, poly) for gi in gis for poly in f.shapes(gi)]
        kept = self._cap_shapes(flat, fit)

        cur: Optional[int] = None
        path = QtGui.QPainterPath()
        for gi, poly in kept:
            if cur is not None and gi != cur:
                self._flush_add(p, f, path, cur, dim)
                path = QtGui.QPainterPath()
            cur = gi
            path.addPolygon(fit.poly(poly))
        if cur is not None:
            self._flush_add(p, f, path, cur, dim)

        # 树梢的小圆点（只有参数树会返回非空）
        if not older:
            tips = f.tip_points(g)
            if tips:
                p.setBrush(self._shape_color(
                    mix_color(f.color_b, self._theme().bg_top, 0.25)))
                dot = QtGui.QPainterPath()
                for (tx, ty, tr) in tips:
                    r = max(0.35, tr * fit.s)   # 太小就画不出来，兜个底
                    dot.addEllipse(fit.pt((tx, ty)), r, r)
                p.drawPath(dot)

    def _flush_add(self, p: QtGui.QPainter, f: Fractal, path: QtGui.QPainterPath,
                   gi: int, dim: bool) -> None:
        c = self._shape_color_at(f, gi / max(1, f.max_gen))
        if dim:
            # 老一代往背景色淡下去（暗色主题变暗、亮色主题变浅，两边都是"退到后面"）
            c = mix_color(c, self._theme().bg_bottom, 0.35)
        p.setBrush(c)
        p.drawPath(path)

    def _paint_add(self, p: QtGui.QPainter, rect: QtCore.QRectF, f: Fractal,
                   g: int, t: float, icon: bool = False, bbox=None) -> None:
        if icon:
            self._draw_add_layer(p, f, g, rect, older=True, bbox=bbox)
            self._draw_add_layer(p, f, g, rect, older=False, bbox=bbox)
            return

        if g > 0:
            p.drawPixmap(0, 0, self._layer(
                "add_old", g,
                lambda pp: self._draw_add_layer(pp, f, g, rect, older=True)))
        newest = self._layer(
            "add_new", g, lambda pp: self._draw_add_layer(pp, f, g, rect, older=False))
        if t < 1.0:
            p.setOpacity(max(0.0, min(1.0, t)))
        p.drawPixmap(0, 0, newest)
        p.setOpacity(1.0)

    # ---- 曲线型 ----------------------------------------------------------

    @staticmethod
    def _curve_pen(color: QtGui.QColor, width: float) -> QtGui.QPen:
        # 平头 + 斜接：细线上看不出差别，但比圆头圆角快 2.6 倍（龙形曲线尤其明显）
        pen = QtGui.QPen(color)
        pen.setWidthF(width)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.FlatCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.BevelJoin)
        return pen

    # 点数超过这个值就不做"描线"动画了，改成整体淡入（描线每帧都要重画整条曲线）
    CURVE_DRAW_ON_MAX = 8000

    def _draw_curve_layer(self, p: QtGui.QPainter, f: Fractal, g: int,
                          rect: QtCore.QRectF, bbox=None) -> None:
        """只画第 g 代的曲线本身。"""
        fit = Fit(bbox or f.view_bbox(g), rect, margin=fit_margin(rect))
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        pts = f.shapes(g)[0]
        if len(pts) < 2:
            return
        color = self._shape_color_at(f, g / max(1, f.max_gen))
        p.setPen(self._curve_pen(color, 2.2))
        p.drawPolyline(QtGui.QPolygonF([fit.pt(pt) for pt in pts]))

    def _paint_curve(self, p: QtGui.QPainter, rect: QtCore.QRectF, f: Fractal,
                     g: int, t: float, icon: bool = False, bbox=None) -> None:
        if icon:
            self._draw_curve_layer(p, f, g, rect, bbox=f.view_bbox(g))
            return

        pts = f.shapes(g)[0]
        n = len(pts)
        if not pts or n < 2:
            return
        fit = Fit(f.view_bbox(g), rect, margin=fit_margin(rect))

        if t < 1.0 and n <= self.CURVE_DRAW_ON_MAX:
            # 点数不多：像用笔描出来一样，只画前 t 段长度
            color = self._shape_color_at(f, g / max(1, f.max_gen))
            p.setPen(self._curve_pen(color, 2.2))
            p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            poly = QtGui.QPolygonF([fit.pt(pt) for pt in pts])
            segs = [math.hypot(poly[i + 1].x() - poly[i].x(),
                               poly[i + 1].y() - poly[i].y())
                    for i in range(poly.count() - 1)]
            want = sum(segs) * max(0.0, min(1.0, t))
            acc = 0.0
            partial = QtGui.QPolygonF([poly[0]])
            for i, d in enumerate(segs):
                if acc + d <= want:
                    partial.append(poly[i + 1])
                    acc += d
                else:
                    remain = want - acc
                    if d > 1e-9 and remain > 0:
                        k = remain / d
                        partial.append(QtCore.QPointF(
                            poly[i].x() + (poly[i + 1].x() - poly[i].x()) * k,
                            poly[i].y() + (poly[i + 1].y() - poly[i].y()) * k))
                    break
            if partial.count() >= 2:
                p.drawPolyline(partial)
        else:
            # 点数太多：贴缓存的整条曲线，用淡入代替描线，保证流畅
            pm = self._layer(
                "curve_new", g,
                lambda pp: self._draw_curve_layer(pp, f, g, rect,
                                                  bbox=f.view_bbox(g)),
                aa=n <= 20000)
            if t < 1.0:
                p.setOpacity(max(0.0, min(1.0, t)))
            p.drawPixmap(0, 0, pm)
            p.setOpacity(1.0)

    # ---- 分层型（康托尔尘埃）---------------------------------------------

    def _paint_rows(self, p: QtGui.QPainter, rect: QtCore.QRectF, f: Fractal,
                    g: int, t: float, icon: bool = False) -> None:
        rows = (f.max_gen + 1) if not icon else min(3, f.max_gen + 1)
        row_h = rect.height() / rows
        # 缩略图只有 44px，边距要小一点才放得下
        margin = 2.0 if icon else 8.0
        avail_w = max(10.0, rect.width() - 2 * margin)
        bar_h = max(2.0, min(row_h * 0.42, 26.0))
        # 注意：横条的 x 必须以 rect.left() 为原点。
        # 画布左边是留给左侧列表的，少加这个偏移整排横条就会整体左移，
        # 左段被侧栏盖住、中间那个"洞"也就不在三分之一的位置上了。
        x_origin = rect.left() + margin

        for gi in range(rows):
            y = rect.top() + gi * row_h
            newest = gi == g
            c = self._shape_color_at(f, gi / max(1, f.max_gen))
            if not newest:
                c = mix_color(c, self._theme().bg_bottom, 0.30 if icon else 0.45)
            else:
                c = QtGui.QColor(c)
                if not icon and t < 1.0:
                    c.setAlphaF(max(0.0, min(1.0, t)))

            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.setBrush(c)
            for seg in f.shapes(gi):
                xs = [q[0] for q in seg]
                x0, x1 = min(xs), max(xs)
                w = max(1.0, (x1 - x0) * avail_w)
                p.drawRect(QtCore.QRectF(x_origin + x0 * avail_w,
                                  y + (row_h - bar_h) / 2.0, w, bar_h))

    # ---- 顶部标题 --------------------------------------------------------

    def _draw_header(self, p: QtGui.QPainter) -> None:
        c = self.canvas
        w = c.width()
        left = c.left()
        theme = self._theme()
        accent = self._shape_color_at(self.f, self.gen / max(1, self.f.max_gen))

        hdr, _ = self._bands()
        s = self._band_scale(hdr, self.HEADER_H)

        p.setPen(theme.text)
        p.setFont(self.font(22, bold=True, scale=s))
        p.drawText(QtCore.QRectF(left, hdr * 0.143, w, hdr * 0.190),
                   QtCore.Qt.AlignmentFlag.AlignHCenter |
                   QtCore.Qt.AlignmentFlag.AlignVCenter,
                   f"分形演化 · {self.f.name}")

        p.setPen(theme.rule)
        p.setFont(self.font(11, scale=s))
        p.drawText(QtCore.QRectF(left + 24, hdr * 0.345, w - 48, hdr * 0.131),
                   QtCore.Qt.AlignmentFlag.AlignHCenter |
                   QtCore.Qt.AlignmentFlag.AlignVCenter,
                   self.f.rule)

        badge_h = hdr * 0.238
        badge_w = min(236.0, max(120.0, w - 24.0))
        badge = QtCore.QRectF(left + (w - badge_w) / 2, hdr * 0.536,
                              badge_w, badge_h)
        bg = QtGui.QColor(accent)
        bg.setAlphaF(0.16)
        p.setBrush(bg)
        pen = QtGui.QPen(QtGui.QColor(accent.red(), accent.green(), accent.blue(), 190))
        pen.setWidthF(1.2)
        p.setPen(pen)
        radius = min(20.0, badge_h / 2)
        p.drawRoundedRect(badge, radius, radius)
        p.setPen(accent)
        p.setFont(self.font(17, bold=True, scale=s))
        p.drawText(badge, QtCore.Qt.AlignmentFlag.AlignCenter, f"第 {self.gen} 代")

        # 左侧面板底部的提示（位置跟着 _relayout 预留的那一条走）
        p.setPen(theme.side_hint)
        p.setFont(self.font(10, bold=True))
        p.drawText(QtCore.QRectF(0, self.height() - self.HINT_H,
                                 self.list_w, self.HINT_H),
                   QtCore.Qt.AlignmentFlag.AlignCenter, "↑ ↓ 切换图案")

    # ---- 底部状态 --------------------------------------------------------

    def _draw_footer(self, p: QtGui.QPainter) -> None:
        c = self.canvas
        w = c.width()
        left = c.left()
        theme = self._theme()

        # 带内各行的位置都按当前带高取，带宽压缩时整体跟着往上收
        _, ftr = self._bands()
        s = self._band_scale(ftr, self.FOOTER_H)
        top = c.top() + c.height() - ftr
        y = top + ftr * 0.409

        p.setFont(self.font(12, scale=s))
        p.setPen(theme.stat)
        p.drawText(QtCore.QRectF(left, y, w, ftr * 0.125),
                   QtCore.Qt.AlignmentFlag.AlignCenter,
                   self.f.stat_text(self.gen))

        bar_w = min(560.0, max(120.0, w - 200.0))
        bar = QtCore.QRectF(left + (w - bar_w) / 2, top + ftr * 0.580, bar_w, 7)
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(theme.track)
        p.drawRoundedRect(bar, 3.5, 3.5)

        mx = max(1, self.f.max_gen)
        ratio = self.gen / mx
        if ratio > 0:
            fill = QtCore.QRectF(bar.left(), bar.top(),
                                 bar.width() * ratio, bar.height())
            grad = QtGui.QLinearGradient(bar.left(), 0, bar.right(), 0)
            grad.setColorAt(0.0, self._shape_color(self.f.color_a))
            grad.setColorAt(1.0, self._shape_color(self.f.color_b))
            p.setBrush(grad)
            p.drawRoundedRect(fill, 3.5, 3.5)

        for i in range(mx + 1):
            x = bar.left() + bar.width() * (i / mx)
            col = (self._shape_color_at(self.f, i / mx)
                   if i <= self.gen else theme.dot_off)
            p.setBrush(col)
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.drawEllipse(QtCore.QPointF(x, bar.center().y()),
                          4.0 if i == self.gen else 2.5,
                          4.0 if i == self.gen else 2.5)

        p.setPen(theme.hint)
        p.setFont(self.font(11, scale=s))
        auto_txt = "A 自动播放：开" if self.auto else "A 自动播放：关"
        p.drawText(QtCore.QRectF(left, top + ftr * 0.705, w, ftr * 0.125),
                   QtCore.Qt.AlignmentFlag.AlignCenter,
                   f"空格 演化一代   ↑↓ 换图案   {auto_txt}   "
                   f"← → 前后翻   R 重来   S 存图   Esc 退出")

        # 最底下一行只放一条消息：临时提示优先，其次才是"到顶了"的提醒。
        # 两者以前各画各的、位置几乎重合，一旦同时出现就会叠字。
        msg, color, size = None, None, 11
        if self.toast:
            msg, color, size = self.toast, theme.msg_ok, 12
        elif self.gen >= self.f.max_gen:
            msg = (f"★ 已到第 {self.f.max_gen} 代（最细的一代）"
                   f"—— 按 R 重来，或按 ← 后退")
            color = theme.msg_warn
        if msg:
            p.setPen(color)
            p.setFont(self.font(size, bold=True, scale=s))
            p.drawText(QtCore.QRectF(left, top + ftr * 0.830, w, ftr * 0.125),
                       QtCore.Qt.AlignmentFlag.AlignCenter, msg)

    # ---- 自测 / 性能 -----------------------------------------------------

    @classmethod
    def benchmark(cls) -> None:
        """
        把每种分形都算到最高代，量一下生成和绘制耗时（``--benchmark``）。

        用来定各代的代数上限：哪一行数值突然变大，那一种就该考虑降代数了。
        """
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        win = cls()
        win.resize(cls.PREF_W, cls.PREF_H)
        win.show()
        app.processEvents()

        print(f"{'分形':<20}{'代数':>4}{'数量':>11}{'生成ms':>9}{'绘制ms':>9}")
        print("-" * 56)
        for i, f in enumerate(win.fractals):
            t0 = time.perf_counter()
            f.ensure(f.max_gen)
            t_build = (time.perf_counter() - t0) * 1000

            win.fi = i
            win.gen = f.max_gen
            win.t = 1.0
            win.update()
            app.processEvents()
            t0 = time.perf_counter()
            win.grab()
            t_draw = (time.perf_counter() - t0) * 1000
            print(f"{f.name:<20}{f.max_gen:>4}{f.count(f.max_gen):>11,}"
                  f"{t_build:>9.0f}{t_draw:>9.0f}")


# --------------------------------------------------------------------------
# 入口
# --------------------------------------------------------------------------

def test_1() -> int:
    """直接运行本文件时的自测：开一个独立窗口（空格演化、↑↓ 换图案）。"""
    app = QtWidgets.QApplication(sys.argv)
    win = FractalEvolutionView()
    win.show()
    return app.exec()




# ---------------------------------------------------------------------------
# 插件入口：注册命令与菜单（被 load_all exec 执行时才会跑）
# ---------------------------------------------------------------------------
def show_classic_fractal():
    """打开「经典分形」标签页（菜单项与 ``gui.show_classic_fractal()`` 都走它）."""
    from zmlx.ui import gui

    gui.get_widget(FractalEvolutionView, caption='经典分形')
    gui.hide_console()


@execute_once(file=__file__)
def setup_ui():
    """注册命令与菜单项（本文件作为插件被 ``load_all`` 执行时调用）.

    ⚠️ 本函数在**控制台内核线程**里执行，``gui.add_func`` / ``gui.add_action``
    会被 GuiApi 派发到主线程执行（见 ``zmlx/ui/main.py`` 的 ``__console_kernel``）。
    """
    from zmlx.ui import gui

    gui.add_func('show_classic_fractal', show_classic_fractal)
    gui.add_action(
        menu=['演示'],
        text='经典分形',
        tooltip='分形图案逐代演化：空格演化、↑↓ 换图案、A 自动播放、S 存图',
        slot=show_classic_fractal,
        overwrite=False,
    )


if __name__ == '__zml_plugin__':
    # 插件路径：由 load_all exec 执行，**没人会替我们调 setup_ui()**，所以在
    # 模块顶层自己调（见 zmlx/ui/plugins/__init__.py）。
    setup_ui()

if __name__ == '__main__':
    # 直接运行本文件：独立窗口自测（等价于搬入前的 ``python -m ...``）。
    # ⚠️ 用独立的 ``if`` 而不是 ``elif``：两种运行方式的判断互不相干，
    #    各自独立判断更清楚，也便于在 IDE 里单独调试下面这一支。
    if '--benchmark' in sys.argv:
        FractalEvolutionView.benchmark()
        sys.exit(0)
    sys.exit(test_1())
