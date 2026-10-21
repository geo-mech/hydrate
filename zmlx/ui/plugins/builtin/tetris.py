# ** name = '螺螺是方块'
# ** desc = '彩蛋游戏：俄罗斯方块（SRS 旋转 + 踢墙表）。默认不加载，勾选后在「帮助 → 彩蛋」下出现'
# ** enabled = False
"""螺螺是方块（Tetris）游戏标签页 —— 菜单「帮助 → 彩蛋 → 螺螺是方块」.

移植自 https://gitee.com/zhangzhaobin/game-development 的《俄罗斯方块.py》
（Tetris Guideline：SRS 旋转 + 踢墙表、7-bag、锁定延迟、幽灵块、Hold、
Next×5、B2B / Combo / T-Spin / Perfect Clear、官方重力曲线），做成一个可嵌进
标签页的 ``QWidget``。游戏规则、渲染与音效逻辑与原版逐行一致，本文件只做了三
处适配（见下），以便在 zmlx 里安全运行。

★ **本模块是个彩蛋，故意不挂菜单**：入口是「帮助 → 关于」页面上、
「Python解释器」一行右侧的**「彩蛋」按钮**（见 ``zmlx/ui/tabs/about.py``），
它直接调 ``gui.show_tetris()``。这样一来它不会占菜单、也不会被误当成
正经功能，但翻到「关于」页的人都能发现。

与原版的差异（仅适配，不改规则）
--------------------------------

1. **Qt 绑定**：原版 ``from PyQt6 import ...``，这里改走 ``zmlx.ui.pyqt``
   （同时支持 PyQt6 / PyQt5，且无头模式下不会因缺少 Qt 而导入失败）。
   ⚠️ 枚举一律写全路径（``QtCore.Qt.Key.Key_Left`` 风格沿用了原版的 ``Qt.``
   别名），因为 PyQt6 把枚举收进了各自的 Enum 命名空间。
2. **可写路径**：音效缓存与最高分存档原本落在脚本同目录 /
   ``QStandardPaths``；这里统一改到 ``app_data.root('tetris')`` ——
   zmlx 的安装目录不保证可写（也可能是只读的 site-packages），而且不该被
   ``.wav`` 与 ``save.json`` 污染。
3. **入口**：原版的 ``main()``（含 ``--selftest`` / ``--shot`` 等命令行）留在
   原仓库；这里只保留 ``TetrisView`` 控件、``gui.show_tetris()`` 命令与
   ``setup_ui()``。

本模块往磁盘写什么
------------------

**只有两处真正的写入**，都落在 ``app_data.root('tetris')`` 下（本机实测：
``C:\\Users\\<用户>\\AppData\\Roaming\\zml\\tetris``，可用 :func:`_data_dir` 复核）：

1. ``save.json`` —— 最高分 / 局数 / 累计消行 / 最佳连击 + 全部设置
   （见 :meth:`TetrisWidget.write_save`）。每局结束、改设置、静音、关标签时各写一次。
2. ``sfx/*.wav`` + ``sfx/.version`` —— 20 个程序合成的音效（见 :func:`build_sounds`）。
   只在**首次运行**（或 :data:`SFX_VERSION` 变了）时才写，之后一直是读缓存。

为便于事后排查，这两处**每次实际写入**都会往 ``record.jsonl`` 追加一条审计
（``kind="write"``：时间 / 文件 / 字节数 / 谁触发 / 成功与否），每局结束再追加
一条战绩（``kind="game"``）。文件是 JSONL（一行一条 JSON），可以直接看，也可以用
:func:`read_record` 读回来 —— 详见第 0 节。

⚠️ 注意 ``pr.save()`` 那几处**不是**写磁盘：那是 ``QPainter`` 的状态栈
（``save`` / ``restore`` 成对），与文件系统无关。

⚠️ **控件的定时器只在可见时跑**：原版游戏一开就一直 60 FPS 重绘，而标签页可能
被切到后台、甚至从未被打开（``gui_restore`` 恢复的标签）。所以这里把 ``QTimer``
的启停挂到 ``showEvent`` / ``hideEvent``：离开标签页即停表，回来再续上，并且
把停表期间的时间差丢掉（否则回来时会按"离屏了几分钟"一次性追帧）。
切走时还会自动暂停，避免回来发现方块已经堆死。

操作
----
    ← →          左右移动（DAS / ARR 可调，见 F2 设置）
    ↓            软降（按住加速下落）
    空格         硬降（直接落底并锁定）
    ↑ / X        顺时针旋转
    Z / Ctrl     逆时针旋转
    A            旋转 180°
    C / Shift    暂存（Hold，每个方块限一次）
    P / Esc      暂停 / 继续
    R            重开一局
    M            静音（全部声音）
    B            背景音乐开关
    F1           键位帮助
    F2           设置（幽灵块 / 网格 / 音效 / 音乐 / 震屏 / DAS / ARR / 起始等级）
    F11          全屏开关
    Esc          结算界面 = 退出

Created by DeepSeek, 2026-10-13
"""

from __future__ import annotations

import base64
import datetime
import json
import math
import random
import re
import sys
import tempfile
import wave
from array import array
from pathlib import Path
from typing import NamedTuple

from zmlx.system import app_data, execute_once
from zmlx.ui.gui_buffer import gui

try:                                    # 统一 Qt 绑定（PyQt6 / PyQt5 皆可）
    from zmlx.ui.pyqt import QtCore, QtGui, QtWidgets
except Exception:                       # pragma: no cover - 无 Qt 环境
    QtCore = QtGui = QtWidgets = None

if QtCore is not None:                  # 无头 / 无绑定时保持模块可导入
    QElapsedTimer = QtCore.QElapsedTimer
    QEvent = QtCore.QEvent
    QPointF = QtCore.QPointF
    QRectF = QtCore.QRectF
    Qt = QtCore.Qt
    QTimer = QtCore.QTimer
    QUrl = QtCore.QUrl

    QBrush = QtGui.QBrush
    QColor = QtGui.QColor
    QFont = QtGui.QFont
    QFontMetrics = QtGui.QFontMetrics
    QIcon = QtGui.QIcon
    QKeyEvent = QtGui.QKeyEvent
    QLinearGradient = QtGui.QLinearGradient
    QMouseEvent = QtGui.QMouseEvent
    QPainter = QtGui.QPainter
    QPainterPath = QtGui.QPainterPath
    QPen = QtGui.QPen
    QPixmap = QtGui.QPixmap
    QRadialGradient = QtGui.QRadialGradient
    QApplication = QtWidgets.QApplication
    QWidget = QtWidgets.QWidget
else:                                   # pragma: no cover - 仅为名字齐全
    QElapsedTimer = QEvent = QPointF = QRectF = Qt = QTimer = QUrl = None
    QBrush = QColor = QFont = QFontMetrics = QIcon = QKeyEvent = None
    QLinearGradient = QMouseEvent = QPainter = QPainterPath = QPen = None
    QPixmap = QRadialGradient = QApplication = QWidget = None

try:                                    # 没有 QtMultimedia 时静默降级
    from zmlx.ui.pyqt import QtMultimedia

    QSoundEffect = None if QtMultimedia is None else QtMultimedia.QSoundEffect
    HAVE_SOUND = QSoundEffect is not None
except Exception:                       # pragma: no cover - 取决于安装
    QSoundEffect = None                 # type: ignore[assignment]
    HAVE_SOUND = False

def _data_dir(*parts: str) -> Path:
    """取一个**可写**的数据目录（app_data 下），避免往仓库里写文件。

    音效缓存与最高分存档都要落盘，而 zmlx 的安装目录不保证可写（也可能是
    只读的 site-packages），所以统一放到 ``app_data.root('tetris')`` 下。

    Args:
        *parts: 数据目录下的相对路径片段。

    Returns:
        拼好的 Path（不保证已存在）。
    """
    try:
        root = Path(app_data.root('tetris'))
    except Exception:                   # pragma: no cover - app_data 不可用时兜底
        root = Path(tempfile.gettempdir()) / 'zml_tetris'
    return root.joinpath(*parts)


SFX_DIR = _data_dir('sfx')


# =============================================================================
# 0. 记录（record.jsonl）—— 把"写盘"与"战绩"清楚地记下来
# =============================================================================
#  ⚠️ **为什么要记**：本模块只有**两处**会往磁盘写东西 —— ``save.json``（最高分 /
#  设置）与 ``sfx/*.wav``（音效缓存）。而存档是**明文 JSON、就在用户目录下**，实测
#  踩到过被手改成 ``high = 9999999`` 的情况（见 :func:`_max_plausible`）。真出了
#  问题，光看一个 ``save.json`` 是查不出"谁在什么时候按什么理由写坏了它"的。
#
#  所以这里把**每次写盘**与**每局结果**都追加成一行 JSON：事后对着时间线就能复盘
#  —— 写了几次、每次多大、由谁触发、成功与否；以及每一局的成绩明细（而不只是
#  ``save.json`` 里那四个被压扁的累计值）。
#
#  格式是 **JSONL**（一行一条 JSON）：既能直接肉眼看，也能 ``json.loads`` 逐行解析。
#  文件：``app_data.root('tetris', 'record.jsonl')``，与本模块的其它数据同处一地。
#  两类条目靠 ``kind`` 区分：
#
#    * ``kind="write"`` —— 一次写盘：``what`` / ``path`` / ``bytes`` / ``why`` / ``ok``
#    * ``kind="game"``  —— 一局结束：``score`` / ``lines`` / ``level`` / ``combo_max`` …
#
#  ⚠️ **记录绝不能反过来影响游戏**：本节每个函数都吞掉自己的异常（写不进去就算了，
#  大不了没有记录），且**写记录这件事本身不再产生记录** —— 否则每条记录都要再记
#  一条，无限递归。

#: 记录文件的大小上限；超过就整份轮转成 ``record.1.jsonl``（见 :func:`_rotate_record`）。
RECORD_MAX_BYTES = 512 * 1024


def record_path() -> Path:
    """记录文件位置（``app_data`` 下，与 ``save.json`` / ``sfx`` 同目录）。"""
    return _data_dir('record.jsonl')


def _rotate_record(path: Path) -> None:
    """记录文件超过 :data:`RECORD_MAX_BYTES` 时滚成 ``record.1.jsonl``（覆盖旧的）。

    ⚠️ 用"整份轮转"而不是"删掉最前面 N 行"：JSONL 是**追加**写的，要从头部删行就得
    每次重写整个文件；轮转则只在超限那一刻发生一次，且留下的仍是最近的一整段。
    """
    try:
        bak = path.with_name(path.stem + '.1' + path.suffix)
        if bak.exists():
            bak.unlink()
        path.replace(bak)
    except Exception:
        pass                    # 轮转失败无所谓：最坏是这个文件一直长下去


def record_event(kind: str, **fields) -> None:
    """追加一条记录到 ``record.jsonl``（任何 IO / 序列化异常都静默吞掉）。

    Args:
        kind: 条目类型，``"write"``（写盘审计）或 ``"game"``（战绩）。
        **fields: 该条目的字段，与 ``time`` / ``kind`` 一起写成一行 JSON。
    """
    item = {'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'kind': kind}
    item.update(fields)
    try:
        path = record_path()
        if path.exists() and path.stat().st_size > RECORD_MAX_BYTES:
            _rotate_record(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    except Exception:
        pass


def record_write(what: str, path, why: str, ok: bool = True, err: str = '') -> None:
    """记录一次**写磁盘**。

    Args:
        what: 写的是什么 —— ``"save"``（存档）或 ``"sfx"``（音效缓存）。
        path: 目标文件；条目里存**绝对路径**，便于拿着它直接去磁盘上核对。
        why: **为什么写**。这是排查问题时最有用的一列，各调用点必须传具体的来源
            （``"game_over"`` / ``"setting:sfx"`` / ``"close_tab"`` …），不要写成
            笼统的 ``"unknown"`` —— 那就等于没记。
        ok: 是否写成功。
        err: 失败时的异常摘要（``"类型: 说明"``），成功时留空。
    """
    path = Path(path)
    size = None
    if ok:                                  # 只有写成了，字节数才有意义
        try:
            size = path.stat().st_size      # 实际落盘字节数，比 len(text) 更可信
        except Exception:
            pass
    record_event('write', what=what, path=str(path), why=why, ok=bool(ok),
                 bytes=size, err=err)


def read_record(limit: int = 20, kind: str = '') -> list:
    """读最近的记录（**最新的在最后**），用于回看 / 排查。

    Args:
        limit: 最多返回多少条；传 0 或负数表示不限。
        kind: 只取某类条目（``"write"`` / ``"game"``）；空串表示两类都要。

    Returns:
        list[dict]: 条目列表。坏行（手改过、被截断）直接跳过，不抛异常。
    """
    try:
        lines = record_path().read_text(encoding='utf-8').splitlines()
    except Exception:
        return []                       # 还没写过记录 / 文件不可读
    out = []
    for line in lines:
        try:
            it = json.loads(line)
        except Exception:
            continue
        if isinstance(it, dict) and (not kind or it.get('kind') == kind):
            out.append(it)
    return out[-limit:] if limit and limit > 0 else out


# =============================================================================
# 1. 画布几何
# =============================================================================
#  设计分辨率固定，paintEvent 与鼠标换算共用 canvas_transform()（与 连连看.py 同一套方案），
#  窗口任意缩放/全屏都不会让版面漂移。

CELL = 30                       # 每格边长（设计像素）
FIELD_COLS = 10                 # 可见列数
FIELD_ROWS = 20                 # 可见行数
BUFFER_ROWS = 2                 # 场地顶部"出生区"行数（不可见区，方块从这里进来）
GRID_ROWS = FIELD_ROWS + BUFFER_ROWS

FIELD_W = FIELD_COLS * CELL     # 300
FIELD_H = FIELD_ROWS * CELL     # 600
FIELD_X = 200                   # 场地左边界
FIELD_Y = 114                   # 可见区上边界
FIELD_BOTTOM = FIELD_Y + FIELD_H
STRIP_TOP = FIELD_Y - BUFFER_ROWS * CELL        # 出生区顶 = 54

BASE_W = 700
BASE_H = 760

FRAME = QRectF(FIELD_X - 9, 45, FIELD_W + 18, 678)      # 场地外框（含出生区）
PANEL_L = QRectF(18, 45, 160, 678)                     # 左面板：Hold + 统计 + 键位
PANEL_R = QRectF(522, 45, 160, 678)                    # 右面板：Next + 等级进度
HEADER_BOTTOM = 45
FOOTER_TOP = 723

FPS = 60                        # 渲染帧率
LOGIC_STEP = 1.0 / 120.0        # 逻辑固定步长（与帧率解耦，掉帧也不会改变手感）
MAX_SUBSTEPS = 10               # 单帧最多补的逻辑步数（防止卡顿后"追帧"雪崩）

HOLD_BOX = QRectF(PANEL_L.x() + 12, 76, 136, 112)
NEXT_SLOT_H = 118               # Next 每个预览格高度
NEXT_BOX = QRectF(PANEL_R.x() + 12, 76, 136, 5 * NEXT_SLOT_H)
PREVIEW_CELL = 22               # Hold/Next 预览格边长
PROGRESS_BAR = QRectF(PANEL_R.x() + 12, 700, 136, 10)

class _Palette:
    """配色：深色（暗色街机风：石墨底 + 霓虹方块）与浅色两套，按语义角色取值。

    ⚠️ **为什么是"语义角色"而不是一堆色值常量**：整套界面原本硬编码了约 85 个色值
    （17 个具名常量 + 68 个内联字面量），而那 68 个里绝大多数只是某基色的
    ``lighter()`` / ``darker()`` / 带 alpha 的变体。与其把 85 个数抄成 170 个数，
    不如只定义**十几个角色**，其余交给 :meth:`edge` / :meth:`shade` 之类的派生 ——
    这样两套主题才可能保持一致的结构，也才可能有人愿意维护。

    ⚠️ **浅色主题不是把深色"取反"**：真正需要逐个人工定夺的是**极性反转**那几处
    （约 20 处）—— 深色下用来提亮的白色半透明叠层（``QColor(255,255,255,22)``），
    在浅色下必须变成压暗的黑色叠层，否则白叠白完全看不出来。这类一律走
    :meth:`edge`（名字就叫"描边/分隔线"），由它按当前主题决定用白还是用黑。

    方块颜色（``PIECE_COLORS``）**两套主题共用、绝不随主题改**：那是俄罗斯方块的
    通用语言，I 青 / J 蓝 / L 橙 / O 黄 / S 绿 / T 紫 / Z 红 一改玩家就认不出来了。
    浅色下只调整它们的高光与描边极性。
    """

    #: 角色 -> (深色值, 浅色值)。两套的键必须完全一致。
    COLORS = {
        # 窗口径向渐变的两端（信箱边也用它）
        'bg0': ((32, 36, 56), (232, 236, 245)),
        'bg1': ((9, 10, 16), (250, 251, 254)),
        # 顶栏 / 底栏
        'bar0': ((34, 39, 58), (244, 246, 251)),
        'bar1': ((17, 19, 28), (226, 230, 240)),
        'bar_line': ((70, 78, 104), (176, 184, 204)),
        # 面板卡
        'panel': ((23, 26, 37), (247, 248, 252)),
        'panel_hi': ((35, 39, 55), (255, 255, 255)),
        'panel_line': ((58, 65, 90), (194, 201, 220)),
        # 场地
        'field0': ((11, 13, 20), (238, 241, 248)),
        'field1': ((17, 20, 29), (231, 235, 245)),
        'field2': ((22, 25, 36), (245, 247, 252)),
        'slot': ((26, 29, 41), (232, 236, 246)),
        'slot_off': ((20, 23, 32), (238, 241, 249)),
        'frame0': ((31, 35, 50), (250, 251, 254)),
        'frame1': ((17, 20, 29), (226, 230, 240)),
        # 文字
        'txt': ((219, 225, 240), (28, 32, 44)),
        'dim': ((136, 145, 168), (88, 96, 116)),
        'faint': ((94, 102, 124), (134, 142, 162)),
        # 语义色
        'accent': ((86, 232, 255), (0, 150, 190)),
        'gold': ((255, 206, 84), (196, 132, 0)),
        'warn': ((255, 92, 92), (214, 40, 40)),
        'good': ((120, 235, 140), (22, 158, 66)),
        'dead': ((96, 100, 116), (150, 156, 170)),
        # 覆盖层蒙版与卡片
        'veil': ((4, 5, 10), (250, 251, 254)),
        'card0': ((40, 45, 65), (255, 255, 255)),
        'card1': ((19, 22, 32), (238, 241, 249)),
        'card_line': ((98, 108, 142), (168, 176, 198)),
        # 弹幕横幅底
        'banner': ((6, 8, 14), (18, 20, 28)),
    }

    #: 当前主题是否为深色（由 :func:`apply_theme` 维护）。
    dark = True

    @classmethod
    def use_dark(cls, dark: bool) -> None:
        """切换当前主题（深色 / 浅色）。"""
        cls.dark = bool(dark)

    @classmethod
    def _raw(cls, role: str) -> tuple:
        pair = cls.COLORS[role]
        return pair[0] if cls.dark else pair[1]

    @classmethod
    def c(cls, role: str, alpha: int = 255) -> QColor:
        """取一个角色对应的颜色；``alpha`` 给 0~255（默认不透明）。"""
        r, g, b = cls._raw(role)
        return QColor(r, g, b, alpha)

    @classmethod
    def edge(cls, alpha: int = 22) -> QColor:
        """半透明的「提亮/压暗」叠层 —— 深色主题下是白，浅色主题下是黑。

        ⚠️ 这是两套主题**唯一靠极性反转**的地方：深色下 `QColor(255,255,255,22)`
        画出来是一条淡淡的高光分隔线，浅色下同样一句会**完全看不见**（白叠白），
        必须换成黑色叠层。凡是「描边 / 分隔线 / 顶部反光 / 内阴影」都用它，
        不要直接写字面量。
        """
        return QColor(255, 255, 255, alpha) if cls.dark else QColor(0, 0, 0, alpha)

    @classmethod
    def shadow(cls, alpha: int = 90) -> QColor:
        """投影：两套主题都是黑，但深色下要更重才压得住。"""
        return QColor(0, 0, 0, alpha if cls.dark else int(alpha * 0.45))

    @classmethod
    def mix(cls, role: str, other: QColor, ratio: float) -> QColor:
        """把某个角色往 ``other`` 方向混 ``ratio``（0~1），用于派生相近色。"""
        base = cls.c(role)
        ratio = min(max(float(ratio), 0.0), 1.0)
        return QColor(round(base.red() * (1 - ratio) + other.red() * ratio),
                      round(base.green() * (1 - ratio) + other.green() * ratio),
                      round(base.blue() * (1 - ratio) + other.blue() * ratio),
                      base.alpha())


#: 主题模式：跟随系统 / 强制深色 / 强制浅色（F2 设置项，见 ``TetrisWidget.cycle_setting``）
THEME_MODES = ("跟随系统", "深色", "浅色")

# 便捷别名：模块内到处都在用，写成短名省得每处都敲 `_Palette.c(...)`。
# ⚠️ 它们是**函数**不是常量 —— 每次调用都按**当时**的主题取值，所以切换主题后
#    同一行代码自然就画出了新配色，不需要重建任何东西（缓存除外，见
#    ``TetrisWidget._reset_caches``）。
def COL(role: str, alpha: int = 255) -> QColor:
    """取语义色（等价于 :meth:`_Palette.c`，模块内的短名）。"""
    return _Palette.c(role, alpha)


def EDGE(alpha: int = 22) -> QColor:
    """取极性化的提亮/压暗叠层（等价于 :meth:`_Palette.edge`）。"""
    return _Palette.edge(alpha)


def SHADOW(alpha: int = 90) -> QColor:
    """取极性化的投影色（等价于 :meth:`_Palette.shadow`）。"""
    return _Palette.shadow(alpha)


#: 兼容旧名（原先是模块级 QColor 常量，现在是按主题取值的函数调用）。
#: ⚠️ 用法统一改成 `COL_TXT()` 这样**加括号调用**；不加括号拿到的是函数对象，
#: 画出来会是黑的且不报错 —— 迁移时最容易漏的一种。
COL_ACCENT = lambda: COL('accent')          # noqa: E731
COL_GOLD = lambda: COL('gold')              # noqa: E731
COL_WARN = lambda: COL('warn')              # noqa: E731
COL_GOOD = lambda: COL('good')              # noqa: E731
COL_DEAD = lambda: COL('dead')              # noqa: E731
COL_TXT = lambda: COL('txt')                # noqa: E731
COL_DIM = lambda: COL('dim')                # noqa: E731
COL_FAINT = lambda: COL('faint')            # noqa: E731
COL_PANEL = lambda: COL('panel')            # noqa: E731
COL_PANEL_HI = lambda: COL('panel_hi')      # noqa: E731
COL_PANEL_LINE = lambda: COL('panel_line')  # noqa: E731
COL_SLOT = lambda: COL('slot')              # noqa: E731
COL_BG0 = lambda: COL('bg0')                # noqa: E731
COL_BG1 = lambda: COL('bg1')                # noqa: E731

FONT_FAMILY = "Microsoft YaHei"
FONT_MONO = "Consolas"

# =============================================================================
# 2. 方块定义（SRS：出生朝向 + 踢墙表）
# =============================================================================

KINDS = "IJLOSTZ"
KIND_ID = {k: i + 1 for i, k in enumerate(KINDS)}       # 棋盘里存的数字 1..7
ID_KIND = {v: k for k, v in KIND_ID.items()}
DEAD_ID = 8                                             # 结算动画用的灰块

PIECE_COLORS = {
    "I": QColor(0, 226, 232),
    "J": QColor(72, 110, 255),
    "L": QColor(255, 156, 40),
    "O": QColor(255, 214, 56),
    "S": QColor(78, 214, 96),
    "T": QColor(186, 96, 255),
    "Z": QColor(255, 76, 88),
}


def dead_color() -> QColor:
    """结算动画里灰块的颜色（死块在浅色下要更深才看得出）。"""
    return COL('dead')

# 出生块：n = 包围盒边长，(x, y) 为盒内格坐标（y 向下）
SPAWN_BOX = {
    "I": (4, ((0, 1), (1, 1), (2, 1), (3, 1))),
    "J": (3, ((0, 0), (0, 1), (1, 1), (2, 1))),
    "L": (3, ((2, 0), (0, 1), (1, 1), (2, 1))),
    "O": (2, ((0, 0), (1, 0), (0, 1), (1, 1))),
    "S": (3, ((1, 0), (2, 0), (0, 1), (1, 1))),
    "T": (3, ((1, 0), (0, 1), (1, 1), (2, 1))),
    "Z": (3, ((0, 0), (1, 0), (1, 1), (2, 1))),
}
SPAWN_X = {"I": 3, "J": 3, "L": 3, "O": 4, "S": 3, "T": 3, "Z": 3}
SPAWN_Y = 0                     # 出生时贴在第 0 行（出生区内），可见区从第 BUFFER_ROWS 行开始


def _rotations() -> dict[str, tuple[tuple[tuple[int, int], ...], ...]]:
    """由出生朝向推出 4 个旋转态：盒内 (x, y) -> (n-1-y, x) 即顺时针 90°。"""
    out: dict[str, tuple[tuple[tuple[int, int], ...], ...]] = {}
    for kind in KINDS:
        n, cells = SPAWN_BOX[kind]
        states = [tuple(sorted(cells))]
        cur = list(cells)
        for _ in range(3):
            cur = [(n - 1 - y, x) for (x, y) in cur]
            states.append(tuple(sorted(cur)))
        out[kind] = tuple(states)
    return out


ROTATIONS = _rotations()

# SRS 踢墙表：写法沿用官方（y 轴向上为正），应用时取 (dx, -dy)
KICKS_JLSTZ = {
    (0, 1): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (1, 0): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
    (1, 2): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
    (2, 1): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (2, 3): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    (3, 2): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (3, 0): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (0, 3): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
}
KICKS_I = {
    (0, 1): ((0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)),
    (1, 0): ((0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)),
    (1, 2): ((0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)),
    (2, 1): ((0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)),
    (2, 3): ((0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)),
    (3, 2): ((0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)),
    (3, 0): ((0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)),
    (0, 3): ((0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)),
}
# 180° 旋转不是官方 SRS 的一部分，这里给一组温和的自定踢墙（够用且不会钻地）
KICKS_180 = ((0, 0), (0, 1), (0, -1), (1, 0), (-1, 0), (0, 2), (0, -2), (2, 0), (-2, 0))
KICKS_180_I = ((0, 0), (0, 1), (0, -1), (0, 2), (0, -2), (1, 0), (-1, 0), (2, 0), (-2, 0))


def kick_table(kind: str, frm: int, to: int):
    """返回该旋转对应的候选偏移序列（已转成屏幕坐标 y 向下）。"""
    if kind == "O":
        return ((0, 0),)
    if (frm - to) % 4 == 2:                       # 180°
        seq = KICKS_180_I if kind == "I" else KICKS_180
    else:
        table = KICKS_I if kind == "I" else KICKS_JLSTZ
        seq = table[(frm, to)]
    return tuple((dx, -dy) for (dx, dy) in seq)


# =============================================================================
# 3. 规则参数（Tetris Guideline）
# =============================================================================

LOCK_DELAY = 0.5                # 触底后锁定延迟（秒）
LOCK_RESET_MAX = 15             # 移动/旋转最多把锁定计时器推迟多少次
CLEAR_TIME = 0.34               # 消行冻结动画时长
LOCK_FLASH = 0.10               # 落地压扁闪光
SOFT_INTERVAL = 0.035           # 软降每格秒数（比任何等级的重力都快）
DAS_PRESETS = (("慢", 0.20, 0.060), ("中", 0.13, 0.033), ("快", 0.085, 0.0))
START_LEVELS = (1, 5, 10)
LINE_PER_LEVEL = 10
MAX_LEVEL = 20
SPAWN_GLOW = 0.35               # 新方块出现时的闪光时长

BASE_CLEAR = {1: 100, 2: 300, 3: 500, 4: 800}
TSPIN_BASE = {
    ("full", 0): 400, ("full", 1): 800, ("full", 2): 1200, ("full", 3): 1600,
    ("mini", 0): 100, ("mini", 1): 200, ("mini", 2): 400, ("mini", 3): 400,
}
PERFECT_BASE = {1: 800, 2: 1200, 3: 1800, 4: 2000}
B2B_MULT = 1.5
COMBO_UNIT = 50
SOFT_DROP_POINT = 1
HARD_DROP_POINT = 2

OVER_ROW_TIME = 0.055           # 结算动画每填满一行的时间
OVER_TIME = OVER_ROW_TIME * GRID_ROWS + 0.45


def gravity_interval(level: int) -> float:
    """官方重力曲线：(0.8 - (L-1)*0.007)^(L-1) 秒/格，直到 20 级都按原式（约 0.00046 s/格）。"""
    lvl = max(1, min(level, 99))
    return max((0.8 - (lvl - 1) * 0.007) ** (lvl - 1), 1.0 / 5000.0)


# =============================================================================
# 4. 音效：程序化合成 WAV + QSoundEffect（无素材依赖，与 claw_machine.py 同一思路）
# =============================================================================

SR = 22050
SFX_NAMES = ("move", "rotate", "lock", "harddrop", "hold", "clear1", "clear2", "clear3",
             "tetris", "tspin", "perfect", "levelup", "gameover", "pause", "go", "combo",
             "combo2", "combo3", "combo4", "bgm")
SFX_VERSION = "1"


def _env(i: int, n: int, a: float = 0.05, r: float = 0.55) -> float:
    """线性 attack + 二次 release 包络。"""
    if n <= 1:
        return 0.0
    t = i / (n - 1)
    at = max(a, 1e-6)
    if t < at:
        e = t / at
    elif t > 1.0 - r:
        k = (t - (1.0 - r)) / max(r, 1e-6)
        e = (1.0 - k) ** 2
    else:
        e = 1.0
    return max(0.0, min(1.0, e))


def _osc(n: int, freq: float, amp: float = 1.0, wave_kind: str = "sin",
         attack: float = 0.02, release: float = 0.6, phase: float = 0.0) -> array:
    out = array("h", bytes(2 * max(0, n)))
    w = 2.0 * math.pi * freq / SR
    for i in range(n):
        p = w * i + phase
        if wave_kind == "sin":
            s = math.sin(p)
        elif wave_kind == "tri":
            s = 2.0 / math.pi * math.asin(max(-1.0, min(1.0, math.sin(p))))
        elif wave_kind == "saw":
            s = 2.0 * ((freq * i / SR) % 1.0) - 1.0
        else:
            s = 1.0 if math.sin(p) >= 0 else -1.0
        out[i] = int(max(-1.0, min(1.0, s * amp * _env(i, n, attack, release))) * 32767)
    return out


def _sweep(n: int, f0: float, f1: float, amp: float = 1.0,
           attack: float = 0.02, release: float = 0.6) -> array:
    out = array("h", bytes(2 * max(0, n)))
    ph = 0.0
    for i in range(n):
        t = i / max(1, n - 1)
        f = f0 + (f1 - f0) * t
        ph += 2.0 * math.pi * f / SR
        out[i] = int(max(-1.0, min(1.0, math.sin(ph) * amp * _env(i, n, attack, release))) * 32767)
    return out


def _noise(n: int, amp: float = 1.0, attack: float = 0.01, release: float = 0.7,
           lp_alpha: float = 0.35, seed: int = 20260712) -> array:
    rnd = random.Random(seed)
    out = array("h", bytes(2 * max(0, n)))
    prev = 0.0
    for i in range(n):
        s = rnd.uniform(-1.0, 1.0)
        prev += lp_alpha * (s - prev)             # 一阶低通，去掉刺耳高频
        out[i] = int(max(-1.0, min(1.0, prev * amp * _env(i, n, attack, release))) * 32767)
    return out


def _mix(*tracks: array) -> array:
    n = max((len(t) for t in tracks), default=0)
    out = array("h", bytes(2 * n))
    for i in range(n):
        s = 0.0
        for t in tracks:
            if i < len(t):
                s += t[i]
        out[i] = int(max(-32767, min(32767, s)))
    return out


def _seq(*tracks: array) -> array:
    out = array("h")
    for t in tracks:
        out.extend(t)
    return out


def _ms(x: float) -> int:
    return int(SR * x / 1000.0)


def _write(path: Path, data: array) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


NOTE_HZ = {
    "A2": 110.00, "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.00,
    "A3": 220.00, "B3": 246.94, "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
    "G4": 392.00, "A4": 440.00, "B4": 493.88, "C5": 523.25, "D5": 587.33, "E5": 659.26,
    "F5": 698.46, "G5": 783.99, "A5": 880.00, "B5": 987.77, "C6": 1046.50,
}
# 《卖货郎》(Korobeiniki) A 段：俄罗斯民谣，公有领域，俄罗斯方块最经典的那段 BGM
# 每项 = (音名 或 None 休止, 八分音符数)
KOROBEINIKI = (
    ("E5", 2), ("B4", 1), ("C5", 1), ("D5", 2), ("C5", 1), ("B4", 1),
    ("A4", 2), ("A4", 1), ("C5", 1), ("E5", 2), ("D5", 1), ("C5", 1),
    ("B4", 3), ("C5", 1), ("D5", 2), ("E5", 2),
    ("C5", 2), ("A4", 2), ("A4", 2), (None, 2),
    ("D5", 3), ("F5", 1), ("A5", 2), ("G5", 1), ("F5", 1),
    ("E5", 3), ("C5", 1), ("E5", 2), ("D5", 1), ("C5", 1),
    ("B4", 2), ("B4", 1), ("C5", 1), ("D5", 2), ("E5", 2),
    ("C5", 2), ("A4", 2), ("A4", 2), (None, 2),
)
KORO_CHORDS = ("E3", "A3", "E3", "A3", "D3", "C3", "E3", "A3")
KORO_BEAT = 0.40                # 四分音符时长（≈150 BPM）


def _korobeiniki() -> array:
    """合成 BGM：主旋律(方波) + 低音(三角波) + 底鼓/沙锤，8 小节循环 ≈13 秒。"""
    eighth = KORO_BEAT / 2.0
    total = int(SR * eighth * sum(d for _, d in KOROBEINIKI))
    mel = array("h", bytes(2 * total))
    at = 0
    for name, dur in KOROBEINIKI:
        n = int(SR * eighth * dur)
        if name:
            piece = _osc(n, NOTE_HZ[name], 0.34, "square", 0.006, 0.55)
            mel[at:at + n] = piece
        at += n

    bass = array("h", bytes(2 * total))
    bar = int(SR * KORO_BEAT * 4)
    for b, root in enumerate(KORO_CHORDS):
        f = NOTE_HZ[root]
        for q in range(4):                      # 每小节 4 个四分音符
            n = int(SR * KORO_BEAT)
            amp = 0.30 if q % 2 == 0 else 0.22
            piece = _osc(n, f * (2.0 if q == 3 else 1.0), amp, "tri", 0.01, 0.5)
            s = b * bar + q * n
            if s + n <= total:
                bass[s:s + n] = piece

    drums = array("h", bytes(2 * total))
    for k in range(0, total, int(SR * eighth)):         # 八分音符沙锤
        n = _ms(28)
        h = _noise(n, 0.055, 0.002, 0.8, 0.65, seed=1000 + k)
        drums[k:k + len(h)] = h
    for b in range(len(KORO_CHORDS)):                    # 每小节 1、3 拍底鼓
        for q in (0, 2):
            s = b * bar + q * int(SR * KORO_BEAT)
            kick = _sweep(_ms(90), 150, 55, 0.34, 0.002, 0.7)
            drums[s:s + len(kick)] = _mix(drums[s:s + len(kick)], kick)
    return _mix(mel, bass, drums)


def build_sounds(folder: Path) -> None:
    """首次运行合成全部音效（约 2 秒），之后直接复用缓存。"""
    ver = folder / ".version"
    if ver.exists() and all((folder / f"{n}.wav").exists() for n in SFX_NAMES):
        try:
            if ver.read_text(encoding="utf-8").strip() == SFX_VERSION:
                return
        except Exception:
            pass                    # 版本文件坏了就重合成，别让整局游戏没声音
    folder.mkdir(parents=True, exist_ok=True)
    print(f"首次运行：正在合成音效到 {folder} …")
    S: dict[str, array] = {}

    S["move"] = _mix(_osc(_ms(26), 300, 0.30, "square", 0.004, 0.7),
                     _osc(_ms(20), 600, 0.12, "sin", 0.004, 0.7))
    S["rotate"] = _seq(_osc(_ms(24), 660, 0.26, "tri", 0.004, 0.5),
                       _osc(_ms(30), 990, 0.20, "sin", 0.004, 0.6))
    S["lock"] = _mix(_sweep(_ms(80), 240, 110, 0.42, 0.003, 0.75),
                     _noise(_ms(50), 0.20, 0.002, 0.85, 0.10))
    S["harddrop"] = _mix(_sweep(_ms(150), 620, 130, 0.46, 0.002, 0.7),
                         _noise(_ms(120), 0.30, 0.002, 0.9, 0.08),
                         _osc(_ms(120), 90, 0.30, "tri", 0.003, 0.8))
    S["hold"] = _seq(_osc(_ms(45), 520, 0.24, "tri", 0.005, 0.4),
                     _osc(_ms(70), 780, 0.26, "sin", 0.005, 0.6))
    S["clear1"] = _seq(_osc(_ms(70), 880, 0.26, "tri", 0.004, 0.35),
                       _osc(_ms(150), 1320, 0.24, "sin", 0.004, 0.6))
    S["clear2"] = _seq(_osc(_ms(65), 880, 0.26, "tri", 0.004, 0.3),
                       _osc(_ms(65), 1174, 0.26, "tri", 0.004, 0.3),
                       _osc(_ms(160), 1568, 0.24, "sin", 0.004, 0.6))
    S["clear3"] = _seq(_osc(_ms(60), 880, 0.26, "tri", 0.004, 0.28),
                       _osc(_ms(60), 1108, 0.26, "tri", 0.004, 0.28),
                       _osc(_ms(60), 1320, 0.26, "tri", 0.004, 0.28),
                       _osc(_ms(180), 1760, 0.24, "sin", 0.004, 0.6))
    S["tetris"] = _seq(*[_osc(_ms(80), f, 0.28, "square", 0.004, 0.3)
                         for f in (659, 880, 1108, 1320)],
                       _osc(_ms(300), 1760, 0.26, "sin", 0.004, 0.75))
    S["tspin"] = _mix(_sweep(_ms(220), 320, 1500, 0.24, 0.01, 0.6),
                      _seq(_osc(_ms(70), 1244, 0.24, "tri", 0.004, 0.3),
                           _osc(_ms(200), 1864, 0.24, "sin", 0.004, 0.7)))
    S["perfect"] = _seq(*[_osc(_ms(95), f, 0.26, "saw", 0.006, 0.3)
                          for f in (523, 659, 784, 1046, 1318, 1568)],
                        _osc(_ms(400), 1568, 0.24, "sin", 0.006, 0.8))
    S["levelup"] = _seq(*[_osc(_ms(90), f, 0.26, "tri", 0.005, 0.35)
                          for f in (523, 659, 784, 1046)],
                        _osc(_ms(220), 1318, 0.22, "sin", 0.005, 0.7))
    S["gameover"] = _seq(*[_osc(_ms(180), f, 0.26, "tri", 0.01, 0.4)
                           for f in (523, 440, 349, 294)],
                         _osc(_ms(520), 220, 0.24, "sin", 0.01, 0.85))
    S["pause"] = _seq(_osc(_ms(70), 660, 0.22, "tri", 0.005, 0.4),
                      _osc(_ms(110), 440, 0.22, "sin", 0.005, 0.6))
    S["go"] = _seq(_osc(_ms(60), 784, 0.26, "tri", 0.004, 0.3),
                   _osc(_ms(160), 1174, 0.24, "sin", 0.004, 0.6))
    for i, f in enumerate((700, 830, 980, 1170)):
        S["combo" if i == 0 else f"combo{i + 1}"] = _seq(
            _osc(_ms(55), f, 0.24, "tri", 0.004, 0.3),
            _osc(_ms(130), f * 1.5, 0.26, "sin", 0.004, 0.6))
    S["bgm"] = _korobeiniki()

    for name, data in S.items():
        wav = folder / f"{name}.wav"
        _write(wav, data)
        record_write('sfx', wav, why='build_sounds')       # 合成音效是写盘，记一笔
    ver_path = folder / ".version"
    ver_path.write_text(SFX_VERSION, encoding="utf-8")
    record_write('sfx', ver_path, why='build_sounds')


class Audio:
    """封装 QSoundEffect；无 QtMultimedia 时全部退化成空操作。"""

    def __init__(self) -> None:
        self.enabled = HAVE_SOUND
        self.sfx_on = True
        self.music_on = True
        self.players: dict[str, list] = {}
        self._rr: dict[str, int] = {}
        if not self.enabled:
            return
        try:
            build_sounds(SFX_DIR)
            for wav in sorted(SFX_DIR.glob("*.wav")):
                voices = 3 if wav.stem in ("move", "rotate", "lock", "combo") else 1
                lst = []
                for _ in range(voices):
                    eff = QSoundEffect()
                    eff.setSource(QUrl.fromLocalFile(str(wav)))
                    lst.append(eff)
                self.players[wav.stem] = lst
            for eff in self.players.get("bgm", []):
                eff.setVolume(0.16)
                eff.setLoopCount(-2)          # QSoundEffect.Infinite == -2
            self.set_music(self.music_on)
        except Exception:
            self.enabled = False

    def play(self, name: str, volume: float = 1.0) -> None:
        if not self.enabled or not self.sfx_on or name == "bgm":
            return
        lst = self.players.get(name)
        if not lst:
            return
        i = self._rr.get(name, 0) % len(lst)
        self._rr[name] = (i + 1) % len(lst)
        eff = lst[i]
        try:
            eff.setVolume(max(0.0, min(1.0, volume)))
            eff.stop()
            eff.play()
        except RuntimeError:
            # 底层的 QSoundEffect 已经被销毁（见 set_music 的说明），整体退化成静音
            self.enabled = False

    def set_sfx(self, on: bool) -> None:
        self.sfx_on = bool(on)
        if not on and self.enabled:
            for name, lst in self.players.items():
                if name != 'bgm':
                    for eff in lst:
                        try:
                            eff.stop()
                        except RuntimeError:
                            pass

    def set_music(self, on: bool) -> None:
        """开关背景音乐.

        ⚠️ 每处调用都套了 ``RuntimeError``：``QSoundEffect`` 是 C++ 对象，控件
        销毁（关标签页）后 Python 侧的包装还在，一碰就抛
        ``wrapped C/C++ object ... has been deleted``。而 ``set_music`` 会在
        **焦点变化 / 暂停 / 隐藏**这些"控件还活着但音频可能已经没了"的时机被调到，
        ``focusOutEvent`` 里更是在事件处理的收尾阶段 —— 那里抛异常会直接冒到
        Qt 事件循环外。所以这里一律按"没声音了"处理，绝不让它抛出去。
        """
        self.music_on = bool(on)
        if not self.enabled:
            return
        for eff in self.players.get('bgm', []):
            try:
                if on:
                    eff.play()
                else:
                    eff.stop()
            except RuntimeError:
                self.enabled = False


# =============================================================================
# 5. 方块贴图：按 (类型, 尺寸, 样式, 缩放) 缓存，避免每帧画渐变
# =============================================================================

_PM_CACHE: dict[tuple, QPixmap] = {}
_PM_LIMIT = 600


def clear_pixmap_cache() -> None:
    _PM_CACHE.clear()


def block_pixmap(kind: str, size: float, mode: str = "solid", scale: float = 1.0) -> QPixmap:
    """生成一块方块的贴图。

    贴图按物理像素生成（scale = 画布缩放 × devicePixelRatio），并把 devicePixelRatio
    设成 px/size —— 这样 draw_pm() 直接按逻辑坐标贴上去就是 1:1 的设备像素拷贝，
    省掉每帧 200 次的平滑缩放（实测整帧从 ~10ms 降到 ~4ms）。
    """
    q = max(0.5, scale)
    px = max(4, int(round(size * q)))
    key = (kind, px, mode)
    hit = _PM_CACHE.get(key)
    if hit is not None:
        return hit
    if len(_PM_CACHE) > _PM_LIMIT:
        _PM_CACHE.clear()

    pm = QPixmap(px, px)
    pm.fill(Qt.GlobalColor.transparent)
    pr = QPainter(pm)
    pr.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    u = px / float(size)                       # 设计像素 -> 贴图像素
    rect = QRectF(0.5 * u, 0.5 * u, px - 1.0 * u, px - 1.0 * u)
    r = max(2.0, 5.0 * u)

    if kind == "dead":
        col = dead_color()
    else:
        col = QColor(PIECE_COLORS.get(kind, COL('dead')))

    if mode == "ghost":
        fill = QColor(col)
        fill.setAlpha(56)
        pr.setPen(Qt.PenStyle.NoPen)
        pr.setBrush(fill)
        pr.drawRoundedRect(rect, r, r)
        edge = QColor(col)
        edge.setAlpha(200)
        pen = QPen(edge, max(1.0, 1.6 * u))
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setDashPattern([2.4, 1.8])
        pr.setPen(pen)
        pr.setBrush(Qt.BrushStyle.NoBrush)
        pr.drawRoundedRect(rect, r, r)
        pr.end()
        pm.setDevicePixelRatio(px / float(size))
        _PM_CACHE[key] = pm
        return pm

    if mode == "flash":
        base = QColor(255, 255, 255)
        lo = QColor(col).lighter(160)
    elif mode == "dead":
        base = QColor(col).lighter(112)
        lo = QColor(col).darker(150)
    else:
        base = QColor(col).lighter(126)
        lo = QColor(col).darker(168)

    g = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    g.setColorAt(0.0, base)
    g.setColorAt(1.0, lo)
    pr.setPen(Qt.PenStyle.NoPen)
    pr.setBrush(QBrush(g))
    pr.drawRoundedRect(rect, r, r)

    if mode != "flash":
        # 左上高光斜面 + 右下暗面，做出塑料块的立体感
        bevel = max(1.0, 2.2 * u)
        hi = QColor(255, 255, 255, 96)
        pr.setBrush(hi)
        top = QPainterPath()
        top.moveTo(rect.left() + r * 0.6, rect.top() + bevel * 0.5)
        top.lineTo(rect.right() - r * 0.6, rect.top() + bevel * 0.5)
        top.lineTo(rect.right() - r * 1.1, rect.top() + bevel * 1.9)
        top.lineTo(rect.left() + r * 1.1, rect.top() + bevel * 1.9)
        top.closeSubpath()
        pr.drawPath(top)
        pr.setBrush(QColor(0, 0, 0, 70))
        bot = QPainterPath()
        bot.moveTo(rect.left() + r * 0.5, rect.bottom() - bevel * 0.6)
        bot.lineTo(rect.right() - r * 0.5, rect.bottom() - bevel * 0.6)
        bot.lineTo(rect.right() - r * 1.0, rect.bottom() - bevel * 2.0)
        bot.lineTo(rect.left() + r * 1.0, rect.bottom() - bevel * 2.0)
        bot.closeSubpath()
        pr.drawPath(bot)

        # 顶部玻璃反光
        gloss = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.top() + rect.height() * 0.52))
        gloss.setColorAt(0.0, QColor(255, 255, 255, 92))
        gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
        pr.setBrush(QBrush(gloss))
        gl = QPainterPath()
        gl.addRoundedRect(QRectF(rect.left() + r * 0.55, rect.top() + bevel * 0.7,
                                 rect.width() - r * 1.1, rect.height() * 0.30), r * 0.5, r * 0.5)
        pr.drawPath(gl)
        # 一角高光点
        pr.setBrush(QColor(255, 255, 255, 120))
        pr.drawEllipse(QPointF(rect.left() + rect.width() * 0.26, rect.top() + rect.height() * 0.16),
                       max(0.8, 1.5 * u), max(0.8, 1.5 * u))

    pr.setBrush(Qt.BrushStyle.NoBrush)
    # ⚠️ 方块外描边**两套主题都用黑**：它压在方块自身的颜色上（不是压在背景上），
    #    而方块颜色两套主题共用、亮度都够高，黑描边在浅色主题下同样成立。
    pr.setPen(QPen(QColor(0, 0, 0, 120), max(1.0, 1.2 * u)))
    pr.drawRoundedRect(rect, r, r)
    pr.end()
    pm.setDevicePixelRatio(px / float(size))
    _PM_CACHE[key] = pm
    return pm


# =============================================================================
# 5b. 彩蛋：螺螺的头像
# =============================================================================

#: 头像数据：123×123 JPEG 字节的 base64。
#:
#: ⚠️ **头像就内置在这里，``luoluo.jpg`` 这个文件已经删除**。原先头像与
#: ``tetris.py`` 同目录、运行时用 ``QPixmap(路径)`` 读盘；后来把这张图内联了进来：
#: 彩蛋本该"整个模块自成一体"，而一个仅 4 KB 的素材单独占一个文件，反而要多操心
#: 它会不会随发行包一起被漏掉（见 ``pyproject.toml`` 的 ``package-data``）。
#: 内联之后，头像与代码**永不脱节**。
#:
#: ⚠️ 这里存的是**已经按短边居中裁好的正方形**，所以 :func:`luoluo_source` 拿到的
#: 就是方的，:func:`luoluo_pixmap` 里那次裁切退化成兜底（仍保留，见那里的说明）。
#: 原图竖版 123×133，裁掉后有效像素本来也只有 123×123；而格子最多画到
#: ``(CELL-2) × devicePixelRatio`` 个物理像素，123×123 早已过剩。编码取
#: ``quality=85, optimize=True``（3852 字节 → base64 5136 字符），在既有的圆形
#: 裁剪与缩放之后，与原图**看不出差别**。
LUOLUO_B64 = (
    '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8LCwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh'
    '0dHx8fExciJCIeJBweHx7/2wBDAQUFBQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4e'
    'Hh4eHh4eHh4eHh7/wAARCAB7AHsDASIAAhEBAxEB/8QAHAAAAgIDAQEAAAAAAAAAAAAABQYEBwACAwEI/8QAOhAAAQMDAwIEBQ'
    'IDBgcAAAAAAQIDBAAFEQYSITFBBxMiURQyYXGRFbFCgdEII1JTocEzRWKSosLh/8QAGgEAAgMBAQAAAAAAAAAAAAAAAgUBAwQA'
    'Bv/EACMRAAICAQUAAgMBAAAAAAAAAAABAgMRBBITITEiQQUUI1H/2gAMAwEAAhEDEQA/ALn2HueK9IHua5hfueK9JTg80w2owZ'
    'Z7xW2elcsp96zcBzmu2ok7ZNZk+9cg5n2qLcbpFgI3ynENI91K61DwjsE7cQfmNYt4gfNxSPePEC0xmnlNLQ6WuDhwdT0pWl+L'
    'TCTtRHQrPT1f/aHMSdrLdMopwQelbC4uDjBqomfFuAlI82IsHvg0fs/iNp+4kIDqmlH/ABGuzELDH79QX3zis+PPsaAWy8wLkV'
    'CLISoJ+vJNT+Qoer69KJJMjDCH6o2FAK4NSGriAOOn1pMvq5cZHxLad3q/lUpNxDNtRJfygYySaCUox9JwxgamsruwOdpCcH7U'
    'XElnHzj81VEvU8VyU6qGtIcQnoo4yO9REa5KUBLjK9467VcVjeupTxkPDLC31hWMHmopd47Vr5hpkUkorHvWvmfUVFKz260N1T'
    'dGbNYX7g6QQlB2p9yBUfWTksvAL8Q9dx9ORwzHCXZjgwAeQj2ziqPu2oL7qF91UmS5tKuEk8JH0rncJcu/3ZbzpXl1Wck9u1Go'
    'lmcRBz5YK+n3rFbckMaaOssVJMd9AKXHd6VfMT1JqIAhteFYJ7HNMd6sc7ygAkpCumOtQYek5bhCihZ57iqOcuWnyCt+1RKRuJ'
    '967JKUAOBRSsjsaLuaantnCUHH2qJIsM5OVKQQByce1Fzon9ZkixajmWiWh1t1QAUDtycHnNXhp7XLV2tqSyhSpATtx1GaohFr'
    'U/E3BPynBzU7Stzl6fuzDiVkNJWNyexGeasjaUTqPoS3TZz6S29B8xKueaQtc3uf8Wu3rR5SOdoqyLROYmQWpiDkONgj+lKuqb'
    'vpVFzW7cUNKeS2QAD6gcUGpr5azJ94KflMXWZc0RXW3GnEA7nE5AKT0qzLZoOKbewXLkorKBnI71tfwxdEW+VZEpeRJCkJAGFc'
    'DuahJtmoEJCfignHbf0pZHTVx+LQa7LES4TXQLyKiJUMV2bOTj616UzIkJ6g1XPjXJUIMeOFHYSSU1Y7QA5Paqs8dnm25MVlJy'
    'Qgk596oubUS2iOZiPpVkOSkDYO9WTCYT5SU7R04pE0Y2SfMI6DineO9hKcnGKSXzeT0FdS2BVm3tO7S4gKwQfxRWPEYSk/3SPx'
    'QONcEoPKuhqX+qtY9KuTVG9l0YJE9yBFWDlpP4qC/YY7p9LScGsTch1OPzW4uIIzuOajkZO1ACbpkR23ENJBCjmq31QwYkxKFj'
    'aCsA/bNXV8Ykp5Gc+9Vp4sxg7A89ACVBXarYWyKbK4j14X3hluysQ5e5QzhLqRwM9MmufiFpCzOTWbuX/LbcUAokZzzQXwFfU7'
    'Z5cV8haAQSlX0o74hRpCkw3Y7pDDbyVFnOcgK5pvDuvDEV6xLojsNvRZ9otjSEpgNOlSXUnB5qZdI0lM95LMYLbz6VHPPH3oZf'
    '7nbXJ8KVELq1MuJ34GEpHFNnx7KgCh9oJxxk81VxwmVJtekpjBI+9EWGkqGe9BEPBPSpsKUVKINMysJlrPAP0qhvGeb8Xqp5hB'
    'BDaQBirtek7W1HJ4FUBqotz7y9Ia3nDpCifel+sswsG3Rw3S6DejoihbkqweRRt0FvhRwKkaZjhu1tJ2n5c1xvr0ZjPmOJSMcg'
    'nFJpy3D6HUcMgOushfMgfbPWuwJUkKCgR2pRnXKzOvlCJ7aJG7hIVRW1KWQAl7emo2v/DtyDQWodFc/etkPvg8Ghkx8sIyM5xQ'
    '1y4z948tCdpPU0KTZI4NSnVNZVxzjigGtyhy1YWSec5NTrO866kIWk56momt2tljW4vPCsCih0Vz78D39n5hg2SWp4IJLnFN+q'
    'WkvRm48doJU4tQKiewpD8GyWLRIKQSCrIB7imZy4B+7RmFZSMLUQrsab1t7BFev6YFCSJsi3Nl1LUeN5wbKehVtV1+9FEQIxQD'
    '5q/+6od+g/EQbm22VKLUlGwj+EE8miVs0teFwGVeZnKRVareXgBrI2oi5PNdYrQQs5rZLnBwa0SVbiaa5KEjo9tUCjpkYqk9Qs'
    'O2vUL0RLAWh1zO49gTV0EZWPvSrrKwx3ZRkuEhWBsII60u10W4ZQx/H27LGe2f1QmUJGCUdvtWXizQZUZXxcFT6ikg469MVxtb'
    'xYSkL3YSNqSlOf8Aej8eUy40A6sFI65pN94HXvhTsnw4s6718fHi3Bp7cCEEp2/tT1YdMBhpBBAPTaeTRi53SIwCAhGSfSAACa'
    'kWKUgq8x9SWQcYBPWiUpv7A40AL7YHCkjO3jqBVVu6Q1Oq/KcN5SmKFZA37QPpg1fN5kNFveBuR32ntQpESBM3LWlCQo42kZqV'
    'Pb6TsQvabsF6gBHxcpiQgjIUhWePrWviWB+gJaBAJWPxTxHjRYjG1CvTjpVa62+IuN7jW2OklJJJV2z2FDHtkbWMvhMhxzTTbi'
    'GSkJJGSPmqfI8xd/G5hScJwnA6mn/SVti2nT0SE22hWwc5HOSKg3pUBE98rKELaGUE8c03h1WJLk+RsprU+pJVu1HMhqbCESNp'
    'AH0q0LRcnFWyMpC/SWwRk1V3iLBtn9xOTOD0pbhQvA4SCcCm622CX+nx/LvkcILacAq+lArMMrwMUeQFKAOKJxUBaSR3pabcCG'
    'xISsKYPRfQUfgXGEwwFOPp5GaZOSRQeOZCyOmDUt1MN2MkSWkudDyM9K2jw/jmvPaWME5FF49ujeQEOKTvxVU9slhhw3Q7RX+s'
    'W47KGJDDCWkKBBCEgDPbpSo9cHEJJSo8DtVu36xsXCyOx0HC0g7PvjiqVuSFxZC2XBhaFFJGKTaytQllDrQ3b4YfpydkomT0+c'
    'oq9h7GvbnDmKfQuNNcwOiM8Cgd4gS5GVRJy4iz3QORQDGsYK1BMhEzsCrOf3qmtbjYPlvZubLay9OdVu6JPIrvbro9GdU2pwnH'
    'PNIcN3WrhIcfaabJ9SeSSPzRyzokb8PqJX3JobFglIf410XIbCOSVcCjdosjjUwqlQ/+GsK3H8ihPh7aHLndGkKyGmyFKXjAyD'
    'nFPd/eMU/CvEFo5y4DjqMVdp6F02ZNRquL4oAMaokTrwYVsAcWlz146JPtS3r6Q0ua4i4zFMynCEgIHHNPtisNqitGXGZEdxR3'
    'FQPK/qapvxJv7Bv8qIvHoV8wHNbbZJLCFbkm8s8u3wydMXKLJcDvGWXcc5xxSQiPclISpF4dSkjgAnAryVcHpymmA+Woi1gKPt'
    'z1ounLKQ02WXEJGAo9TVIA82HSuuEqZtd+bWLUgb1ug/IO5q3ND6F0tIgfFSZUqQlDm1KUoz09+taeId0CdJyEtrKMjPB6dqn+'
    'DiJ87RSHI0+O2hMhwYUhSiecc80w075q978Cur4pYG9ETT8SOliPGktISMYTHWD/AKigt2dtEYKci+Y8oDPlqG059uaMqtd1/i'
    'uUZP0+GI/9qgahslykQSkSoiygbxhvCiR05JNHgjoBtz23re45Giuhac5JTkA/mqV1/PYdvTy0gJQo9enP1q53JaoluTG86HHc'
    'TypKW8lX35qsteaXhXNp6SxOSX3Dkt+Xxn6AEkVEqo2Rww658b6EmC8y9lLbyFY6gEcVvIt/muBaZAT7AppDv9lu9olqXFTJbK'
    'TnclKsY/FR2dT6lbbCF7XADj1JOfxmltui2eG+vWr7LLYi/DJ9biVdc57VxjoL0hfkpJI59Izmk+2P3y7LR5ilJTuGQkEDFWdo'
    'i3yIS0KxzkHnmsUoNemxW8hJsaNYoiOItcBwIX36fzrJFm1rJOy5xpqWlHrjcn78dKs223JbaEhSD0+YCul01BDislQU4XCcAF'
    'RGfv2rfp1FxwKdRU3LLZT2uvEBVitren4ii9MaAyUqyofQ+1U/eruuZPW8+wQ47yrJ619W23SWmdXrdm6mthKifQGW9jhHvuHW'
    'uV18BvDq5OFxgXmMsDCQE7gDWh15Mx8kIuCmn2V7PS2oKCSnjg0/QLfFnw2piglJdTuIBxirJ1F/ZtLag7YLyhzuGZDRQo/TuK'
    'UXfBLxPjuKZZihTaThJS5xig2HDtra4l+zPMbxhTZH4ol4JXG4mwLjMT1R20SCCEt7/mGc9fpSVqNavgXfUeh/Y1r4aSH0vzWk'
    'POJR5qPSlRH8B9qjRXtVuJs1kf6I+g2xc1JJ/WVk46mMBUd1MsHL16kqP/Q2hP8AtQzTduiPxyp5Lizju8v+tH2NN2V4jzYW77'
    'ur/rWrLMZpbpkKPlK5DbjijjLm3dn+Q/2ry5XeOk4U28sDr5bRUK3maasbPCLc1j2USr9zW8Cy2pLiUogMIB/wp2/tUxbOFq53'
    'C0voKH4jm0/5rRA/akW9aG0ZeHFux3UW6Qr+JB4J/mKvGdb4jbZQlo7U9AVk/uaBPRIi3ClcVhYIVnc2D+9Wb8HYKDkaB1NbH9'
    '9qfiT2grcPWASPtnmpcJesobgQ7p8qPA3ISSP3q4W7HaXG1KVBazuxlOR+1Q22G485LTIUlAUON5Pf70OapexJ+UfGKNrja5uX'
    'pbszkcEY3KOAPr14pqsnh5M+Jan3i6QypKc+QolQH3OQDTdGWtLBCVqAA4GakNErUFK6+44qZShFdRCy5GMsw2w2h++MJ2jany'
    'kpGB+TU9lqzn0m8rUfYOJGf/GhkiQ8ngLPPXPNRlJQ+AHm21g9QpANVADIIlrH/MZR7gBfH+gAqUIkUDCLpKCew3p/pSg3a7es'
    'KzDZH1Snaf8ASoz0GMHVAIWBn/MV/Wirin6cf//Z'
)

#: 一次落块被标成"螺螺"的概率。
LUOLUO_RATE = 0.3

#: 头像的原图与缩放后的贴图缓存。
#:
#: ⚠️ **必须缓存**：头像要按格子尺寸重绘，而一帧最多画 4 个格子、每秒 60 帧 ——
#: 每帧现做一次 ``scaled()`` 会白白吃掉渲染预算（本项目对帧率敏感，见
#: :func:`block_pixmap` 的说明）。键里带 ``px``，缩放/换屏时会各自留一份。
_LUOLUO_SRC: list = [None]          # [QPixmap | False]，False = 已确认解码失败
_LUOLUO_CACHE: dict[int, QPixmap] = {}


def luoluo_source():
    """取头像原图（只解码一次，之后一直复用）。

    Returns:
        QPixmap: 头像原图（正方形）；解码失败时返回 ``None``。

    ⚠️ 数据来自模块内联的 :data:`LUOLUO_B64`，**不再读磁盘** —— 于是也没有了
    "文件被删掉 / 发行包漏带"这类失败模式。

    ⚠️ 失败结果也会被记住（存成 ``False``）：否则每帧都会去重试解码同一份坏数据。
    失败时游戏照常跑（方块退回成普通配色），只是没有头像。
    """
    cached = _LUOLUO_SRC[0]
    if cached is False:
        return None
    if cached is not None:
        return cached
    try:
        pm = QPixmap()
        if not pm.loadFromData(base64.b64decode(LUOLUO_B64), 'JPG') or pm.isNull():
            raise ValueError('cannot decode the embedded image')
    except Exception as err:
        print(f'螺螺的头像解码失败（LUOLUO_B64）：{err}')
        _LUOLUO_SRC[0] = False
        return None
    _LUOLUO_SRC[0] = pm
    return pm


def luoluo_pixmap(size: float, scale: float = 1.0) -> QPixmap:
    """把头像裁成正方形并缩放成一块方块的尺寸（带缓存）。

    头像原图是竖长方形（人像照），直接塞进方块会变形，所以按**短边居中裁成正方形**
    再缩放 —— 保住脸不变形（人像大致居中，裁掉的是两侧背景）。

    ⚠️ 内置的 :data:`LUOLUO_B64` 存的**已经是裁好的正方形**，所以下面那次裁切
    实际上不再改变任何像素。保留它是为了兜底：万一以后换一张非正方形的内置图，
    这里仍然会自动裁正，不必再想一遍这件事。

    Args:
        size: 目标逻辑边长（设计像素），通常传 ``CELL - 2``。
        scale: 画布缩放 × devicePixelRatio（与 :func:`block_pixmap` 一致）。

    Returns:
        QPixmap: 圆形裁剪的头像；没有头像时返回 ``None``。
    """
    src = luoluo_source()
    if src is None:
        return None
    px = max(4, int(round(size * max(0.5, scale))))
    hit = _LUOLUO_CACHE.get(px)
    if hit is not None:
        return hit

    w, h = src.width(), src.height()
    side = min(w, h)                      # 内置数据已是正方形，这里等价于原样取用
    cut = src.copy((w - side) // 2, (h - side) // 2, side, side)

    out = QPixmap(px, px)
    out.fill(Qt.GlobalColor.transparent)
    pr = QPainter(out)
    pr.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pr.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    # 圆形裁剪：与方块的圆角矩形配在一起，看着像一枚头像贴纸
    path = QPainterPath()
    path.addEllipse(QRectF(0.0, 0.0, px, px))
    pr.setClipPath(path)
    pr.drawPixmap(QRectF(0.0, 0.0, px, px), cut,
                  QRectF(0.0, 0.0, float(side), float(side)))
    pr.end()
    out.setDevicePixelRatio(px / float(size))
    _LUOLUO_CACHE[px] = out
    return out


def clear_luoluo_cache() -> None:
    """清掉头像贴图缓存（缩放变化时由控件调用）。"""
    _LUOLUO_CACHE.clear()


# =============================================================================
# 6. 文本条目：绘制与"版面体检"共用同一份数据，避免两边写法漂移
# =============================================================================

class Txt(NamedTuple):
    name: str
    x: float
    y: float                 # 基线 y
    font: QFont
    text: str
    color: QColor
    align: str = "left"      # left | right | center
    shadow: bool = False     # 是否带 1px 深色描边（体检时按无描边算，留 2px 余量）


def place_text(item: Txt) -> tuple[float, float]:
    if item.align == "left":
        return item.x, item.y
    w = QFontMetrics(item.font).horizontalAdvance(item.text)
    if item.align == "right":
        return item.x - w, item.y
    return item.x - w / 2.0, item.y


def ink_rect(item: Txt) -> QRectF:
    """文字"实际着墨"矩形（tightBoundingRect 相对基线，y 向上为负）。"""
    r = QRectF(QFontMetrics(item.font).tightBoundingRect(item.text))
    x, y = place_text(item)
    return QRectF(x + r.x(), y + r.y(), max(1.0, r.width()), max(1.0, r.height()))


def font(size: int, weight: QFont.Weight = QFont.Weight.Normal, spacing: float = 0.0,
         family: str = FONT_FAMILY) -> QFont:
    f = QFont(family, size)
    f.setWeight(weight)
    if spacing:
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
    return f


# =============================================================================
# 7. 游戏逻辑模型（纯 Python，无 Qt 依赖 → --selftest 可以逐条断言）
# =============================================================================

class Game:
    """棋盘、随机、旋转、锁定、计分的全部规则。

    events 里按时间顺序堆事件，控件每帧 drain 一次用于配音效、粒子、浮字：
        ("spawn", kind) ("move",) ("rotate", kick) ("lock", kind, x, y) ("harddrop", x, y, n)
        ("hold", kind) ("clear", n, tspin, label, gain) ("tspin0", label, gain)
        ("perfect", bonus) ("levelup", lvl) ("dead", reason) ("over", reason)
    """

    def __init__(self, seed: int | None = None, start_level: int = 1) -> None:
        self.start_level = start_level
        self.das, self.arr = DAS_PRESETS[1][1], DAS_PRESETS[1][2]
        self.reset(seed)

    # ------------------------------------------------------------ 生命周期
    def reset(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)
        self.grid = [[0] * FIELD_COLS for _ in range(GRID_ROWS)]
        self.grid_rev = 0                   # 盘面版本号：控件据此判断"堆叠层"贴图要不要重画
        #: 彩蛋：已锁定的、贴了螺螺头像的那些格子，存 (x, y)。
        #: ⚠️ 单独存一份而不是塞进 ``grid``：``grid`` 每格只有一个 1..8 的小整数
        #: （配色 / 消行 / 自检都按这个假设写），改动它牵动太多地方。这里只记"哪些
        #: 格子要贴脸"，消行时跟着行一起搬，互不干扰。
        self.faces: set[tuple[int, int]] = set()
        self.bag: list[str] = []
        self.queue: list[str] = [self._from_bag() for _ in range(6)]
        self.active: dict | None = None
        self.hold: str | None = None
        self.hold_used = False
        self.score = 0
        self.lines = 0
        self.level = self.start_level
        self.combo = -1
        self.b2b = False
        self.pieces = 0
        self.elapsed = 0.0
        self.events: list[tuple] = []
        self.phase = "play"                 # play | clear | dying | over
        self.clear_rows: list[int] = []
        self.clear_t = 0.0
        self.clear_label = ""
        self.clear_gain = 0
        self.clear_tspin: str | None = None
        self.over_t = 0.0
        self.dead_filled = 0
        self.dead_reason = ""
        self.grav_acc = 0.0
        self.lock_timer = 0.0
        self.lock_resets = 0
        self.grounded = False
        self.last_rot = False
        self.last_kick = 0
        self.soft = False
        self.das_dir = 0
        self.dir_held = {-1: False, 1: False}     # 左右键各自是否还按着
        self.das_t = 0.0
        self.arr_t = 0.0
        self.das_fired = False
        self.stats = {
            "single": 0, "double": 0, "triple": 0, "tetris": 0,
            "tspin": 0, "tspin_mini": 0, "perfect": 0,
            "combo_max": 0, "hold": 0, "hard": 0, "soft": 0,
            "hard_cells": 0, "soft_cells": 0, "rotations": 0,
            "height": 0, "topout_row": GRID_ROWS,
        }
        self.spawn()
        self.events.clear()

    # ------------------------------------------------------------ 随机
    def _from_bag(self) -> str:
        if not self.bag:
            self.bag = list(KINDS)
            self.rng.shuffle(self.bag)
        return self.bag.pop()

    def expect_queue(self) -> list[str]:
        return list(self.queue[:5])

    # ------------------------------------------------------------ 几何
    @staticmethod
    def cells_of(kind: str, rot: int, x: int, y: int) -> tuple[tuple[int, int], ...]:
        return tuple((x + cx, y + cy) for cx, cy in ROTATIONS[kind][rot % 4])

    def active_cells(self) -> tuple[tuple[int, int], ...]:
        a = self.active
        if a is None:
            return ()
        return self.cells_of(a["kind"], a["rot"], a["x"], a["y"])

    def fits(self, kind: str, rot: int, x: int, y: int) -> bool:
        for bx, by in self.cells_of(kind, rot, x, y):
            if bx < 0 or bx >= FIELD_COLS or by >= GRID_ROWS:
                return False
            if by >= 0 and self.grid[by][bx]:
                return False
        return True

    def ghost_y(self) -> int:
        a = self.active
        if a is None:
            return 0
        y = a["y"]
        while self.fits(a["kind"], a["rot"], a["x"], y + 1):
            y += 1
        return y

    def stack_top(self) -> int:
        """最高的已占用行（GRID_ROWS = 完全空）。"""
        for y in range(GRID_ROWS):
            if any(self.grid[y]):
                return y
        return GRID_ROWS

    def stack_height(self) -> int:
        """堆叠高度（含出生区，满场 = GRID_ROWS）。"""
        return GRID_ROWS - self.stack_top()

    def board_signature(self) -> int:
        """盘面内容指纹：控件据此判断"堆叠层"贴图要不要重画。

        为什么不只用 grid_rev：自检 / 演示 / 体检代码会直接改 self.grid（造局面比走规则快），
        那些路径不会经过 lock_piece/collapse_rows。按内容取指纹就永远不会拿到过期贴图，
        代价是每帧 220 个格子的哈希（约 10µs），可以忽略。

        ⚠️ **必须把 ``faces`` 也掺进去**（彩蛋：螺螺的头像）：头像不属于 ``grid``
        的内容，只哈希 grid 的话，同一盘面"有没有脸"算出的指纹相同 —— 堆叠层
        贴图会被判定为没变而**沿用上一张**，头像于是时有时无。掺进排序后的格子
        列表即可（数量很少，代价可忽略）。
        """
        return hash((tuple(tuple(row) for row in self.grid),
                     tuple(sorted(self.faces))))

    def danger(self) -> float:
        """0（安全）→1（顶到可见区天花板）的危险度，用于边框预警。"""
        above = self.stack_top() - BUFFER_ROWS
        return max(0.0, min(1.0, 1.0 - above / 6.0))

    # ------------------------------------------------------------ 操作
    def _settle(self, count_reset: bool = True) -> None:
        """刷新贴地状态；玩家操作贴地的方块时按规则重置锁定计时器（最多 15 次）。"""
        a = self.active
        if a is None:
            return
        on = not self.fits(a["kind"], a["rot"], a["x"], a["y"] + 1)
        self.grounded = on
        if not on:
            self.lock_timer = 0.0
        elif count_reset and self.lock_resets < LOCK_RESET_MAX:
            self.lock_resets += 1
            self.lock_timer = 0.0

    def move(self, dx: int, dy: int = 0, gravity: bool = False) -> bool:
        a = self.active
        if a is None or self.phase != "play":
            return False
        if not self.fits(a["kind"], a["rot"], a["x"] + dx, a["y"] + dy):
            return False
        a["x"] += dx
        a["y"] += dy
        if dx:
            self.last_rot = False
        self._settle(count_reset=not gravity)
        if dx and not gravity:
            self.events.append(("move",))
        return True

    def rotate(self, direction: int) -> bool:
        """direction: +1 顺时针 / -1 逆时针 / 2 转 180°"""
        a = self.active
        if a is None or self.phase != "play":
            return False
        frm = a["rot"]
        to = (frm + 2) % 4 if direction == 2 else (frm + direction) % 4
        for i, (dx, dy) in enumerate(kick_table(a["kind"], frm, to)):
            if self.fits(a["kind"], to, a["x"] + dx, a["y"] + dy):
                a["rot"] = to
                a["x"] += dx
                a["y"] += dy
                self.last_rot = True
                self.last_kick = i
                self.stats["rotations"] += 1
                self._settle()
                self.events.append(("rotate", i))
                return True
        return False

    def soft_step(self) -> bool:
        """软降一格（成功才加点数）。"""
        a = self.active
        if a is None or self.phase != "play":
            return False
        if self.fits(a["kind"], a["rot"], a["x"], a["y"] + 1):
            a["y"] += 1
            self.last_rot = False
            self.score += SOFT_DROP_POINT
            self.stats["soft"] += 1
            self.stats["soft_cells"] += 1
            self.grounded = False
            self.lock_timer = 0.0
            return True
        self.grounded = True
        return False

    def hard_drop(self) -> int:
        a = self.active
        if a is None or self.phase != "play":
            return 0
        n = 0
        while self.fits(a["kind"], a["rot"], a["x"], a["y"] + 1):
            a["y"] += 1
            n += 1
        self.score += n * HARD_DROP_POINT
        self.stats["hard"] += 1
        self.stats["hard_cells"] += n
        if n:
            # 真的掉过格子才算"最后一次动作是硬降"；原地硬降不该抹掉刚做的旋转，
            # 否则玩家最常用的"转进去 + 空格锁定"就永远判不出 T-Spin
            self.last_rot = False
        self.events.append(("harddrop", a["x"], a["y"], n))
        self.lock_piece()
        return n

    def hold_piece(self) -> bool:
        if self.active is None or self.phase != "play" or self.hold_used:
            return False
        kind = self.active["kind"]
        nxt = self.hold
        self.hold = kind
        self.active = None
        self.stats["hold"] += 1
        ok = self._spawn_kind(nxt) if nxt else self.spawn()
        self.hold_used = True
        if ok:
            self.events.append(("hold", kind))
        return True

    def set_soft(self, on: bool) -> None:
        self.soft = bool(on)

    def press_dir(self, direction: int) -> None:
        """左右按下：立刻移动一格并开始 DAS 计时，同时记住这个方向还按着。"""
        self.dir_held[direction] = True
        self.das_dir = direction
        self.das_t = 0.0
        self.arr_t = 0.0
        self.das_fired = False
        self.move(direction, 0)

    def release_dir(self, direction: int) -> None:
        """松开一个方向键：另一个方向还按着就回到它，并按 ARR 直接续上（DAS 视为已蓄满）。"""
        self.dir_held[direction] = False
        if self.das_dir != direction:
            return
        other = -direction
        if self.dir_held.get(other):
            self.das_dir = other
            self.das_t = self.das
            self.arr_t = 0.0
            self.das_fired = True
        else:
            self.das_dir = 0
            self.das_fired = False

    def release_all(self) -> None:
        """松开全部方向键：暂停 / 失焦时调用，避免回来时"卡键"继续平移。"""
        self.dir_held[-1] = self.dir_held[1] = False
        self.das_dir = 0
        self.das_fired = False
        self.soft = False

    # ------------------------------------------------------------ 每帧推进
    def update(self, dt: float) -> None:
        if self.phase == "over":
            return
        self.elapsed += dt

        if self.phase == "dying":
            self.over_t += dt
            want = min(GRID_ROWS, int(self.over_t / OVER_ROW_TIME))
            while self.dead_filled < want:
                self.grid[GRID_ROWS - 1 - self.dead_filled] = [DEAD_ID] * FIELD_COLS
                self.dead_filled += 1
                self.grid_rev += 1
            if self.over_t >= OVER_TIME:
                self.phase = "over"
                self.events.append(("over", self.dead_reason))
            return

        a = self.active
        if a is not None:
            a["glow"] = max(0.0, a["glow"] - dt)
            a["flash"] = max(0.0, a.get("flash", 0.0) - dt)

        if self.phase == "clear":
            self.clear_t += dt
            if self.clear_t >= CLEAR_TIME:
                self.collapse_rows()
                self.phase = "play"
                self.spawn()
            return

        if a is None:
            self.spawn()
            return

        self._update_das(dt)

        interval = min(self.gravity_interval(), SOFT_INTERVAL) if self.soft else self.gravity_interval()
        if self.fits(a["kind"], a["rot"], a["x"], a["y"] + 1):
            # 只在悬空时积累重力：贴地的方块如果还继续攒，一旦被挪到空中就会"一次掉到底"
            # （20 级时每步 3.3 格，攒几秒就是几十格）
            self.grav_acc += dt
            guard = 0
            while self.grav_acc >= interval and guard < 40:
                guard += 1
                ok = self.soft_step() if self.soft else self.move(0, 1, gravity=True)
                if not ok:
                    break
                self.grav_acc -= interval
        else:
            self.grav_acc = 0.0

        if a is not None and self.fits(a["kind"], a["rot"], a["x"], a["y"] + 1):
            self.grounded = False
            self.lock_timer = 0.0
        else:
            self.grounded = True
            self.lock_timer += dt
            if self.lock_timer >= LOCK_DELAY:
                self.lock_piece()

    def gravity_interval(self) -> float:
        return gravity_interval(self.level)

    def _update_das(self, dt: float) -> None:
        if self.das_dir == 0:
            return
        self.das_t += dt
        if self.das_t < self.das:
            return
        if not self.das_fired:
            self.das_fired = True
            self.move(self.das_dir, 0)
            self.arr_t = 0.0
            return
        if self.arr <= 1e-9:                      # ARR = 0：一帧推到墙
            guard = 0
            while self.move(self.das_dir, 0) and guard < FIELD_COLS + 2:
                guard += 1
            return
        self.arr_t += dt
        guard = 0
        while self.arr_t >= self.arr and guard < FIELD_COLS:
            self.arr_t -= self.arr
            guard += 1
            if not self.move(self.das_dir, 0):
                self.arr_t = 0.0
                break

    # ------------------------------------------------------------ 锁定与消除
    def detect_tspin(self, kind: str, rot: int, x: int, y: int) -> str | None:
        if kind != "T" or not self.last_rot:
            return None
        blocked = 0
        filled = set()
        for cx, cy in ((0, 0), (2, 0), (0, 2), (2, 2)):
            bx, by = x + cx, y + cy
            occ = (bx < 0 or bx >= FIELD_COLS or by >= GRID_ROWS
                   or (by >= 0 and self.grid[by][bx]))
            if occ:
                blocked += 1
                filled.add((cx, cy))
        if blocked < 3:
            return None
        front = ((0, 0), (2, 0)) if rot == 0 else \
                ((2, 0), (2, 2)) if rot == 1 else \
                ((0, 2), (2, 2)) if rot == 2 else ((0, 0), (0, 2))
        if all(c in filled for c in front) or self.last_kick == 4:
            return "full"
        return "mini"

    def lock_piece(self) -> None:
        a = self.active
        if a is None:
            return
        kind, rot, x, y = a["kind"], a["rot"], a["x"], a["y"]
        cells = self.active_cells()
        for bx, by in cells:
            if by >= 0:
                self.grid[by][bx] = KIND_ID[kind]
        # 彩蛋：把贴头像的那一格记进盘面，落定之后也一直显示（见 self.faces）。
        # ⚠️ 用 a["face_i"] 取当前旋转态下的**同一个格子**：cells 是经过 ROTATIONS
        # 旋转后的坐标，用下标取就自动跟着转，不必再算一次旋转。
        fi = a.get("face_i", -1)
        if a.get("luoluo") and 0 <= fi < len(cells):
            self.faces.add(cells[fi])
        self.grid_rev += 1
        self.active = None
        tspin = self.detect_tspin(kind, rot, x, y)
        self.events.append(("lock", kind, x, y, tspin))
        if all(by < BUFFER_ROWS for _, by in cells):        # lock out：整块锁在出生区
            self.dead("lock out")
            return

        top = self.stack_top()
        self.stats["topout_row"] = min(self.stats["topout_row"], top)
        self.stats["height"] = max(self.stats["height"], self.stack_height())

        rows = [yy for yy in range(GRID_ROWS) if all(self.grid[yy])]
        if rows:
            n = len(rows)
            base = TSPIN_BASE[(tspin, min(n, 3))] if tspin else BASE_CLEAR[n]
            difficult = bool(tspin) or n == 4
            b2b_applied = difficult and self.b2b
            if b2b_applied:
                base = int(base * B2B_MULT)
            gain = base * self.level
            self.combo += 1
            self.stats["combo_max"] = max(self.stats["combo_max"], self.combo)
            if self.combo >= 1:
                gain += COMBO_UNIT * self.combo * self.level
            self.b2b = bool(difficult)
            self.score += gain
            self.clear_rows = rows
            self.clear_t = 0.0
            self.clear_label = self.clear_text(n, tspin, self.combo)
            self.clear_gain = gain
            self.clear_tspin = tspin
            self.phase = "clear"
            self.events.append(("clear", n, tspin, self.clear_label, gain,
                                b2b_applied, self.combo))
            if tspin:
                self.stats["tspin" if tspin == "full" else "tspin_mini"] += 1
            self.stats[{1: "single", 2: "double", 3: "triple", 4: "tetris"}[n]] += 1
        else:
            self.combo = -1
            if tspin:
                base = TSPIN_BASE[(tspin, 0)]
                gain = base * self.level
                self.score += gain
                self.stats["tspin" if tspin == "full" else "tspin_mini"] += 1
                self.events.append(("tspin0", "T-SPIN" if tspin == "full" else "T-SPIN MINI", gain))
            self.spawn()

    @staticmethod
    def clear_text(n: int, tspin: str | None, combo: int) -> str:
        if tspin:
            word = {1: "单消", 2: "双消", 3: "三连消"}.get(n, "")
            head = "T-SPIN" if tspin == "full" else "T-SPIN MINI"
            return f"{head} {word}".strip()
        return {1: "单消", 2: "双消", 3: "三连消", 4: "四连消 TETRIS!"}.get(n, "消除")
    def collapse_rows(self) -> None:
        rows = sorted(self.clear_rows)
        n = len(rows)
        gone = set(rows)
        keep = [row for y, row in enumerate(self.grid) if y not in gone]
        self.grid = [[0] * FIELD_COLS for _ in range(n)] + keep
        # 彩蛋：头像格子跟着**同一套行搬运规则**走 —— 被消掉的行连同那格一起消失，
        # 其余各行下移「它**下方**被消掉的行数」：
        #     新行号 = 旧行号 + count(被消行 > 旧行号)
        # ⚠️ 这里连着踩过两次坑（先写 `- count(r < fy)`，又改成 `+ count(r < fy)`，
        #    都不对）。方向靠想当然很容易错，所以这个结论是**穷举实测**出来的：
        #    对 6 行 / 22 行网格跑了 170 组「行 × 被消集合」，只有
        #    `old + count(gone > old)` 全中（本行不会被消，`>=` 与 `>` 等价），
        #    其余写法最多错 166/170。改这段请务必重跑"记号方块跟着走"那类测试。
        if self.faces:
            self.faces = {
                (fx, fy + sum(1 for r in rows if r > fy))
                for fx, fy in self.faces if fy not in gone
            }
        self.grid_rev += 1
        old_level = self.level
        self.lines += n
        self.level = min(MAX_LEVEL, self.start_level + self.lines // LINE_PER_LEVEL)
        if self.level != old_level:
            self.events.append(("levelup", self.level))
        if not any(any(row) for row in self.grid):
            # 完美清除的奖励按"消行前"的等级算（官方：等级一律取消行前的那一刻）
            bonus = PERFECT_BASE[min(n, 4)] * old_level
            self.score += bonus
            self.stats["perfect"] += 1
            self.events.append(("perfect", bonus))
        self.clear_rows = []
        self.clear_label = ""
        self.clear_tspin = None

    # ------------------------------------------------------------ 结束
    def dead(self, reason: str) -> None:
        if self.phase in ("dying", "over"):
            return
        self.dead_reason = reason
        self.phase = "dying"
        self.over_t = 0.0
        self.dead_filled = 0
        self.release_all()
        self.events.append(("dead", reason))

    def spawn(self) -> bool:
        kind = self.queue.pop(0)
        self.queue.append(self._from_bag())
        return self._spawn_kind(kind)

    def _spawn_kind(self, kind: str) -> bool:
        x, y = SPAWN_X[kind], SPAWN_Y
        # 彩蛋：这一块是否贴螺螺的头像；贴的话**只挑一格**（见 LUOLUO_RATE）
        face = self.rng.random() < LUOLUO_RATE
        self.active = {"kind": kind, "rot": 0, "x": x, "y": y,
                       "glow": SPAWN_GLOW, "flash": 0.0,
                       "luoluo": face,
                       # 贴头像的那一格在 ROTATIONS 里的下标（不加头像时为 -1）
                       "face_i": self.rng.randrange(4) if face else -1}
        self.hold_used = False
        self.grav_acc = 0.0
        self.lock_timer = 0.0
        self.lock_resets = 0
        self.last_rot = False
        self.last_kick = 0
        if not self.fits(kind, 0, x, y):                 # block out：出生位置被占
            self.dead("block out")
            return False
        # 官方规则：方块出现后若下方为空，立刻下移一格（所以新块会露出小半个在场内）
        if self.fits(kind, 0, x, y + 1):
            self.active["y"] = y + 1
        self.pieces += 1
        self.grounded = not self.fits(kind, 0, self.active["x"], self.active["y"] + 1)
        self.events.append(("spawn", kind))
        return True

    # ------------------------------------------------------------ 统计
    def pps(self) -> float:
        return self.pieces / self.elapsed if self.elapsed > 0.05 else 0.0

    def lines_to_next(self) -> tuple[int, int]:
        """(已在本级消的行数, 本级需要的行数)"""
        need = LINE_PER_LEVEL
        done = self.lines - (self.level - self.start_level) * LINE_PER_LEVEL
        return max(0, min(need, done)), need


# =============================================================================
# 8. 控件：固定步长逻辑 + 输入 + 特效 + 覆盖层
# =============================================================================

DEFAULT_OPT = {
    "ghost": True, "grid": True, "sfx": True, "music": True, "shake": True,
    "face": True,                         # 彩蛋：螺螺的头像（见 LUOLUO_RATE）
    "feel": 1, "start_level": 0,          # feel 索引进 DAS_PRESETS，start_level 索引进 START_LEVELS
    "theme": 0,                           # 索引进 THEME_MODES：0 = 跟随系统，1 = 深色，2 = 浅色
}


def save_path() -> Path:
    """最高分 / 设置的存档位置（放在 app_data 下，与游戏仓库文件互不打扰）。"""
    return _data_dir('save.json')


def load_save() -> dict:
    try:
        p = save_path()
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def _safe_int(value, default: int = 0) -> int:
    """存档里的数字可能是任何东西（手改、旧版本、损坏），取不到就用默认值。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


#: 一次消行最多能拿多少分基础分（T-Spin 三连消 1600，比四连消的 800 更高）。
BEST_CLEAR_BASE = max(max(TSPIN_BASE.values()), max(BASE_CLEAR.values()))   # 1600

#: 每一行最多折算多少分。推导（见 :func:`_max_plausible` 的说明）：
#:
#: * 最划算的是 **T-Spin 三连消**：1600 基础 × B2B 1.5 × 满级 20 = 48000 分，
#:   但它只消 **3 行** → 16000 分/行（四连消 800×1.5×20=24000 分 / 4 行 = 6000 分/行，
#:   反而不如它）；
#: * 再给 **2 倍**余量，把 combo（每级 50×等级）、Perfect Clear（最高 2000×等级）
#:   以及软/硬降的一点零头都算进去 → 32000 分/行。
#:
#: ⚠️ 这个上限的作用是"挡掉荒谬的值"（9999999、10²⁰），不是精确鉴定成绩真伪：
#: 要打满它得在满级下不断做出 T-Spin 三连消并维持 B2B 不断 —— 真做到了也不该被误判。
MAX_POINTS_PER_LINE = int(BEST_CLEAR_BASE * B2B_MULT * MAX_LEVEL / 3 * 2)   # 32000

#: 统计量的上界。这几个数字本身只是"别让乘数失控"的护栏，取得都很宽：
#: 每小时按 200 块算，10 万局也要连续玩几千小时 —— 正常用户一辈子碰不到。
MAX_TOTAL_LINES = 100_000_000
MAX_GAMES = 1_000_000
MAX_COMBO = 100_000


def _max_plausible(total_lines: int) -> int:
    """按"已消行数"推算最高分的**理论上限**（用于挡住明显被手改过的存档）。

    ⚠️ **为什么需要它**：``save.json`` 是明文 JSON，而且就在用户目录下。实测踩到过
    一份 ``high = 9999999``（10⁷−1，典型的"占位 / 封顶"值）却只有 21 局、52 行的
    存档 —— 而 52 行按最理想算（每次都四连消 + B2B 不断 + 20 级满级）也只有
    **约 31 万分**，即那个数字比理论极值还高 32 倍。最高分是整个界面里唯一一个
    "用户会当真"的数字，被这种值污染之后就彻底失去意义了。

    ⚠️ 上限**刻意留了余量**（每行按 :data:`MAX_POINTS_PER_LINE` = 32000 算，约为
    真实上限 16000 的 2 倍）：本函数的职责是**挡掉荒谬的值**（9999999、10²⁰、负数），
    不是精确鉴定成绩真伪。真要打满它得在满级下全程维持 T-Spin 三连消 + B2B 不断 ——
    万一有人做到了，也不该被误判成作弊。

    Args:
        total_lines: 该存档累计消掉的行数。

    Returns:
        int: 允许的最高分。**一行没消过就是 0** —— 没有消行就不可能有分数
        （软降/硬降那点零头也是跟着方块走的，而没消行就不会有 ``total_lines``）。
    """
    return max(0, int(total_lines)) * MAX_POINTS_PER_LINE


def sanitize_stats(saved) -> dict:
    """把存档里的**统计量**收成合法值（非负、且不超出理论上限）。

    ⚠️ 与 :func:`sanitize_opt` 的分工：那个管"设置"，这个管四个统计数字 ——
    ``high`` / ``games`` / ``total_lines`` / ``best_combo``。原先这四个只过了一道
    ``_safe_int()``（只保证是整数），于是 ``-5`` 或 ``9999999`` 都会被照单全收：
    前者让"破纪录"动画每次都触发，后者则见 :func:`_max_plausible` 的说明。

    ⚠️ **``high`` 的判据依赖 ``total_lines``**，所以两者必须一起校验、且顺序固定：
    先把 ``total_lines`` 收干净（它自己有上限），再用它去算 ``high`` 允许的上限。
    反过来（先判 high）就是拿旧的行数去限制新的高分，会把刚打出的成绩误杀。

    Args:
        saved: 存档字典（``load_save()`` 的返回值，可能损坏 / 缺字段）。

    Returns:
        dict: 只含这四个键的干净字典。
    """
    if not isinstance(saved, dict):
        saved = {}

    # ⚠️ 行数与局数也要有上限：它们是**乘数**（用来推算 high 的天花板），
    #    留一个 10^18 的行数会让 _max_plausible 直接失去意义。
    total_lines = max(0, min(_safe_int(saved.get("total_lines")), MAX_TOTAL_LINES))
    games = max(0, min(_safe_int(saved.get("games")), MAX_GAMES))
    best_combo = max(0, min(_safe_int(saved.get("best_combo")), MAX_COMBO))

    # 最后才收 high：它要用到已经收干净的 total_lines
    high = min(max(0, _safe_int(saved.get("high"))), _max_plausible(total_lines))

    return {"high": high, "games": games,
            "total_lines": total_lines, "best_combo": best_combo}


def sanitize_opt(saved_opt) -> dict:
    """把存档里的设置收成合法值：越界索引取模、其余一律转 bool。

    存档只当"建议"—— 手改坏一个字段不该让游戏起不来（曾实测：{"feel": 9} → IndexError）。
    """
    opt = dict(DEFAULT_OPT)
    if isinstance(saved_opt, dict):
        for k, v in saved_opt.items():
            if k not in opt:
                continue
            if k == "feel":
                opt[k] = _safe_int(v) % len(DAS_PRESETS)
            elif k == "start_level":
                opt[k] = _safe_int(v) % len(START_LEVELS)
            elif k == "theme":
                opt[k] = _safe_int(v) % len(THEME_MODES)
            else:
                opt[k] = bool(v)
    return opt


class TetrisWidget(QWidget):
    """画面、手感与音效都在这里；规则在 Game 里。"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("螺螺是方块 — Tetris")
        self.setMinimumSize(420, 456)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setWindowIcon(make_window_icon())

        self.save_data = load_save()
        self.opt = sanitize_opt(self.save_data.get("opt"))
        # ⚠️ 统计量走 sanitize_stats，而不是四个裸 _safe_int：手改的存档里可能是负数
        #    或"封顶值"（实测见过 high = 9999999 而 total_lines 只有 52 —— 比按行数
        #    推算的理论极值还高 32 倍）。最高分是这界面上唯一一个会被当真的数字，
        #    被这种值污染之后就彻底没意义了。
        stats = sanitize_stats(self.save_data)
        self.high = stats["high"]
        self.games = stats["games"]
        self.total_lines = stats["total_lines"]
        self.best_combo = stats["best_combo"]
        self.persist = True

        self.audio = Audio()
        self.audio.set_sfx(bool(self.opt["sfx"]))
        self.audio.set_music(bool(self.opt["music"]))

        self.game = Game(seed=None, start_level=START_LEVELS[self.opt["start_level"]])
        self._apply_feel()

        self.acc = 0.0
        self.fps = 60.0
        self.t = 0.0
        self.paused = False
        self.overlay: str | None = None
        self.auto_pause = True
        self.recorded = False
        self.new_record = False

        self.particles: list[dict] = []
        self.toasts: list[dict] = []
        self.trails: list[dict] = []
        self.shake_t = 0.0
        self.shake_amp = 0.0
        self.flash = 0.0
        self.banner: dict | None = None
        self.hold_flash = 0.0
        self.hover_row = -1
        self._bg_cache: dict[tuple, QPixmap] = {}
        self._stack_cache: dict[tuple, QPixmap] = {}
        self._chrome_cache: dict[tuple, QPixmap] = {}
        self._wbg_cache: dict[tuple, QPixmap] = {}
        self._fps_acc = 0.0
        self._theme_ready = False           # apply_theme 是否已经定过一次主题
        self._palette_hooked = False        # 是否已接上 QApplication.paletteChanged

        self.clock = QElapsedTimer()
        self.clock.start()
        self.last_ms = self.clock.elapsed()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self._frame)
        self.timer.start(max(1, int(1000 / FPS)))

        # 主题：先按设置定一次，再挂上"系统主题变了"的信号（见 _on_palette_changed）。
        self.apply_theme()

    # ------------------------------------------------------------ 主题（深色 / 浅色）
    def _stylesheet_dark(self):
        """从宿主套的样式表里读底色判深浅；读不到返回 ``None``。

        ⚠️ **为什么不能只看 palette**：zmlx 的主题（「设置 → 样式表」，以及随包发布的
        ``zml_window_style.qss``）走的是 ``setStyleSheet``，它生成的规则是
        ``QWidget { color: ... }`` 加
        ``QMainWindow, QDialog, ... { background-color: ... }`` —— **一个 ``QPalette``
        角色都没改**。实测：套上深色样式表后 ``palette().Window`` 仍是默认的
        ``#efefef``（L=239），纯按 palette 判会一直判成"浅色" —— 用户明明设了深色
        主题，游戏却换了浅色皮肤（实测踩到过）。所以样式表必须单独读一份。

        做法：**先看 QApplication，再沿 ``parent()`` 往上找**第一份非空 ``styleSheet``，
        取其中第一条 ``background-color``。

        ⚠️ 两级都必须看，实测漏了任一级都不行：zmlx 的 ``gui.set_style_sheet`` 最终落在
        **QApplication** 上（``MainWindow.setStyleSheet`` 那条转接），而
        ``QApplication.styleSheet()`` **不在**任何控件的 ``parent()`` 链里 —— 只往上找
        会一无所获；反过来，祖先窗口上也可能是有人单独设的。

        取第一条 ``background-color`` 是因为 zmlx 生成的规则里第一条正是"容器底色"
        （窗口底色）：实测深色 ``#14161c``(L=24)、浅色 ``#f6f7fb``(L=249)，分得很开。
        两边都取不到就返回 ``None``，由调用方退回 palette。
        """
        try:
            candidates = []
            app = QApplication.instance()
            if app is not None:
                candidates.append(app.styleSheet())
            node = self
            while node is not None:
                candidates.append(node.styleSheet())
                node = node.parent()
            for qss in candidates:
                if not qss:
                    continue
                m = re.search(
                    r'background-color\s*:\s*(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})', qss)
                if m is None:
                    continue
                col = QColor(m.group(1))
                if col.isValid():
                    return col.lightness() < 128
            return None
        except Exception:                   # pragma: no cover - 解析失败就退回 palette
            return None

    def _system_dark(self) -> bool:
        """当前系统 / 宿主样式**是不是**深色。

        两个来源，按可靠性排序：

        1. **样式表**（:meth:`_stylesheet_dark`）—— zmlx 的主题实际走这条路；
        2. **palette** —— 操作系统级的深色模式，以及没有任何样式表时的兜底。

        ⚠️ 刻意**不**调 ``gui.in_dark_mode()``：那要走 GuiApi 的通道往返，而本函数在
        ``paletteChanged`` 回调与每帧轮询里都会被调到 —— 前者在事件处理路径上，不该
        再排队；何况无头模式下 ``gui.exists()`` 为假，那个接口给不出答案。
        """
        from_qss = self._stylesheet_dark()
        if from_qss is not None:
            return from_qss
        try:
            bg = self.palette().color(QtGui.QPalette.ColorRole.Window)
            return bg.lightness() < 128
        except Exception:                   # pragma: no cover - 极端环境下退回深色
            return True

    def theme_dark(self) -> bool:
        """按设置 + 系统决定**当前该用**深色还是浅色。"""
        mode = THEME_MODES[self.opt.get("theme", 0) % len(THEME_MODES)]
        if mode == "深色":
            return True
        if mode == "浅色":
            return False
        return self._system_dark()

    def apply_theme(self) -> None:
        """把当前主题应用到调色板，并在**真的变了**的时候清掉那些按旧主题烘的贴图。

        ⚠️ **必须清缓存**：本游戏有 6 层 ``QPixmap`` 缓存（方块、整窗底、chrome、
        场地背景、堆叠层、头像），key 里只有"内容 + 像素尺寸"、**不含主题**。
        不清的话换主题后会看到"新配色的文字压在旧配色的面板上"这种半新半旧的画面。
        这里刻意**不**清 ``_LUOLUO_CACHE``（头像与主题无关，重做一次圆裁剪纯属浪费）。

        ⚠️ 只在 ``dark`` 真的翻转时才清：``apply_theme`` 会在系统主题变化、设置改动、
        控件构造时都被调到，每次都清等于白白重烘所有贴图。
        """
        dark = self.theme_dark()
        if dark == _Palette.dark and getattr(self, '_theme_ready', False):
            return
        _Palette.use_dark(dark)
        self._theme_ready = True
        if hasattr(self, '_bg_cache'):      # 构造期间还没有这些缓存
            self._reset_caches()
        self.update()

    def _on_palette_changed(self, *_args) -> None:
        """宿主 / 系统换主题时回调（接 ``QApplication.paletteChanged``）。

        ⚠️ 槽写成**绑定方法**（不是 lambda）：lambda 没有接收者 QObject，控件销毁后
        Qt 不会自动断连，迟到的事件会碰已经析构的 C++ 对象。

        ⚠️ 只在"跟随系统"时才响应：用户显式锁定了深色 / 浅色，就不该被系统带跑。

        ⚠️ **光靠这个信号是不够的**：实测 ``QApplication.setPalette()`` 会发它，但
        ``setStyleSheet()``（zmlx 的「设置 → 样式表」以及 ``zml_window_style.qss``
        走的就是这条路）**只改 palette、一个信号都不发**。所以真正的自动跟随靠
        :meth:`_poll_theme` 轮询兜底，本回调只是让"操作系统换深色"这类场景**立刻**
        生效、不必等下一次轮询。
        """
        if THEME_MODES[self.opt.get("theme", 0) % len(THEME_MODES)] != "跟随系统":
            return
        self.apply_theme()

    def _poll_theme(self) -> None:
        """廉价的主题轮询（挂在每帧的 ``advance`` 末尾）。

        ⚠️ 为什么需要它：见 :meth:`_on_palette_changed` —— 换样式表不发信号，只能自己
        定期看一眼 palette。代价只有一个亮度计算（约 1µs），相对每帧 4ms 的绘制预算
        可以忽略；而 :meth:`apply_theme` 在主题没变时会立刻返回，不会白白清缓存。
        """
        if THEME_MODES[self.opt.get("theme", 0) % len(THEME_MODES)] == "跟随系统":
            self.apply_theme()

    def _reset_caches(self) -> None:
        """丢掉所有"按主题 / 尺寸烘出来"的贴图（头像缓存除外）。"""
        self._bg_cache.clear()
        self._stack_cache.clear()
        self._chrome_cache.clear()
        self._wbg_cache.clear()
        clear_pixmap_cache()

    # ------------------------------------------------------------ 每帧
    def _frame(self) -> None:
        now = self.clock.elapsed()
        dt = (now - self.last_ms) / 1000.0
        self.last_ms = now
        dt = max(0.0, min(dt, 0.25))
        if dt > 0:
            self.fps += 0.12 * ((1.0 / dt) - self.fps)
        self.advance(dt)
        self.update()

    def advance(self, dt: float) -> None:
        """推进 dt 秒：逻辑走固定步长，特效走真实 dt。测试直接调它，不依赖计时器。"""
        self.t += dt
        self._poll_theme()              # 换样式表不发信号，只能每帧看一眼（代价约 1µs）
        running = (not self.paused) and self.overlay is None and self.game.phase != "over"
        if running:
            self.acc += dt
            cap = LOGIC_STEP * MAX_SUBSTEPS
            if self.acc > cap:
                self.acc = cap
            steps = 0
            while self.acc >= LOGIC_STEP and steps < MAX_SUBSTEPS:
                self.acc -= LOGIC_STEP
                steps += 1
                self.game.update(LOGIC_STEP)
                self._drain_events()
        self._advance_fx(dt)

    # ------------------------------------------------------------ 事件 -> 视听反馈
    def _drain_events(self) -> None:
        g = self.game
        while g.events:
            ev = g.events.pop(0)
            self._handle_event(ev)

    def _handle_event(self, ev: tuple) -> None:
        kind = ev[0]
        g = self.game
        if kind == "move":
            self.audio.play("move", 0.45)
        elif kind == "rotate":
            self.audio.play("rotate", 0.5)
        elif kind == "lock":
            _, pk, px, py, tspin = ev
            self.audio.play("lock", 0.7)
            cx, cy = self.cell_center(px + 1, py + 1)
            self.add_particles(cx, cy, 5, PIECE_COLORS[pk], speed=60, life=0.32, size=2.6, grav=140)
        elif kind == "harddrop":
            _, px, py, n = ev
            self.audio.play("harddrop", 0.8)
            self.shake(0.16, min(7.0, 2.0 + n * 0.35))
            for c in range(FIELD_COLS):
                self.trails.append({"c": c, "r0": py - n, "r1": py, "t": 0.0, "life": 0.18})
            _, y = self.cell_center(0, py + 1)
            for i in range(10):
                x = FIELD_X + (px + 0.5 + (i % 5) * 0.9) * CELL
                self.add_particles(x, y, 3, QColor(190, 200, 225), speed=110, life=0.34,
                                   size=2.2, grav=220)
        elif kind == "hold":
            self.hold_flash = 0.3
            self.audio.play("hold", 0.6)
        elif kind == "clear":
            _, n, tspin, label, gain, b2b, combo = ev
            self._fx_clear(n, tspin, label, gain, b2b, combo)
        elif kind == "tspin0":
            _, label, gain = ev
            self.audio.play("tspin", 0.8)
            self.show_banner(label, f"+{gain}", COL_ACCENT() if ev[1].endswith("MINI") else COL_GOLD())
            c = g.active
            if c:
                cx, cy = self.cell_center(c["x"] + 1, c["y"] + 1)
                self.add_particles(cx, cy, 18, COL_ACCENT(), speed=200, life=0.5, size=3.0, grav=90)
        elif kind == "perfect":
            _, bonus = ev
            self.audio.play("perfect", 0.9)
            self.show_banner("完美清除", f"PERFECT CLEAR · 额外 +{bonus}", QColor(255, 240, 180), 1.6)
            self.flash = max(self.flash, 0.5)
            self.shake(0.3, 5.0)
        elif kind == "levelup":
            _, lvl = ev
            self.audio.play("levelup", 0.85)
            self.show_banner(f"LEVEL {lvl}", "速度提升", COL_GOOD(), 1.1)
        elif kind == "dead":
            self.audio.play("gameover", 0.9)
            self.shake(0.5, 8.0)
            self.flash = max(self.flash, 0.35)
        elif kind == "over":
            self._finish_game()
        elif kind == "spawn":
            pass

    def _fx_clear(self, n: int, tspin: str | None, label: str, gain: int,
                  b2b: bool = False, combo: int = 0) -> None:
        g = self.game
        self.audio.play({1: "clear1", 2: "clear2", 3: "clear3", 4: "tetris"}.get(n, "clear1"), 0.9)
        if tspin:
            self.audio.play("tspin", 0.7)
        rows = list(g.clear_rows)
        for y in rows:
            for c in range(FIELD_COLS):
                v = g.grid[y][c]
                col = PIECE_COLORS.get(ID_KIND.get(v, "T"), COL_ACCENT())
                cx, cy = self.cell_center(c + 0.5, y + 0.5)
                self.add_particles(cx, cy, 4, col, speed=230, life=0.62, size=3.4, grav=520)
        _, mid_y = self.cell_center(0, sum(rows) / len(rows) + 0.5)
        self.toasts.append({"text": f"+{gain}", "x": FIELD_X + FIELD_W * 0.5, "y": mid_y - 26,
                            "t": 0.0, "life": 1.05, "color": COL_GOLD(), "size": 17, "vy": -34})
        self.show_banner(f"{label}{'  B2B' if b2b else ''}",
                         f"连击 ×{combo}" if combo >= 1 else "", COL_GOLD(), 0.95)
        if n >= 3:
            self.flash = max(self.flash, 0.22 if n == 3 else 0.4)
        self.shake(0.22, 3.0 + 1.6 * n)

    def show_banner(self, text: str, sub: str, color: QColor, life: float = 1.0) -> None:
        self.banner = {"text": text, "sub": sub, "color": QColor(color), "t": 0.0, "life": life}

    def shake(self, dur: float, amp: float) -> None:
        if not self.opt["shake"]:
            return
        self.shake_t = max(self.shake_t, dur)
        self.shake_amp = max(self.shake_amp, amp)

    def add_particles(self, x: float, y: float, n: int, color: QColor, speed: float = 120.0,
                      life: float = 0.5, size: float = 3.0, grav: float = 300.0,
                      spread: float = math.tau, kind: str = "spark") -> None:
        if len(self.particles) > 900:
            return
        rnd = self.game.rng
        for _ in range(n):
            a = rnd.uniform(0, spread) - spread / 2.0
            v = speed * rnd.uniform(0.45, 1.0)
            self.particles.append({
                "x": x, "y": y, "vx": math.sin(a) * v, "vy": -abs(math.cos(a)) * v * 0.9,
                "life": life * rnd.uniform(0.7, 1.25), "max": life, "color": QColor(color),
                "size": size * rnd.uniform(0.7, 1.3), "grav": grav, "kind": kind,
            })

    def _advance_fx(self, dt: float) -> None:
        alive = []
        for p in self.particles:
            p["life"] -= dt
            if p["life"] <= 0:
                continue
            p["vy"] += p["grav"] * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            alive.append(p)
        self.particles = alive

        toasts = []
        for s in self.toasts:
            s["t"] += dt
            s["y"] += s["vy"] * dt
            s["vy"] *= 0.94
            if s["t"] < s["life"]:
                toasts.append(s)
        self.toasts = toasts

        trails = []
        for tr in self.trails:
            tr["t"] += dt
            if tr["t"] < tr["life"]:
                trails.append(tr)
        self.trails = trails

        if self.shake_t > 0:
            self.shake_t = max(0.0, self.shake_t - dt)
            if self.shake_t == 0:
                self.shake_amp = 0.0
        self.flash = max(0.0, self.flash - dt * 1.6)
        self.hold_flash = max(0.0, self.hold_flash - dt)
        if self.banner is not None:
            self.banner["t"] += dt
            if self.banner["t"] >= self.banner["life"]:
                self.banner = None

    def shake_offset(self) -> tuple[float, float]:
        if self.shake_t <= 0 or self.shake_amp <= 0:
            return 0.0, 0.0
        k = self.shake_t / 0.5
        amp = self.shake_amp * min(1.0, k)
        return (math.sin(self.t * 97.0) * amp, math.cos(self.t * 61.0) * amp * 0.7)

    # ------------------------------------------------------------ 局管理
    def request_close(self) -> None:
        """请求「关掉游戏」——暂停卡片上的 Q、结算界面的 Esc 都走这里.

        ⚠️ **绝不要用 ``self.close()``**：本控件在 zmlx 里是**标签页里的子控件**，
        而对一个子控件调 ``close()`` 只会把它 ``hide()`` 掉 —— 标签头还留着、
        ``QTabWidget.currentWidget()`` 还会返回这个**已经隐藏**的控件，标签页状态
        就此损坏（实测：之后点标签头能把它再显示出来，但它已经"被关过一次"了）。
        原版是独立顶层窗口，``close()`` 语义正确，所以这一处是移植带来的**必须改**
        的地方。

        ★ 正确的做法是**请宿主关掉这个标签页**（``TabWidget.close_tab`` 会走完
        ``save_file`` / ``cleanup_before_tab_close`` / ``deleteLater`` 全套流程）。
        宿主通过 ``self.close_callback`` 注入；若没人注入（例如单独跑 ``test_1()``
        的独立窗口场景），就退回 ``close()`` —— 那时它确实是顶层窗口，语义正确。
        """
        cb = getattr(self, 'close_callback', None)
        if callable(cb):
            cb()
        else:
            self.close()

    def _apply_feel(self) -> None:
        _, das, arr = DAS_PRESETS[self.opt["feel"]]
        self.game.das, self.game.arr = das, arr

    def new_game(self) -> None:
        self.game.start_level = START_LEVELS[self.opt["start_level"]]
        self._apply_feel()
        self.game.reset()
        self._drain_events()
        self.game.events.clear()
        self.paused = False
        self.overlay = None
        self.recorded = False
        self.new_record = False
        self.hover_row = -1
        self.acc = 0.0
        self.particles.clear()
        self.toasts.clear()
        self.trails.clear()
        self.shake_t = 0.0
        self.flash = 0.0
        self.audio.play("go", 0.7)
        self.show_banner("开始!", f"起始等级 {self.game.level}", COL_ACCENT(), 0.9)

    def toggle_pause(self) -> None:
        # 结算界面与结算动画期间不接暂停：否则"暂停"会把死亡动画冻在半路
        if self.game.phase in ("dying", "over"):
            return
        self.paused = not self.paused
        if self.paused:
            self.game.release_all()             # 暂停时松开所有方向键，避免"卡键"
            self.audio.set_music(False)
        else:
            self.audio.set_music(bool(self.opt["music"]))
            self.acc = 0.0
        self.audio.play("pause", 0.6 if self.paused else 0.4)

    def _finish_game(self) -> None:
        if self.recorded:
            return
        self.recorded = True
        g = self.game
        new_high = g.score > self.high
        self.new_record = new_high
        self.high = max(self.high, g.score)
        self.games += 1
        self.total_lines += g.lines
        self.best_combo = max(self.best_combo, g.stats["combo_max"])
        # 记一局战绩：save.json 里只有四个被压扁的累计值（high / games / total_lines /
        # best_combo），看不出"哪一局、什么等级、打了多久"。这里按局留明细。
        # ⚠️ 与 write_save 共用 self.persist 开关：自测不污染用户的记录文件。
        if self.persist:
            record_event(
                'game', score=g.score, lines=g.lines, level=g.level, pieces=g.pieces,
                combo_max=g.stats["combo_max"], tetris=g.stats["tetris"],
                tspin=g.stats["tspin"] + g.stats["tspin_mini"],
                perfect=g.stats["perfect"], duration=round(g.elapsed, 1),
                pps=round(g.pps(), 2), record=new_high, games=self.games)
        self.write_save(why='game_over')
        if new_high:
            self.audio.play("perfect", 0.8)
            self.flash = max(self.flash, 0.45)

    def write_save(self, why: str = 'unknown') -> None:
        """把最高分 / 设置写进 ``save.json``，并记一笔写盘审计。

        Args:
            why: **谁触发的这次写盘**。它会原样进 ``record.jsonl`` —— 事后要靠它
                区分"正常打完一局"和"某个按键顺手改了设置"，所以各调用点都要传
                具体来源，别用默认值。

        Note:
            - 写失败**不抛异常**（原逻辑如此）：没记下最高分也比让游戏崩掉强。
              但失败会在记录里留下 ``ok=false`` + ``err``，不会悄悄消失。
        """
        if not self.persist:
            return                      # 自测（playthrough_check）里刻意不落盘
        p = save_path()
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps({
                "high": self.high, "games": self.games, "total_lines": self.total_lines,
                "best_combo": self.best_combo, "opt": self.opt,
            }, ensure_ascii=False, indent=1), encoding="utf-8")
            record_write('save', p, why=why)
        except Exception as err:
            record_write('save', p, why=why, ok=False,
                         err=f'{type(err).__name__}: {err}')

    # ------------------------------------------------------------ 输入
    def keyPressEvent(self, ev) -> None:  # noqa: N802
        if ev.isAutoRepeat():
            ev.accept()
            return
        k, mod = ev.key(), ev.modifiers()
        g = self.game

        if k == Qt.Key.Key_F11:
            self.toggle_fullscreen()
            return
        if k == Qt.Key.Key_F1:
            self.overlay = None if self.overlay == "help" else "help"
            self.update()
            return
        if k == Qt.Key.Key_F2:
            self.overlay = None if self.overlay == "settings" else "settings"
            self.update()
            return
        if self.overlay is not None:
            if k == Qt.Key.Key_Escape:
                self.overlay = None
            elif self.overlay == "settings" and Qt.Key.Key_1 <= k <= Qt.Key.Key_9:
                self.cycle_setting(k - Qt.Key.Key_1)   # 数字键只在设置面板里改设置
            return
        if k == Qt.Key.Key_Escape:
            if g.phase == "over":
                self.request_close()
            else:
                self.toggle_pause()
            return
        if k == Qt.Key.Key_Q and (g.phase == "over" or self.paused):
            self.request_close()                        # 暂停卡片上写着"Q 退出"就得真能退
            return
        if k == Qt.Key.Key_R:
            self.new_game()
            return
        if k == Qt.Key.Key_M:
            on = not (self.opt["sfx"] or self.opt["music"])
            self.opt["sfx"] = self.opt["music"] = on
            self.audio.set_sfx(on)
            self.audio.set_music(on)
            self.write_save(why='key:mute')
            return
        if k == Qt.Key.Key_B:
            self.opt["music"] = not self.opt["music"]
            self.audio.set_music(bool(self.opt["music"]) and not self.paused)
            self.write_save(why='key:music')
            return
        if k == Qt.Key.Key_P:
            self.toggle_pause()
            return

        if self.paused or g.phase != "play":
            # 暂停时用空格继续、结算界面用空格重开；消行冻结/结算动画期间空格不该有任何副作用
            if k == Qt.Key.Key_Space and (self.paused or g.phase == "over"):
                if g.phase == "over":
                    self.new_game()
                else:
                    self.toggle_pause()
            return

        if k == Qt.Key.Key_Left:
            g.press_dir(-1)
        elif k == Qt.Key.Key_Right:
            g.press_dir(1)
        elif k == Qt.Key.Key_Down:
            g.set_soft(True)
        elif k == Qt.Key.Key_Space:
            g.hard_drop()
        elif k in (Qt.Key.Key_Up, Qt.Key.Key_X):
            g.rotate(1)
        elif k in (Qt.Key.Key_Z, Qt.Key.Key_Control):
            g.rotate(-1)
        elif k == Qt.Key.Key_A:
            g.rotate(2)
        elif k in (Qt.Key.Key_C, Qt.Key.Key_Shift):
            g.hold_piece()
        else:
            super().keyPressEvent(ev)
            return
        self._drain_events()

    def keyReleaseEvent(self, ev) -> None:  # noqa: N802
        if ev.isAutoRepeat():
            ev.accept()
            return
        k = ev.key()
        if k == Qt.Key.Key_Left:
            self.game.release_dir(-1)
        elif k == Qt.Key.Key_Right:
            self.game.release_dir(1)
        elif k == Qt.Key.Key_Down:
            self.game.set_soft(False)
        else:
            super().keyReleaseEvent(ev)

    def focusOutEvent(self, ev) -> None:  # noqa: N802
        # 切走窗口就自动暂停：消行冻结 / 死亡动画期间也要暂停，否则切出去游戏还在自己跑
        # （toggle_pause 自己会在 dying/over 时什么都不做）
        if self.auto_pause and not self.paused and self.overlay is None:
            self.toggle_pause()
        super().focusOutEvent(ev)

    def toggle_fullscreen(self) -> None:
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    # ------------------------------------------------------------ 设置 / 鼠标
    def setting_rows(self) -> list[tuple[str, str, str]]:
        """(标题, 当前值, 说明) —— 绘制、点击、数字键都读这一份。"""
        o = self.opt
        _, das, arr = DAS_PRESETS[o["feel"]]
        return [
            ("幽灵块", "开" if o["ghost"] else "关", "落点预览"),
            ("网格线", "开" if o["grid"] else "关", "场地底纹"),
            ("音效", "开" if o["sfx"] else "关", "移动/消行"),
            ("背景音乐", "开" if o["music"] else "关", "俄罗斯民谣"),
            ("震屏", "开" if o["shake"] else "关", "硬降/消行"),
            ("手感 DAS/ARR", DAS_PRESETS[o["feel"]][0], f"{das:.3f}s / {arr:.3f}s"),
            ("起始等级", str(START_LEVELS[o["start_level"]]), "下一局生效"),
            ("螺螺头像", "开" if o["face"] else "关", f"约 {LUOLUO_RATE:.0%} 的方块"),
            ("主题", THEME_MODES[o["theme"] % len(THEME_MODES)], "跟随系统可自动换肤"),
        ]

    def cycle_setting(self, idx: int) -> None:
        rows = self.setting_rows()
        if not (0 <= idx < len(rows)):
            return
        o = self.opt
        key = ("ghost", "grid", "sfx", "music", "shake", "feel", "start_level",
               "face", "theme")[idx]
        if key == "feel":
            o["feel"] = (o["feel"] + 1) % len(DAS_PRESETS)
            self._apply_feel()
        elif key == "start_level":
            o["start_level"] = (o["start_level"] + 1) % len(START_LEVELS)
        elif key == "theme":
            o["theme"] = (o["theme"] + 1) % len(THEME_MODES)
            self.apply_theme()              # 内部按需清缓存 + 重绘
        else:
            o[key] = not o[key]
            if key == "sfx":
                self.audio.set_sfx(o["sfx"])
                if o["sfx"]:
                    self.audio.play("go", 0.5)
            elif key == "music":
                self.audio.set_music(bool(o["music"]) and not self.paused)
            elif key == "grid":
                self._bg_cache.clear()
        self.write_save(why=f'setting:{key}')
        self.update()

    def canvas_transform(self) -> tuple[float, float, float]:
        """返回 (缩放, 横向信箱边, 纵向信箱边)；绘制与鼠标换算共用一份来源。"""
        w, h = self.width(), self.height()
        s = min(w / BASE_W, h / BASE_H)
        return s, (w - BASE_W * s) / 2.0, (h - BASE_H * s) / 2.0

    def to_canvas(self, x: float, y: float) -> tuple[float, float]:
        s, ox, oy = self.canvas_transform()
        if s <= 0:
            return 0.0, 0.0
        return (x - ox) / s, (y - oy) / s

    def card_rect(self) -> QRectF:
        """当前覆盖层卡片的矩形（绘制、点击、体检共用一份）。"""
        if self.overlay == "help":
            return overlay_geom("help")
        if self.overlay == "settings":
            return overlay_geom("settings")
        if self.paused:
            return overlay_geom("pause")
        if self.game.phase == "over":
            return overlay_geom("over")
        return QRectF()

    def mousePressEvent(self, ev: QMouseEvent) -> None:  # noqa: N802
        if ev.button() != Qt.MouseButton.LeftButton:
            return
        cx, cy = self.to_canvas(ev.position().x(), ev.position().y())
        if self.overlay == "settings":
            card = self.card_rect()
            for i in range(len(self.setting_rows())):
                if setting_row_rect(card, i).contains(QPointF(cx, cy)):
                    self.cycle_setting(i)
                    return
            if not card.contains(QPointF(cx, cy)):
                self.overlay = None
                self.update()
            return
        if self.overlay == "help":
            self.overlay = None
            self.update()
            return
        if self.paused and self.card_rect().contains(QPointF(cx, cy)):
            self.toggle_pause()
            return
        if self.game.phase == "over" and self.card_rect().contains(QPointF(cx, cy)):
            self.new_game()

    def mouseMoveEvent(self, ev: QMouseEvent) -> None:  # noqa: N802
        if self.overlay != "settings":
            if self.hover_row != -1:
                self.hover_row = -1
                self.update()
            return
        cx, cy = self.to_canvas(ev.position().x(), ev.position().y())
        card = self.card_rect()
        row = -1
        for i in range(len(self.setting_rows())):
            if setting_row_rect(card, i).contains(QPointF(cx, cy)):
                row = i
                break
        if row != self.hover_row:
            self.hover_row = row
            self.update()

    def leaveEvent(self, ev) -> None:  # noqa: N802
        if self.hover_row != -1:
            self.hover_row = -1
            self.update()

    # =====================================================================
    # 文本布局：绘制与 --ui 版面体检共用这一份数据
    # =====================================================================
    def status_line(self) -> str:
        g = self.game
        tags = []
        if g.combo >= 1:
            tags.append(f"连击 ×{g.combo}")
        if g.b2b:
            tags.append("B2B")
        return " · ".join(tags) if tags else "—"

    def tip(self) -> str:
        return TIPS[int(self.t / 12) % len(TIPS)] if TIPS else ""

    def text_items(self) -> list[Txt]:
        g, o = self.game, self.opt
        items: list[Txt] = []
        black, bold = QFont.Weight.Black, QFont.Weight.DemiBold

        # ---- 顶栏
        items.append(Txt("标题", 20, 32, font(19, black, 3), "螺 螺 是 方 块", COL_TXT(), shadow=True))
        items.append(Txt("副标题", 238, 31, font(10), "SRS · 7-bag · Hold · T-Spin", COL_FAINT()))
        items.append(Txt("最高分", 680, 31, font(12, bold), f"最高分 {fmt_int(max(self.high, g.score))}",
                         COL_GOLD(), "right"))

        # ---- 左面板：Hold + 统计
        items.append(Txt("HOLD标签", 30, 68, font(10, bold, 2), "HOLD", COL_DIM()))
        items.append(Txt("HOLD提示", 166, 68, font(9), "C 暂存", COL_FAINT(), "right"))
        if g.hold is None:
            items.append(Txt("HOLD空", HOLD_BOX.center().x(), HOLD_BOX.center().y() + 5,
                             font(12), "空", COL_FAINT(), "center"))
        items.append(Txt("得分标签", 30, 216, font(10, bold, 2), "得分", COL_DIM()))
        items.append(Txt("得分值", 30, 252, font(22, black), fmt_int(g.score), COL_TXT(), shadow=True))
        for i, (k, v) in enumerate((("最高分", fmt_int(max(self.high, g.score))), ("等级", str(g.level)),
                                    ("消行", str(g.lines)), ("用时", fmt_time(g.elapsed)),
                                    ("方块", str(g.pieces)))):
            y = 288 + i * 30
            items.append(Txt(f"{k}标签", 30, y, font(10), k, COL_DIM()))
            items.append(Txt(f"{k}值", 166, y, font(13, bold, 0, FONT_MONO), v, COL_TXT(), "right"))
        items.append(Txt("状态", 30, 440, font(11, bold), self.status_line(),
                         COL_ACCENT() if g.combo >= 1 or g.b2b else COL_FAINT()))
        items.append(Txt("操作标签", 30, 472, font(10, bold, 2), "操作", COL_DIM()))
        for i, (k, d) in enumerate((("← →", "左右移动"), ("↓", "软降"), ("空格", "硬降"),
                                    ("↑ / X", "顺时针"), ("Z", "逆时针"), ("A", "旋转 180°"),
                                    ("C", "暂存 Hold"), ("P / Esc", "暂停"),
                                    ("F1 / F2", "帮助 / 设置"), ("R", "重开一局"))):
            y = 498 + i * 21
            items.append(Txt(f"键{k}", 30, y, font(10, bold, 0, FONT_MONO), k, COL_ACCENT()))
            items.append(Txt(f"说明{d}", 92, y, font(10), d, COL_DIM()))

        # ---- 右面板：Next
        items.append(Txt("NEXT标签", 534, 68, font(10, bold, 2), "NEXT", COL_DIM()))
        items.append(Txt("NEXT提示", 670, 68, font(9), "5 个预览", COL_FAINT(), "right"))
        done, need = g.lines_to_next()
        items.append(Txt("下一级标签", 534, 694, font(10), "下一级", COL_DIM()))
        items.append(Txt("下一级进度", 670, 694, font(10, bold, 0, FONT_MONO),
                         f"{done} / {need}", COL_ACCENT(), "right"))

        # ---- 场地里的小字
        items.append(Txt("出生区", 210, 90, font(9), "出生区", COL_FAINT()))
        dg = g.danger()
        if dg > 0.5 and g.phase == "play":
            pulse = 0.5 + 0.5 * math.sin(self.t * 7.0)
            warm = COL_WARN()
            warm.setAlphaF(0.45 + 0.55 * pulse)
            items.append(Txt("危险", 490, 90, font(10, bold), "危险！堆太高了", warm, "right"))

        # ---- 底栏
        items.append(Txt("底栏左", 20, 744, font(9), "F1 帮助 · F2 设置 · F11 全屏", COL_FAINT()))
        items.append(Txt("底栏右", 680, 744, font(9),
                         f"音效 {'开' if o['sfx'] else '关'} · 音乐 {'开' if o['music'] else '关'}"
                         f" · {self.fps:.0f} FPS", COL_FAINT(), "right"))
        if g.phase == "play" and not self.paused and self.overlay is None:
            items.append(Txt("底栏提示", 350, 744, font(9), self.tip(), COL('dim'), "center"))

        # ---- 覆盖层文字
        items.extend(self._overlay_texts())
        return items

    def _overlay_texts(self) -> list[Txt]:
        g = self.game
        items: list[Txt] = []
        black, bold = QFont.Weight.Black, QFont.Weight.DemiBold

        if self.overlay == "settings":
            card = overlay_geom("settings")
            cx = card.center().x()
            items.append(Txt("设置标题", cx, card.y() + 50, font(21, black, 4), "设 置", COL_TXT(), "center",
                             shadow=True))
            items.append(Txt("设置副标题", cx, card.y() + 70, font(9),
                             "改动立刻生效，最高分与设置会自动保存", COL_FAINT(), "center"))
            for i, (label, value, desc) in enumerate(self.setting_rows()):
                r = setting_row_rect(card, i)
                items.append(Txt(f"设置{i}名", r.x() + 16, r.y() + 21, font(12, bold), label, COL_TXT()))
                items.append(Txt(f"设置{i}注", r.x() + 150, r.y() + 21, font(9), desc, COL_FAINT()))
                items.append(Txt(f"设置{i}值", r.right() - 16, r.y() + 21, font(12, bold, 0, FONT_MONO),
                                 value, COL_ACCENT(), "right"))
            items.append(Txt("设置提示", cx, card.bottom() - 24, font(10),
                             f"点击一行或按 1–{len(self.setting_rows())} 切换 · F2 / Esc 关闭",
                             COL_DIM(), "center"))
            return items

        if self.overlay == "help":
            card = overlay_geom("help")
            cx = card.center().x()
            items.append(Txt("帮助标题", cx, card.y() + 52, font(21, black, 4), "键位与计分", COL_TXT(),
                             "center", shadow=True))
            items.append(Txt("帮助操作", card.x() + 28, card.y() + 90, font(10, bold, 2), "操作", COL_ACCENT()))
            left = (("← →", "左右移动"), ("↓", "软降"), ("空格", "硬降"), ("↑ / X", "顺时针"),
                    ("Z / Ctrl", "逆时针"), ("A", "旋转 180°"))
            right = (("C / Shift", "暂存 Hold"), ("P / Esc", "暂停 / 继续"), ("R", "重开一局"),
                     ("F1 / F2", "帮助 / 设置"), ("F11", "全屏切换"), ("M / B", "静音 / 音乐"))
            for col, group in enumerate((left, right)):
                x = card.x() + 28 + col * 250
                for i, (k, d) in enumerate(group):
                    y = card.y() + 120 + i * 24
                    items.append(Txt(f"帮助键{col}{i}", x, y, font(10, bold, 0, FONT_MONO), k, COL_ACCENT()))
                    items.append(Txt(f"帮助说明{col}{i}", x + 76, y, font(10), d, COL_DIM()))
            items.append(Txt("帮助计分", card.x() + 28, card.y() + 272, font(10, bold, 2),
                             "计分（基础分 × 等级）", COL_ACCENT()))
            score_lines = (
                "单消 100 · 双消 300 · 三连消 500 · 四连消 800",
                "T-Spin 400 / 单消 800 / 双消 1200 / 三连消 1600",
                "背靠背 ×1.5 · 连击 50 × n × 等级",
                "完美清除 800 / 1200 / 1800 / 2000 · 软降 1 分 · 硬降 2 分",
                "SRS 旋转 + 踢墙 · 7-bag 随机 · 锁定延迟 0.5s（最多 15 次重置）",
            )
            for i, s in enumerate(score_lines):
                items.append(Txt(f"计分行{i}", card.x() + 28, card.y() + 302 + i * 24, font(10), s, COL_DIM()))
            items.append(Txt("帮助尾", cx, card.y() + 448, font(10),
                             "最高分与设置自动保存在程序的 data 目录（zml/tetris）",
                             COL_FAINT(), "center"))
            items.append(Txt("帮助关闭", cx, card.bottom() - 24, font(10),
                             "F1 / Esc 关闭 · 点卡片外也能关", COL_DIM(), "center"))
            return items

        if self.paused and self.overlay is None:
            card = overlay_geom("pause")
            cx = card.center().x()
            items.append(Txt("暂停标题", cx, card.y() + 64, font(24, black, 6), "暂 停", COL_TXT(),
                             "center", shadow=True))
            items.append(Txt("暂停提示", cx, card.y() + 108, font(11),
                             "P / Esc 继续 · 空格 继续 · R 重开 · Q 退出", COL_DIM(), "center"))
            items.append(Txt("暂停提示2", cx, card.y() + 136, font(10),
                             "F1 帮助 · F2 设置", COL_FAINT(), "center"))
            return items

        if self.overlay is None and g.phase == "over":
            card = overlay_geom("over")
            cx = card.center().x()
            items.append(Txt("结束标题", cx, card.y() + 58, font(26, black, 6), "游戏结束", COL_TXT(),
                             "center", shadow=True))
            reason = {"block out": "新方块出生位被占（Block Out）",
                      "lock out": "方块锁在出生区上方（Lock Out）"}.get(g.dead_reason, g.dead_reason)
            items.append(Txt("结束原因", cx, card.y() + 84, font(10), reason, COL_DIM(), "center"))
            items.append(Txt("结束得分标签", cx, card.y() + 120, font(11, bold, 3), "本局得分", COL_DIM(),
                             "center"))
            items.append(Txt("结束得分", cx, card.y() + 164, font(34, black, 2), fmt_int(g.score),
                             COL_GOLD(), "center", shadow=True))
            if self.new_record:
                items.append(Txt("新纪录", cx, card.y() + 192, font(12, bold, 3), "★ 新纪录 ★",
                                 QColor(255, 240, 180), "center"))
            pairs = (("消行", str(g.lines)), ("四连消", str(g.stats["tetris"])),
                     ("等级", str(g.level)), ("T-Spin", str(g.stats["tspin"] + g.stats["tspin_mini"])),
                     ("方块数", str(g.pieces)), ("最长连击", str(g.stats["combo_max"])),
                     ("用时", fmt_time(g.elapsed)), ("完美清除", str(g.stats["perfect"])),
                     ("速度 PPS", f"{g.pps():.2f}"), ("最高分", fmt_int(self.high)))
            for i, (k, v) in enumerate(pairs):
                x = card.x() + 40 + (i % 2) * 210
                y = card.y() + 240 + (i // 2) * 30
                items.append(Txt(f"统计{k}标签", x, y, font(11), k, COL_DIM()))
                items.append(Txt(f"统计{k}值", x + 168, y, font(12, bold, 0, FONT_MONO), v, COL_TXT(),
                                 "right"))
            items.append(Txt("结束提示", cx, card.y() + 430, font(11),
                             "R / 空格 再来一局 · Esc / Q 退出", COL_DIM(), "center"))
            return items
        return items

    # =====================================================================
    # 绘制
    # =====================================================================
    def paintEvent(self, ev) -> None:  # noqa: N802
        w, h = self.width(), self.height()
        pr = QPainter(self)
        pr.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pr.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        pr.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        pr.drawPixmap(QPointF(0.0, 0.0), self._window_bg_pixmap())

        s, ox, oy = self.canvas_transform()
        dpr = self.devicePixelRatioF()
        pr.translate(round(ox * dpr) / dpr, round(oy * dpr) / dpr)
        pr.scale(s, s)
        scale = s * dpr

        pr.drawPixmap(QPointF(0.0, 0.0), self._chrome_pixmap(scale))
        self._draw_hold(pr, scale)
        self._draw_next(pr, scale)
        self._draw_progress(pr)
        self._draw_field(pr, scale)
        # 面板文字先画，覆盖层的蒙版与卡片压在上面，最后再画覆盖层自己的文字
        items = self.text_items()
        for item in items:
            if not item.name.startswith(OVERLAY_PREFIX):
                self._draw_text(pr, item)
        self._draw_overlay_cards(pr)
        for item in items:
            if item.name.startswith(OVERLAY_PREFIX):
                self._draw_text(pr, item)
        self._draw_toasts(pr)
        if self.flash > 0.0:
            # 震屏闪光：深色主题下是"白闪"，浅色主题下必须改成"黑闪" ——
            # 白底上再叠白是看不见的（这正是极性反转最容易漏的一处）。
            c = QColor(255, 255, 255) if _Palette.dark else QColor(0, 0, 0)
            c.setAlphaF(min(0.5, self.flash * 0.45) * (1.0 if _Palette.dark else 0.6))
            pr.fillRect(QRectF(0, 0, BASE_W, BASE_H), c)
        pr.end()

    def _draw_text(self, pr: QPainter, item: Txt) -> None:
        x, y = place_text(item)
        pr.setFont(item.font)
        if item.shadow:
            # 文字描边：深色下用黑影压住亮字，浅色下用白影托住暗字。
            shadow = QColor(0, 0, 0, 170) if _Palette.dark else QColor(255, 255, 255, 210)
            pr.setPen(shadow)
            pr.drawText(QPointF(x + 1.2, y + 1.2), item.text)
        pr.setPen(item.color)
        pr.drawText(QPointF(x, y), item.text)

    # ---------------------------------------------------------------- 框架
    def _window_bg_pixmap(self) -> QPixmap:
        """整窗底色渐变（信箱边也要好看）缓存成一张贴图，省掉每帧 210 万像素的渐变填充。"""
        w, h = max(1, self.width()), max(1, self.height())
        px, py = max(1, int(round(w * self.devicePixelRatioF()))), \
                 max(1, int(round(h * self.devicePixelRatioF())))
        ck = (px, py)
        pm = self._wbg_cache.get(ck)
        if pm is None:
            if len(self._wbg_cache) > 6:
                self._wbg_cache.clear()
            pm = QPixmap(px, py)
            bg = QRadialGradient(QPointF(px / 2.0, py * 0.34), max(px, py) * 0.8)
            bg.setColorAt(0.0, COL_BG0())
            bg.setColorAt(1.0, COL_BG1())
            bp = QPainter(pm)
            bp.fillRect(QRectF(0, 0, px, py), QBrush(bg))
            bp.end()
            pm.setDevicePixelRatio(px / float(w))
            self._wbg_cache[ck] = pm
        return pm

    def _chrome_pixmap(self, scale: float) -> QPixmap:
        """顶栏/底栏/面板卡/HOLD/NEXT 槽底/进度条轨道都是静态的，整层缓存成一张贴图。

        实测：这一层每帧重画要 ~5ms（十几个带抗锯齿的圆角矩形），缓存后只剩一次 blit。
        """
        q = max(0.5, scale)
        px, py = max(1, int(round(BASE_W * q))), max(1, int(round(BASE_H * q)))
        ck = (px, py)
        pm = self._chrome_cache.get(ck)
        if pm is None:
            if len(self._chrome_cache) > 8:
                self._chrome_cache.clear()
            pm = QPixmap(px, py)
            pm.fill(Qt.GlobalColor.transparent)
            cp = QPainter(pm)
            cp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            cp.scale(q, q)
            self._draw_chrome(cp)
            self._paint_panel_slots(cp)
            self._paint_field_frame(cp)
            cp.end()
            pm.setDevicePixelRatio(px / float(BASE_W))
            self._chrome_cache[ck] = pm
        return pm

    def _draw_chrome(self, pr: QPainter) -> None:
        head = QRectF(0, 0, BASE_W, HEADER_BOTTOM)
        g = QLinearGradient(head.topLeft(), head.bottomLeft())
        g.setColorAt(0.0, COL('bar0'))
        g.setColorAt(1.0, COL('bar1'))
        pr.setPen(Qt.PenStyle.NoPen)
        pr.setBrush(QBrush(g))
        pr.drawRect(head.adjusted(0, -HEADER_BOTTOM, 0, 0))
        pr.setPen(QPen(COL('bar_line', 150), 1))
        pr.drawLine(QPointF(0, HEADER_BOTTOM - 0.5), QPointF(BASE_W, HEADER_BOTTOM - 0.5))

        foot = QRectF(0, FOOTER_TOP, BASE_W, BASE_H - FOOTER_TOP)
        bar1_lo = COL('bar1').darker(150) if _Palette.dark else COL('bar1').lighter(104)
        g2 = QLinearGradient(foot.topLeft(), foot.bottomLeft())
        g2.setColorAt(0.0, COL('bar1'))
        g2.setColorAt(1.0, bar1_lo)
        pr.setBrush(QBrush(g2))
        pr.setPen(Qt.PenStyle.NoPen)
        pr.drawRect(foot)
        pr.setPen(QPen(COL('bar_line', 130), 1))
        pr.drawLine(QPointF(0, FOOTER_TOP + 0.5), QPointF(BASE_W, FOOTER_TOP + 0.5))

        for rect in (PANEL_L, PANEL_R):
            pr.setPen(Qt.PenStyle.NoPen)
            pr.setBrush(SHADOW(90))
            pr.drawRoundedRect(rect.adjusted(-3, 3, 3, 9), 16, 16)
            pg = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            pg.setColorAt(0.0, COL_PANEL_HI())
            pg.setColorAt(1.0, COL_PANEL())
            pr.setBrush(QBrush(pg))
            pr.setPen(QPen(COL_PANEL_LINE(), 1.3))
            pr.drawRoundedRect(rect, 14, 14)
            pr.setPen(QPen(EDGE(22), 1))
            pr.drawLine(QPointF(rect.left() + 14, rect.top() + 1.5),
                        QPointF(rect.right() - 14, rect.top() + 1.5))

    def _paint_panel_slots(self, pr: QPainter) -> None:
        """HOLD 框、5 个 NEXT 槽、进度条轨道：内容不变，跟着 _chrome_pixmap 一起缓存。"""
        self._slot_bg(pr, HOLD_BOX, 235)
        for i in range(5):
            slot = QRectF(NEXT_BOX.x(), NEXT_BOX.y() + i * NEXT_SLOT_H, NEXT_BOX.width(),
                          NEXT_SLOT_H - 8)
            self._slot_bg(pr, slot, alpha=235 if i == 0 else 210, glow=i == 0)
            if i == 0:
                pr.setPen(Qt.PenStyle.NoPen)
                pr.setBrush(COL_ACCENT())
                pr.drawRoundedRect(QRectF(slot.x() + 3, slot.center().y() - 12, 3, 24), 1.5, 1.5)
        pr.setPen(Qt.PenStyle.NoPen)
        pr.setBrush(COL('field0'))
        pr.drawRoundedRect(PROGRESS_BAR, 5, 5)
        pr.setBrush(Qt.BrushStyle.NoBrush)
        pr.setPen(QPen(COL('panel_line', 160), 1))
        pr.drawRoundedRect(PROGRESS_BAR, 5, 5)

    def _slot_bg(self, pr: QPainter, rect: QRectF, alpha: int = 255, glow: bool = False) -> None:
        pr.setPen(Qt.PenStyle.NoPen)
        pr.setBrush(SHADOW(70))
        pr.drawRoundedRect(rect.adjusted(-1, 2, 1, 5), 10, 10)
        base = COL('field1') if _Palette.dark else COL('slot')
        col = QColor(base.red(), base.green(), base.blue(), alpha)
        pr.setBrush(col)
        pr.setPen(QPen(COL('panel_line', 120), 1.1))
        pr.drawRoundedRect(rect, 10, 10)
        if glow:
            gg = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            accent = COL('accent')
            gg.setColorAt(0.0, QColor(accent.red(), accent.green(), accent.blue(), 34))
            gg.setColorAt(1.0, QColor(accent.red(), accent.green(), accent.blue(), 0))
            pr.setPen(Qt.PenStyle.NoPen)
            pr.setBrush(QBrush(gg))
            pr.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 9, 9)

    def _piece_preview(self, pr: QPainter, kind: str, slot: QRectF, cell: float, scale: float,
                       alpha: float = 1.0, mode: str = "solid") -> None:
        minx, miny, maxx, maxy = piece_bounds(kind)
        w = (maxx - minx + 1) * cell
        h = (maxy - miny + 1) * cell
        ox = slot.center().x() - w / 2.0
        oy = slot.center().y() - h / 2.0
        if alpha < 0.999:
            pr.save()
            pr.setOpacity(max(0.05, alpha))
        for (cx, cy) in ROTATIONS[kind][0]:
            r = QRectF(ox + (cx - minx) * cell + 1, oy + (cy - miny) * cell + 1, cell - 2, cell - 2)
            draw_pm(pr, block_pixmap(kind, cell - 2, mode, scale), r)
        if alpha < 0.999:
            pr.restore()

    def _draw_hold(self, pr: QPainter, scale: float) -> None:
        """槽底在 _chrome_pixmap 里，这里只画会变的：暂存方块与闪光。"""
        g = self.game
        if g.hold is not None:
            self._piece_preview(pr, g.hold, HOLD_BOX, PREVIEW_CELL, scale,
                                alpha=0.4 if g.hold_used else 1.0)
        if self.hold_flash > 0.0:
            c = COL_ACCENT()
            c.setAlphaF(min(1.0, self.hold_flash / 0.3) * 0.5)
            pr.setPen(QPen(c, 2.0))
            pr.setBrush(Qt.BrushStyle.NoBrush)
            pr.drawRoundedRect(HOLD_BOX, 10, 10)

    def _draw_next(self, pr: QPainter, scale: float) -> None:
        g = self.game
        queue = g.expect_queue()
        for i in range(5):
            slot = QRectF(NEXT_BOX.x(), NEXT_BOX.y() + i * NEXT_SLOT_H, NEXT_BOX.width(),
                          NEXT_SLOT_H - 8)
            if i < len(queue):
                self._piece_preview(pr, queue[i], slot, PREVIEW_CELL, scale,
                                    alpha=(1.0, 0.86, 0.74, 0.64, 0.56)[i])

    def _draw_progress(self, pr: QPainter) -> None:
        g = self.game
        done, need = g.lines_to_next()
        frac = done / float(need) if need else 0.0
        if frac <= 0:
            return
        fill = QRectF(PROGRESS_BAR.x(), PROGRESS_BAR.y(), max(4.0, PROGRESS_BAR.width() * frac),
                      PROGRESS_BAR.height())
        lg = QLinearGradient(fill.topLeft(), fill.topRight())
        lg.setColorAt(0.0, COL('accent'))
        lg.setColorAt(1.0, COL('good'))
        pr.setPen(Qt.PenStyle.NoPen)
        pr.setBrush(QBrush(lg))
        pr.drawRoundedRect(fill, 5, 5)

    # ---------------------------------------------------------------- 场地
    def cell_rect(self, c: int, y: int) -> QRectF:
        """格坐标（含出生区，y 从场地顶部数）→ 画布矩形。"""
        return QRectF(FIELD_X + c * CELL + 1, FIELD_Y + (y - BUFFER_ROWS) * CELL + 1, CELL - 2, CELL - 2)

    def cell_center(self, c: float, y: float) -> tuple[float, float]:
        return (FIELD_X + (c + 0.5) * CELL, FIELD_Y + (y - BUFFER_ROWS + 0.5) * CELL)

    def _field_bg(self, scale: float) -> QPixmap:
        return cached_pixmap(self._bg_cache, ("field", bool(self.opt["grid"])),
                             FIELD_W, FIELD_H + BUFFER_ROWS * CELL, scale, self._paint_field_bg)

    def _paint_field_bg(self, pr: QPainter) -> None:
        w, h = FIELD_W, FIELD_H + BUFFER_ROWS * CELL
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, COL('field0'))
        grad.setColorAt(0.42, COL('field1'))
        grad.setColorAt(1.0, COL('field2'))
        pr.setPen(Qt.PenStyle.NoPen)
        pr.setBrush(QBrush(grad))
        pr.drawRect(QRectF(0, 0, w, h))

        grid = bool(self.opt["grid"])
        cell_bg = COL_SLOT() if grid else COL('slot_off')
        for y in range(GRID_ROWS):
            for c in range(FIELD_COLS):
                pr.setBrush(cell_bg)
                pr.setPen(Qt.PenStyle.NoPen)
                pr.drawRoundedRect(QRectF(c * CELL + 1, y * CELL + 1, CELL - 2, CELL - 2), 5, 5)
        if grid:
            pr.setPen(QPen(EDGE(12), 1))
            for c in range(1, FIELD_COLS):
                pr.drawLine(QPointF(c * CELL, 0), QPointF(c * CELL, h))
            for y in range(1, GRID_ROWS):
                pr.drawLine(QPointF(0, y * CELL), QPointF(w, y * CELL))

        # 出生区：压暗 + 斜纹，一眼能看出"这两行不是场地"
        strip_h = BUFFER_ROWS * CELL
        pr.setPen(Qt.PenStyle.NoPen)
        pr.setBrush(SHADOW(70))
        pr.drawRect(QRectF(0, 0, w, strip_h))
        pr.setPen(QPen(EDGE(10), 1))
        for x in range(-strip_h, int(w) + strip_h, 16):
            pr.drawLine(QPointF(x, strip_h), QPointF(x + strip_h, 0))
        pr.setPen(QPen(COL('dim', 70), 1, Qt.PenStyle.DashLine))
        pr.drawLine(QPointF(0, strip_h + 0.5), QPointF(w, strip_h + 0.5))

    def _paint_field_frame(self, pr: QPainter) -> None:
        """场地外框（阴影 + 槽体）：静态，跟 chrome 一起缓存；震屏时只有内容在抖。"""
        fr = FRAME
        pr.setPen(Qt.PenStyle.NoPen)
        pr.setBrush(SHADOW(120))
        pr.drawRoundedRect(fr.adjusted(-3, 5, 3, 13), 18, 18)
        fg = QLinearGradient(fr.topLeft(), fr.bottomLeft())
        fg.setColorAt(0.0, COL('frame0'))
        fg.setColorAt(1.0, COL('frame1'))
        pr.setBrush(QBrush(fg))
        pr.setPen(QPen(COL_PANEL_LINE(), 1.4))
        pr.drawRoundedRect(fr, 14, 14)

    def _draw_field(self, pr: QPainter, scale: float) -> None:
        g = self.game
        dx, dy = self.shake_offset()
        field = QRectF(FIELD_X, STRIP_TOP, FIELD_W, FIELD_H + BUFFER_ROWS * CELL)
        pr.save()
        pr.translate(dx, dy)

        pr.save()
        clip = QPainterPath()
        clip.addRoundedRect(field, 6, 6)
        pr.setClipPath(clip)
        draw_pm(pr, self._field_bg(scale), field)
        self._draw_trails(pr)
        self._draw_stack(pr, scale)
        self._draw_clear_fx(pr, scale)
        self._draw_active(pr, scale)
        self._draw_particles(pr)
        self._draw_banner(pr)
        pr.restore()

        dg = g.danger()
        if dg > 0.02:
            pulse = 0.5 + 0.5 * math.sin(self.t * 5.0)
            c = COL_WARN()
            c.setAlphaF(min(0.8, dg * (0.30 + 0.70 * pulse)))
            pr.setPen(QPen(c, 2.4))
            pr.setBrush(Qt.BrushStyle.NoBrush)
            pr.drawRoundedRect(FRAME.adjusted(0.6, 0.6, -0.6, -0.6), 14, 14)
        pr.restore()

    def _draw_stack(self, pr: QPainter, scale: float) -> None:
        """已固定的方块整体缓存成一张贴图：只有锁定/消行/结算动画会改变盘面。"""
        g = self.game
        # ⚠️ key 里带上「螺螺头像」开关：关掉它必须立刻让**已缓存**的堆叠贴图失效，
        #    否则那张图里还糊着上一帧画好的头像，要等盘面变了才消失。
        key = (g.board_signature(), tuple(g.clear_rows), self.opt.get("face", True))
        q = max(0.5, scale)
        w, h = FIELD_W, FIELD_H + BUFFER_ROWS * CELL
        px, py = max(1, int(round(w * q))), max(1, int(round(h * q)))
        ck = (key, px, py)
        pm = self._stack_cache.get(ck)
        if pm is None:
            # 只留当前这一张：整层贴图 600x1320@2x 约 3MB，留十几张就是几十 MB 白占着
            self._stack_cache.clear()
            pm = QPixmap(px, py)
            pm.fill(Qt.GlobalColor.transparent)
            sp = QPainter(pm)
            sp.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            sp.scale(q, q)
            self._paint_stack(sp, scale)
            sp.end()
            pm.setDevicePixelRatio(px / float(w))
            self._stack_cache[ck] = pm
        pr.drawPixmap(QPointF(FIELD_X, STRIP_TOP), pm)

    @staticmethod
    def _face_rect(r: QRectF) -> QRectF:
        """头像在方块里占的矩形：居中、比方块小一圈.

        ⚠️ 留出这一圈是**有意的**：底下那层彩色方块会露出来当描边，这样即使照片
        偏暗，这一格在场地里也依然看得清轮廓（否则深色头像会糊成一个洞）。
        """
        pad = max(1.0, (CELL - 2) * 0.10)
        return r.adjusted(pad, pad, -pad, -pad)

    def _paint_stack(self, pr: QPainter, scale: float) -> None:
        """在设计坐标里画已固定方块，原点 = (FIELD_X, STRIP_TOP)，跳过正在闪的消行。"""
        g = self.game
        clearing = set(g.clear_rows)
        on = self.opt.get("face", True)
        face = luoluo_pixmap(CELL - 2, scale) if (on and g.faces) else None
        for y in range(g.stack_top(), GRID_ROWS):
            if y in clearing:
                continue
            row = g.grid[y]
            for c in range(FIELD_COLS):
                v = row[c]
                if not v:
                    continue
                kind = "dead" if v == DEAD_ID else ID_KIND.get(v, "I")
                r = QRectF(c * CELL + 1, y * CELL + 1, CELL - 2, CELL - 2)
                draw_pm(pr, block_pixmap(kind, CELL - 2, "solid", scale), r)
                # 彩蛋：落定后依然显示头像（见 Game.faces）
                if face is not None and (c, y) in g.faces:
                    draw_pm(pr, face, self._face_rect(r))

    def _draw_trails(self, pr: QPainter) -> None:
        for tr in self.trails:
            a = max(0.0, 1.0 - tr["t"] / tr["life"])
            x = FIELD_X + tr["c"] * CELL
            y0 = FIELD_Y + (tr["r0"] - BUFFER_ROWS) * CELL
            y1 = FIELD_Y + (tr["r1"] - BUFFER_ROWS + 1) * CELL
            gg = QLinearGradient(0, y0, 0, y1)
            gg.setColorAt(0.0, QColor(255, 255, 255, 0))
            gg.setColorAt(1.0, QColor(190, 210, 255, int(90 * a)))
            pr.setPen(Qt.PenStyle.NoPen)
            pr.setBrush(QBrush(gg))
            pr.drawRect(QRectF(x + 2, y0, CELL - 4, max(1.0, y1 - y0)))

    def _draw_active(self, pr: QPainter, scale: float) -> None:
        g = self.game
        a = g.active
        if a is None or g.phase not in ("play", "dying"):
            return
        kind = a["kind"]
        if self.opt["ghost"] and g.phase == "play":
            gy = g.ghost_y()
            if gy != a["y"]:
                for cx, cy in ROTATIONS[kind][a["rot"]]:
                    y = gy + cy
                    if y < 0:
                        continue
                    draw_pm(pr, block_pixmap(kind, CELL - 2, "ghost", scale),
                            self.cell_rect(a["x"] + cx, y))

        lockp = min(1.0, g.lock_timer / LOCK_DELAY) if (g.grounded and g.phase == "play") else 0.0
        glow = min(1.0, a.get("glow", 0.0) / SPAWN_GLOW)
        # 彩蛋：这一块有螺螺的头像吗；有的话**只贴一格**（a["face_i"]，见 _spawn_kind）
        face = (luoluo_pixmap(CELL - 2, scale)
                if (a.get("luoluo") and self.opt.get("face", True)) else None)
        face_i = a.get("face_i", -1)
        for i, (cx, cy) in enumerate(ROTATIONS[kind][a["rot"]]):
            y = a["y"] + cy
            if y < 0:
                continue
            r = self.cell_rect(a["x"] + cx, y)
            if glow > 0.01:
                halo = QColor(PIECE_COLORS[kind])
                halo.setAlphaF(0.30 * glow)
                pr.setPen(Qt.PenStyle.NoPen)
                pr.setBrush(halo)
                pr.drawRoundedRect(r.adjusted(-5, -5, 5, 5), 10, 10)
            draw_pm(pr, block_pixmap(kind, CELL - 2, "solid", scale), r)
            if face is not None and i == face_i:
                draw_pm(pr, face, self._face_rect(r))
            if lockp > 0.55:
                w = QColor(255, 255, 255)
                blink = 0.6 + 0.4 * math.sin(self.t * 34.0)
                w.setAlphaF((lockp - 0.55) / 0.45 * 0.42 * blink)
                pr.setPen(Qt.PenStyle.NoPen)
                pr.setBrush(w)
                pr.drawRoundedRect(r, 6, 6)
        if g.grounded and g.lock_resets >= LOCK_RESET_MAX and g.phase == "play":
            amber = COL_GOLD()
            amber.setAlphaF(0.35 + 0.25 * math.sin(self.t * 12.0))
            pr.setPen(QPen(amber, 2.0))
            pr.setBrush(Qt.BrushStyle.NoBrush)
            for cx, cy in ROTATIONS[kind][a["rot"]]:
                y = a["y"] + cy
                if y >= 0:
                    pr.drawRoundedRect(self.cell_rect(a["x"] + cx, y).adjusted(-2, -2, 2, 2), 8, 8)

    def _draw_clear_fx(self, pr: QPainter, scale: float) -> None:
        g = self.game
        if g.phase != "clear" or not g.clear_rows:
            return
        p = min(1.0, g.clear_t / CLEAR_TIME)
        for y in g.clear_rows:
            top = FIELD_Y + (y - BUFFER_ROWS) * CELL
            band = QColor(255, 255, 255)
            band.setAlphaF(0.50 * (1.0 - p) ** 0.7)
            pr.setPen(Qt.PenStyle.NoPen)
            pr.setBrush(band)
            pr.drawRect(QRectF(FIELD_X, top, FIELD_W, CELL))
            pr.save()
            pr.setOpacity(max(0.0, 1.0 - p * 0.9))
            for c in range(FIELD_COLS):
                v = g.grid[y][c]
                kind = "dead" if v == DEAD_ID else ID_KIND.get(v, "I")
                shrink = p * 0.85
                w = CELL * (1.0 - shrink)
                r = QRectF(FIELD_X + c * CELL + (CELL - w) / 2.0, top + 1 + shrink * 5, w,
                           CELL - 2 - shrink * 10)
                draw_pm_scaled(pr, block_pixmap(kind, CELL - 2, "flash", scale), r)
            pr.restore()

    def _draw_particles(self, pr: QPainter) -> None:
        for p in self.particles:
            a = max(0.0, min(1.0, p["life"] / p["max"]))
            col = QColor(p["color"])
            col.setAlphaF(a * 0.95)
            size = max(0.6, p["size"] * (0.35 + 0.65 * a))
            pen = QPen(col, size)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pr.setPen(pen)
            pr.drawLine(QPointF(p["x"], p["y"]),
                        QPointF(p["x"] - p["vx"] * 0.022, p["y"] - p["vy"] * 0.022))

    def _draw_banner(self, pr: QPainter) -> None:
        b = self.banner
        if not b:
            return
        p = min(1.0, b["t"] / b["life"])
        appear = min(1.0, b["t"] / 0.10)
        fade = 1.0 if p < 0.72 else max(0.0, (1.0 - p) / 0.28)
        alpha = appear * fade
        if alpha <= 0.01:
            return
        cy = FIELD_Y + FIELD_H * 0.32 - (1.0 - fade) * 12.0
        sub = b.get("sub") or ""
        bar = QRectF(FIELD_X + 8, cy - 28, FIELD_W - 16, 52 if sub else 42)
        pr.setPen(Qt.PenStyle.NoPen)
        # 横幅压在场地之上：底衬跟着主题走（深色下是近黑，浅色下是近白），
        # 否则浅色场地中央会突兀地坐着一块黑板。
        import_bg = COL('banner')
        pr.setBrush(QColor(import_bg.red(), import_bg.green(), import_bg.blue(), int(168 * alpha)))
        pr.drawRoundedRect(bar, 12, 12)
        pr.setBrush(QColor(b["color"].red(), b["color"].green(), b["color"].blue(), int(30 * alpha)))
        pr.drawRoundedRect(bar, 12, 12)

        # 字号随内容自适应：横幅不能超出场地宽度
        size = int(22 * (0.90 + 0.10 * appear))
        f = font(size, QFont.Weight.Black, 2)
        while size > 11 and QFontMetrics(f).horizontalAdvance(b["text"]) > bar.width() - 20:
            size -= 1
            f = font(size, QFont.Weight.Black, 2)
        pr.setFont(f)
        rect = QRectF(bar.x(), bar.y() + 4, bar.width(), 30)
        # 主文字描边：深色底衬上描黑，浅色底衬上描白
        halo = QColor(0, 0, 0, int(190 * alpha)) if _Palette.dark else \
            QColor(255, 255, 255, int(200 * alpha))
        pr.setPen(halo)
        pr.drawText(rect.adjusted(1.5, 1.5, 1.5, 1.5), Qt.AlignmentFlag.AlignCenter, b["text"])
        col = QColor(b["color"])
        col.setAlphaF(alpha)
        pr.setPen(col)
        pr.drawText(rect, Qt.AlignmentFlag.AlignCenter, b["text"])
        if sub:
            f2 = font(11, QFont.Weight.DemiBold, 1)
            pr.setFont(f2)
            col2 = COL_TXT()
            col2.setAlphaF(alpha * 0.9)
            pr.setPen(col2)
            pr.drawText(QRectF(bar.x(), bar.y() + 30, bar.width(), 20),
                        Qt.AlignmentFlag.AlignCenter, sub)

    def _draw_toasts(self, pr: QPainter) -> None:
        for s in self.toasts:
            p = min(1.0, s["t"] / s["life"])
            alpha = max(0.0, 1.0 - p * p)
            f = font(s["size"], QFont.Weight.Black, 1)
            pr.setFont(f)
            w = QFontMetrics(f).horizontalAdvance(s["text"])
            x = s["x"] - w / 2.0
            col = QColor(s["color"])
            col.setAlphaF(alpha)
            pr.setPen(QColor(0, 0, 0, int(190 * alpha)))
            pr.drawText(QPointF(x + 1.5, s["y"] + 1.5), s["text"])
            pr.setPen(col)
            pr.drawText(QPointF(x, s["y"]), s["text"])

    # ---------------------------------------------------------------- 覆盖层
    def _draw_overlay_cards(self, pr: QPainter) -> None:
        kind = ("settings" if self.overlay == "settings" else
                "help" if self.overlay == "help" else
                "pause" if self.paused else
                "over" if self.game.phase == "over" else None)
        if kind is None:
            return
        pr.setPen(Qt.PenStyle.NoPen)
        veil = COL('veil')
        pr.setBrush(QColor(veil.red(), veil.green(), veil.blue(), 190 if _Palette.dark else 205))
        pr.drawRect(QRectF(0, 0, BASE_W, BASE_H))

        card = overlay_geom(kind)
        pr.setBrush(SHADOW(150))
        pr.drawRoundedRect(card.adjusted(-5, 9, 5, 20), 24, 24)
        cg = QLinearGradient(card.topLeft(), card.bottomLeft())
        cg.setColorAt(0.0, COL('card0'))
        cg.setColorAt(1.0, COL('card1'))
        pr.setBrush(QBrush(cg))
        pr.setPen(QPen(COL('card_line'), 1.6))
        pr.drawRoundedRect(card, 18, 18)
        pr.setPen(Qt.PenStyle.NoPen)
        accent = COL_ACCENT() if kind != "over" else COL_GOLD()
        pr.setBrush(accent)
        pr.drawRoundedRect(QRectF(card.x() + 20, card.y() + 9, card.width() - 40, 3), 1.5, 1.5)

        if kind == "settings":
            hot_line = COL('accent', 130)
            hot_fill = COL('accent', 46)
            for i in range(len(self.setting_rows())):
                r = setting_row_rect(card, i)
                hot = i == self.hover_row
                pr.setPen(QPen(hot_line if hot else EDGE(22), 1))
                pr.setBrush(hot_fill if hot else EDGE(14))
                pr.drawRoundedRect(r, 9, 9)
                pr.setPen(Qt.PenStyle.NoPen)
                pr.setBrush(COL('accent', 170) if hot else COL('dim', 90))
                pr.drawRoundedRect(QRectF(r.x() + 6, r.center().y() - 7, 3, 14), 1.5, 1.5)
        elif kind == "over":
            pr.setPen(QPen(EDGE(26), 1))
            pr.drawLine(QPointF(card.x() + 30, card.y() + 210),
                        QPointF(card.right() - 30, card.y() + 210))

    def resizeEvent(self, ev) -> None:  # noqa: N802
        # 尺寸变了，所有按物理像素烘的贴图都要重做（含头像 —— 它的键是 px）。
        self._reset_caches()
        clear_luoluo_cache()
        super().resizeEvent(ev)


# =============================================================================
# 9. 绘制基础设施
# =============================================================================

def cached_pixmap(cache: dict, key, w: float, h: float, scale: float, paint) -> QPixmap:
    """按 (key, 物理尺寸) 缓存贴图；paint 里按设计坐标画，缩放交给这里。"""
    q = max(0.5, scale)
    px, py = max(1, int(round(w * q))), max(1, int(round(h * q)))
    ck = (key, px, py)
    pm = cache.get(ck)
    if pm is None:
        if len(cache) > 8:                 # 每张都是整块场地大小，别攒太多
            cache.clear()
        pm = QPixmap(px, py)
        pm.fill(Qt.GlobalColor.transparent)
        pr = QPainter(pm)
        pr.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pr.scale(q, q)
        paint(pr)
        pr.end()
        pm.setDevicePixelRatio(px / float(w))
        cache[ck] = pm
    return pm


def draw_pm(pr: QPainter, pm: QPixmap, rect: QRectF) -> None:
    """1:1 快路径：贴图自带 devicePixelRatio，按逻辑左上角直接贴。"""
    pr.drawPixmap(rect.topLeft(), pm)


def draw_pm_scaled(pr: QPainter, pm: QPixmap, rect: QRectF) -> None:
    """需要缩放（消行动画的收缩）时走平滑路径。"""
    pr.drawPixmap(rect, pm, QRectF(0, 0, pm.width(), pm.height()))


def piece_bounds(kind: str, rot: int = 0) -> tuple[int, int, int, int]:
    """方块在包围盒里的 (minx, miny, maxx, maxy)，用于预览居中。"""
    cells = ROTATIONS[kind][rot % 4]
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    return min(xs), min(ys), max(xs), max(ys)


def overlay_geom(kind: str) -> QRectF:
    """各类覆盖层卡片的设计坐标（居中）。

    ⚠️ **settings 的高度必须跟着设置行数走**：行高 38、首行从卡片顶 84 起，末尾还要
    给"点击一行…"那行提示留位置。9 行时需要 84 + 9*38 + 约 40 = 466 —— 原先写死 420
    （只够 8 行），第 9 行会正好顶到卡片底、把提示文字压住（`ui_check` 会报
    「设置提示 与 设置8名 重叠」）。这里按行数**算**出来，以后再加设置项就不用
    再想一遍这件事。
    """
    rows = len(DEFAULT_OPT) if kind == "settings" else 0
    settings_h = 84 + rows * 38 + 46
    return {
        "pause": QRectF(170, 296, 360, 168),
        # 垂直居中：卡片变高时上下一起长，别只往下坠
        "settings": QRectF(120, (BASE_H - settings_h) / 2.0, 460, settings_h),
        "help": QRectF(88, 118, 524, 524),
        "over": QRectF(112, 138, 476, 484),
    }.get(kind, QRectF(150, 250, 400, 260))


def setting_row_rect(card: QRectF, i: int) -> QRectF:
    return QRectF(card.x() + 20, card.y() + 84 + i * 38, card.width() - 40, 32)


def make_window_icon() -> QIcon:
    """程序化画一个图标：深色圆角底 + 一个 T 块。

    ⚠️ 这个图标**刻意不跟随主题**：它画在标签栏/任务栏上，底色由宿主的样式表决定，
    而不是由游戏自己的场地决定。用固定深色底 + 亮紫块，在浅色和深色标签栏上都看得清；
    若跟着主题走，浅色主题下会得到一个"白底白块"的空图标。
    """
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    pr = QPainter(pm)
    pr.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    bg = QLinearGradient(0, 0, 0, 64)
    bg.setColorAt(0.0, QColor(46, 52, 78))
    bg.setColorAt(1.0, QColor(18, 20, 30))
    pr.setPen(QPen(QColor(90, 100, 130), 2))
    pr.setBrush(QBrush(bg))
    pr.drawRoundedRect(QRectF(2, 2, 60, 60), 12, 12)
    cells = ((1, 0), (0, 1), (1, 1), (2, 1))
    for (cx, cy) in cells:
        r = QRectF(8 + cx * 16, 8 + cy * 16, 16, 16)
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0.0, PIECE_COLORS["T"].lighter(130))
        g.setColorAt(1.0, PIECE_COLORS["T"].darker(150))
        pr.setPen(Qt.PenStyle.NoPen)
        pr.setBrush(QBrush(g))
        pr.drawRoundedRect(r.adjusted(1, 1, -1, -1), 3, 3)
    pr.end()
    return QIcon(pm)


TIPS = (
    "幽灵块显示落点，C 键暂存方块",
    "四连消 800 分，背靠背再 ×1.5",
    "T-Spin 要 T 块旋转后四角占三个",
    "软降 1 分/格，硬降 2 分/格",
    "锁定延迟 0.5 秒，最多推迟 15 次",
    "完美清除（Perfect Clear）有额外大奖",
    "F2 可调 DAS/ARR 手感与起始等级",
    "消行会随等级加速，20 级就是极限",
)


def fmt_int(n: int) -> str:
    return f"{n:,}"


def fmt_time(sec: float) -> str:
    sec = max(0.0, sec)
    return f"{int(sec) // 60:02d}:{int(sec) % 60:02d}"


# =============================================================================
# 10. 自检（--selftest / --ui）
# =============================================================================

def _expect(cond: bool, label: str) -> int:
    print(f"  [{'ok ' if cond else 'FAIL'}] {label}")
    return 0 if cond else 1


def _put(g: Game, kind: str, rot: int, x: int, y: int, last_rot: bool = False) -> None:
    g.active = {"kind": kind, "rot": rot, "x": x, "y": y, "glow": 0.0, "flash": 0.0}
    g.last_rot = last_rot
    g.last_kick = 0
    g.grounded = not g.fits(kind, rot, x, y + 1)
    g.lock_timer = 0.0
    g.lock_resets = 0


def _fill_row(g: Game, y: int, skip: tuple[int, ...] = ()) -> None:
    for c in range(FIELD_COLS):
        g.grid[y][c] = 0 if c in skip else KIND_ID["I"]


def _blank(g: Game) -> Game:
    g.grid = [[0] * FIELD_COLS for _ in range(GRID_ROWS)]
    g.events.clear()
    return g


def _event(g: Game, kind: str):
    """取最后一个指定类型的事件（事件的 gain 是模型算好的，测试直接用，避免自己算错）。"""
    for e in reversed(g.events):
        if e[0] == kind:
            return e
    return None


def selftest() -> int:
    bad = 0

    print("== 画布几何 ==")
    bad += _expect((BASE_W, BASE_H) == (700, 760), f"设计分辨率 {BASE_W}x{BASE_H}")
    bad += _expect((FIELD_X, FIELD_W, FIELD_Y, FIELD_H) == (200, 300, 114, 600),
                   "场地 300x600，左上 (200,114)")
    bad += _expect(STRIP_TOP == 54 and FIELD_BOTTOM == 714, "出生区顶 54 / 场底 714")
    bad += _expect(FRAME.left() == 191 and FRAME.right() == 509 and FRAME.bottom() == FOOTER_TOP,
                   "场地外框 (191,45)-(509,723) 与底栏对齐")
    bad += _expect(PANEL_L.right() < FRAME.left() and PANEL_R.left() > FRAME.right(),
                   "左右面板都在场地之外")
    bad += _expect(PANEL_L.contains(HOLD_BOX), "HOLD 框在左面板内")
    bad += _expect(PANEL_R.contains(NEXT_BOX) and PANEL_R.contains(PROGRESS_BAR),
                   "NEXT 框与等级进度条都在右面板内")
    bad += _expect(HOLD_BOX.bottom() < 288 and NEXT_BOX.bottom() < 694, "面板内部上下不打架")
    for name in ("pause", "settings", "help", "over"):
        c = overlay_geom(name)
        bad += _expect(QRectF(0, 0, BASE_W, BASE_H).contains(c), f"{name} 卡片在画布内 {c}")

    print("== 方块与 SRS 旋转 ==")
    bad += _expect(all(len(ROTATIONS[k][r]) == 4 for k in KINDS for r in range(4)),
                   "7 种方块 × 4 个旋转态都是 4 格")
    bad += _expect(all(len(set(ROTATIONS[k][r])) == 4 for k in KINDS for r in range(4)),
                   "每种旋转态内部不重叠")
    ok = True
    for k in KINDS:
        for r in range(4):
            if ROTATIONS[k][r] != ROTATIONS[k][(r + 4) % 4]:
                ok = False
    bad += _expect(ok, "旋转态按 4 取模闭合")
    bad += _expect(ROTATIONS["I"][1] == ((2, 0), (2, 1), (2, 2), (2, 3)), "I 的 R 态 = 第 3 列竖条")
    bad += _expect(ROTATIONS["T"][1] == ((1, 0), (1, 1), (1, 2), (2, 1)), "T 的 R 态朝右")
    bad += _expect(ROTATIONS["T"][2] == ((0, 1), (1, 1), (1, 2), (2, 1)), "T 的 2 态朝下")
    bad += _expect(ROTATIONS["T"][3] == ((0, 1), (1, 0), (1, 1), (1, 2)), "T 的 L 态朝左")
    bad += _expect(ROTATIONS["O"][0] == ROTATIONS["O"][2], "O 旋转不改变形状")
    spawns = {k: Game.cells_of(k, 0, SPAWN_X[k], SPAWN_Y) for k in KINDS}
    bad += _expect(spawns["I"] == ((3, 1), (4, 1), (5, 1), (6, 1)), "I 出生在第 3~6 列")
    bad += _expect(sorted({c for c, _ in spawns["T"]}) == [3, 4, 5], "T 出生在第 3~5 列")
    bad += _expect(sorted({c for c, _ in spawns["O"]}) == [4, 5], "O 出生在第 4~5 列")
    bad += _expect(all(y in (0, 1) for k in KINDS for _, y in spawns[k]), "所有方块都出生在出生区两行内")

    print("== 踢墙表 ==")
    for table, name in ((KICKS_JLSTZ, "JLSTZ"), (KICKS_I, "I")):
        bad += _expect(set(table) == {(a, b) for a in range(4) for b in range(4) if (a - b) % 4 in (1, 3)},
                       f"{name} 覆盖全部 8 组相邻旋转")
        bad += _expect(all(len(v) == 5 and v[0] == (0, 0) for v in table.values()),
                       f"{name} 每组 5 个候选且第一个是 (0,0)")
        sym = all(tuple((-x, -y) for (x, y) in table[(a, b)]) == table[(b, a)]
                  for (a, b) in table)
        bad += _expect(sym, f"{name} 正反旋转表互为镜像（官方 SRS 的关键性质）")
    bad += _expect(all(kick_table("O", a, (a + 1) % 4) == ((0, 0),) for a in range(4)),
                   "O 旋转没有踢墙偏移")
    bad += _expect(kick_table("I", 0, 1)[3] == (-2, 1), "I 的 0→R 第 4 个候选 = (-2, 向下 1)")

    print("== 踢墙（真局面） ==")
    g = _blank(Game(seed=3))
    _put(g, "I", 1, -2, 5)                    # 竖着的 I 贴左墙
    bad += _expect(g.rotate(-1) and g.active["rot"] == 0 and g.active["x"] == 0,
                   "左墙处 I 由竖转横被踢回场内 (x:-2 → 0)")
    g = _blank(Game(seed=3))
    _put(g, "T", 0, -1, 10)
    bad += _expect(not g.rotate(1) or all(c >= 0 for c, _ in g.active_cells()),
                   "贴左墙的 T 旋转后仍在场内")
    g = _blank(Game(seed=3))
    _fill_row(g, GRID_ROWS - 1)
    g.grid[GRID_ROWS - 1][4] = 0
    _put(g, "T", 0, 3, GRID_ROWS - 3)
    g.active["y"] = GRID_ROWS - 3
    bad += _expect(g.rotate(1) and all(y < GRID_ROWS for _, y in g.active_cells()),
                   "贴地的 T 旋转后不穿地")
    g = _blank(Game(seed=3))
    _put(g, "S", 0, 4, 6)
    cells0 = g.active_cells()
    for _ in range(4):
        g.rotate(1)
    bad += _expect(g.active_cells() == cells0 and g.active["rot"] == 0, "开阔处转 4 次回到原样")

    print("== 棋盘与落点 ==")
    g = _blank(Game(seed=5))
    bad += _expect(not g.fits("I", 0, -1, 0), "越出左墙不合法")
    bad += _expect(not g.fits("I", 0, 7, 0), "越出右墙不合法")
    bad += _expect(not g.fits("I", 1, 3, GRID_ROWS - 3), "越出地面不合法")
    _fill_row(g, GRID_ROWS - 1, skip=(0, 4, 5))
    _put(g, "O", 0, 4, 0)
    bad += _expect(g.ghost_y() == GRID_ROWS - 2, f"O 的落点是最后一行 (ghost_y={g.ghost_y()})")
    before = g.score
    n = g.hard_drop()
    bad += _expect(n == GRID_ROWS - 2 and g.score - before == 2 * n,
                   f"硬降 {n} 格、每格 2 分（+{g.score - before}）")
    bad += _expect(g.grid[GRID_ROWS - 1][4] == KIND_ID["O"]
                   and g.grid[GRID_ROWS - 2][5] == KIND_ID["O"], "硬降后 O 真的落在盘面上")
    bad += _expect(g.pieces == 2, "锁定后立刻出下一个方块")

    print("== 消行与计分 ==")
    g = _blank(Game(seed=9))
    _fill_row(g, GRID_ROWS - 1, skip=(4,))
    _put(g, "I", 1, 2, GRID_ROWS - 4)
    g.hard_drop()
    bad += _expect(g.phase == "clear" and g.lines == 0, "消行先冻结播放动画")
    bad += _expect(_event(g, "clear") is not None and _event(g, "clear")[1] == 1,
                   "产生 1 行消除事件")
    g.update(CLEAR_TIME + 0.01)
    bad += _expect(g.lines == 1 and g.phase == "play", "动画结束后行数 +1")
    bad += _expect(g.grid[GRID_ROWS - 1][4] == KIND_ID["I"], "消除后上方内容整体下移")

    # 四连消（第 18 行留一个孤块，免得顺带触发完美清除）
    g = _blank(Game(seed=11))
    g.grid[GRID_ROWS - 5][0] = KIND_ID["J"]
    for y in range(GRID_ROWS - 4, GRID_ROWS):
        _fill_row(g, y, skip=(9,))
    _put(g, "I", 1, 7, GRID_ROWS - 4)
    g.hard_drop()
    g.update(CLEAR_TIME + 0.01)
    ev = _event(g, "clear")
    bad += _expect(g.lines == 4 and ev is not None and ev[4] == 800 * g.level,
                   f"四连消 800×等级 = {ev[4] if ev else None}")
    bad += _expect(g.stats["tetris"] == 1, "统计里记到一次四连消")

    # 三连消（I 竖插 3 行，第 4 格留在第 18 行，不算完美清除）
    g = _blank(Game(seed=12))
    for y in range(GRID_ROWS - 3, GRID_ROWS):
        _fill_row(g, y, skip=(9,))
    _put(g, "I", 1, 7, GRID_ROWS - 4)
    g.hard_drop()
    g.update(CLEAR_TIME + 0.01)
    ev = _event(g, "clear")
    bad += _expect(g.lines == 3 and ev is not None and ev[4] == 500 * g.level,
                   f"三连消 500×等级 = {ev[4] if ev else None}")

    # 背靠背：已经有 B2B 状态的四连消 ×1.5
    g = _blank(Game(seed=13))
    g.b2b = True
    g.grid[GRID_ROWS - 5][0] = KIND_ID["J"]
    for y in range(GRID_ROWS - 4, GRID_ROWS):
        _fill_row(g, y, skip=(9,))
    _put(g, "I", 1, 7, GRID_ROWS - 4)
    g.hard_drop()
    g.update(CLEAR_TIME + 0.01)
    ev = _event(g, "clear")
    bad += _expect(ev is not None and ev[5] is True and ev[4] == int(800 * B2B_MULT) * g.level,
                   f"背靠背四连消 800×1.5×等级 = {ev[4] if ev else None}")

    # 连击：两块连续各消一行
    g = _blank(Game(seed=14))
    _fill_row(g, GRID_ROWS - 1, skip=(4,))
    _put(g, "I", 1, 2, GRID_ROWS - 4)
    g.hard_drop()
    g.update(CLEAR_TIME + 0.01)
    first = _event(g, "clear")
    _fill_row(g, GRID_ROWS - 1, skip=(6,))
    _put(g, "I", 1, 4, GRID_ROWS - 4)
    g.hard_drop()
    g.update(CLEAR_TIME + 0.01)
    second = _event(g, "clear")
    want = 100 * g.level + COMBO_UNIT * 1 * g.level
    bad += _expect(first is not None and second is not None and g.combo == 1
                   and second[6] == 1 and second[4] == want,
                   f"连击加成 {COMBO_UNIT}×n×等级（第二块 +{second[4] if second else None}，"
                   f"应为 {want}）")

    # 完美清除
    g = _blank(Game(seed=15))
    for y in (GRID_ROWS - 2, GRID_ROWS - 1):
        _fill_row(g, y, skip=(8, 9))
    _put(g, "O", 0, 8, 0)
    before = g.score
    g.hard_drop()
    g.update(CLEAR_TIME + 0.01)
    gain = g.score - before
    bad += _expect(g.stats["perfect"] == 1
                   and gain == (300 + PERFECT_BASE[2]) * g.level + 2 * (GRID_ROWS - 2),
                   f"完美清除额外奖励（本块 +{gain}）")
    bad += _expect(g.stack_top() == GRID_ROWS, "完美清除后盘面是空的")

    print("== T-Spin ==")
    # 第 19 行：给 T 的角留出缺口；第 20 行整行只差 T 的三格；第 21 行只差 T 的凸起
    def tspin_board(mode: str = "single") -> Game:
        gg = _blank(Game(seed=21))
        skip19 = (4, 7) if mode != "mini" else (4, 5, 7)
        _fill_row(gg, GRID_ROWS - 3, skip=skip19)
        _fill_row(gg, GRID_ROWS - 2, skip=(3, 4, 5) if mode != "none" else (0, 3, 4, 5))
        _fill_row(gg, GRID_ROWS - 1, skip=(0, 4) if mode != "none" else (1, 4))
        _put(gg, "T", 0, 3, GRID_ROWS - 3, last_rot=True)
        return gg

    g = tspin_board("single")
    bad += _expect(g.fits("T", 0, 3, GRID_ROWS - 3), "T-Spin 场景里 T 放得下")
    g.lock_piece()
    ev = _event(g, "clear")
    bad += _expect(ev is not None and ev[2] == "full", f"四角占三个 → 完整 T-Spin（{ev}）")
    bad += _expect(ev is not None and ev[4] == TSPIN_BASE[("full", 1)] * g.level,
                   f"T-Spin 单消 = {TSPIN_BASE[('full', 1)]}×等级 = {ev[4] if ev else None}")

    g = tspin_board("mini")
    g.lock_piece()
    ev = _event(g, "clear")
    bad += _expect(ev is not None and ev[2] == "mini", f"前角只堵一个 → T-Spin Mini（{ev}）")
    bad += _expect(ev is not None and ev[4] == TSPIN_BASE[("mini", 1)] * g.level,
                   f"T-Spin Mini 单消 = {TSPIN_BASE[('mini', 1)]}×等级 = {ev[4] if ev else None}")

    g = tspin_board("none")
    g.lock_piece()
    ev = _event(g, "tspin0")
    bad += _expect(ev is not None and ev[2] == 400 * g.level,
                   f"T-Spin 不吃行也是 400×等级 = {ev[2] if ev else None}")
    bad += _expect(not g.clear_rows, "这一手确实没有消行")

    g = _blank(Game(seed=23))
    _put(g, "T", 0, 3, GRID_ROWS - 3, last_rot=False)
    g.lock_piece()
    bad += _expect(_event(g, "tspin0") is None and _event(g, "clear") is None,
                   "没旋转过的 T 不算 T-Spin")

    print("== T-Spin × 硬降（复审发现的回归） ==")
    g = tspin_board("single")
    g.hard_drop()                                   # 原地硬降 0 格
    ev = _event(g, "clear")
    bad += _expect(ev is not None and ev[2] == "full" and ev[4] == 800 * g.level,
                   f"转进去再按空格锁定照样算 T-Spin（{ev}）")

    print("== 完美清除按消行前的等级结算 ==")
    g = _blank(Game(seed=24))
    g.lines = LINE_PER_LEVEL - 1                    # 再来 2 行就升级
    for y in (GRID_ROWS - 2, GRID_ROWS - 1):
        _fill_row(g, y, skip=(8, 9))
    _put(g, "O", 0, 8, 0)
    before = g.score
    g.hard_drop()
    g.update(CLEAR_TIME + 0.01)
    gain = g.score - before
    want = (BASE_CLEAR[2] + PERFECT_BASE[2]) * 1 + 2 * (GRID_ROWS - 2)
    bad += _expect(g.level == 2 and gain == want,
                   f"升级的那一手仍按旧等级算（+{gain}，应为 {want}）")

    print("== 出生后立刻下移一格 ==")
    g = Game(seed=25)
    low = max(y for _, y in g.active_cells())
    bad += _expect(low >= BUFFER_ROWS, f"新方块已经露出可见区（最低一格在第 {low} 行）")

    print("== 左右键同时按的处理 ==")
    g = _blank(Game(seed=26))
    _put(g, "O", 0, 4, 4)
    g.press_dir(-1)
    g.press_dir(1)
    g.release_dir(1)
    bad += _expect(g.das_dir == -1 and g.dir_held[-1], "松开后按的那个键，仍按着的方向继续生效")
    g.release_dir(-1)
    bad += _expect(g.das_dir == 0 and not any(g.dir_held.values()), "两个键都松开后彻底停下")

    print("== 存档容错 ==")
    bad += _expect(sanitize_opt({"feel": 9, "start_level": 42, "ghost": 0}) ==
                   {**DEFAULT_OPT, "feel": 0, "start_level": 0, "ghost": False},
                   "越界/错类型的手改存档被收成合法值")
    bad += _expect(sanitize_opt(None) == DEFAULT_OPT and sanitize_opt([1, 2]) == DEFAULT_OPT
                   and sanitize_opt({"没这个键": 1}) == DEFAULT_OPT, "坏存档一律回到默认设置")
    bad += _expect(_safe_int("abc") == 0 and _safe_int(None) == 0 and _safe_int(3) == 3,
                   "最高分读到垃圾值时退回 0")

    # 统计量的合理性校验（见 sanitize_stats）：手改的 save.json 不能污染"最高分"。
    # ⚠️ 用真出现过的那个病例当样例：high = 9999999（10⁷−1，典型的封顶值）却只有
    #    52 行 —— 52 行按满级+TSpin三连消+B2B 也到不了，必须被压回理论上限。
    s = sanitize_stats({"high": 9999999, "games": 21, "total_lines": 52, "best_combo": 2})
    bad += _expect(s["high"] == _max_plausible(52) < 9999999,
                   f"封顶值被压回理论上限（{s['high']:,} < 9,999,999）")
    bad += _expect(s["games"] == 21 and s["total_lines"] == 52 and s["best_combo"] == 2,
                   "压 high 时不动其它统计量")
    bad += _expect(_max_plausible(0) == 0, "一行没消过时最高分上限为 0")
    bad += _expect(_max_plausible(52) < 9999999,
                   f"理论上限随行数增长且远低于封顶值（52 行 -> {_max_plausible(52):,}）")
    bad += _expect(_max_plausible(1000) > _max_plausible(100),
                   "行数越多允许的分数越高（上限是单调的）")
    # 正常成绩不能被误杀：上限内的一律原样保留
    bad += _expect(sanitize_stats({"high": 30000, "total_lines": 1})["high"] == 30000,
                   "上限内的真实成绩原样保留")
    # 负数 / 非数字 / 缺字段 / 不是字典
    bad += _expect(sanitize_stats({"high": -5})["high"] == 0, "负数最高分归零")
    bad += _expect(sanitize_stats({"high": 10 ** 20, "total_lines": 10 ** 20})["high"]
                   == _max_plausible(MAX_TOTAL_LINES), "天文数字被行数上限兜住")
    bad += _expect(sanitize_stats(None) == {"high": 0, "games": 0, "total_lines": 0,
                                            "best_combo": 0}, "非字典存档全归零")
    bad += _expect(sanitize_stats("坏")["high"] == 0 and sanitize_stats({})["high"] == 0,
                   "字符串/空存档全归零")

    print("== 7-bag 随机 ==")
    g = Game(seed=2024)
    seq = [g._from_bag() for _ in range(700)]
    counts = {k: seq.count(k) for k in KINDS}
    bad += _expect(all(v == 100 for v in counts.values()), f"700 个方块每种 100 个 {counts}")
    bad += _expect(all(set(seq[i:i + 7]) == set(KINDS) for i in range(0, 700, 7)),
                   "每 7 个一组恰好是全部 7 种（7-bag）")
    bad += _expect(Game(seed=42).expect_queue() == Game(seed=42).expect_queue(),
                   "同一个种子给出同一串方块")
    bad += _expect(len(Game(seed=1).expect_queue()) == 5, "预览队列 5 个")
    bad += _expect(len({tuple(Game(seed=s).expect_queue()) for s in range(30)}) > 25,
                   "不同种子给出不同序列")

    print("== 重力与等级 ==")
    bad += _expect(abs(gravity_interval(1) - 1.0) < 1e-9, "1 级每秒 1 格")
    bad += _expect(abs(gravity_interval(10) - (0.8 - 9 * 0.007) ** 9) < 1e-9,
                   f"10 级 {gravity_interval(10):.4f} 秒/格（官方曲线）")
    bad += _expect(all(gravity_interval(l) > gravity_interval(l + 1) for l in range(1, 18)),
                   "前 18 级下落速度严格递增")
    bad += _expect(all(gravity_interval(l) >= gravity_interval(l + 1) for l in range(1, 60)),
                   "等级继续升高也不会变慢")
    bad += _expect(all(abs(gravity_interval(l) - (0.8 - (l - 1) * 0.007) ** (l - 1)) < 1e-12
                       for l in range(1, 21)), "1~20 级完全按官方公式，没有被下限截断")
    bad += _expect(gravity_interval(99) >= 1 / 5000, "极端等级下仍有一个兜底速度")
    g = Game(seed=1)
    g.lines = 9
    _fill_row(g, GRID_ROWS - 1, skip=(4,))
    _put(g, "I", 1, 2, GRID_ROWS - 4)
    g.hard_drop()
    g.update(CLEAR_TIME + 0.01)
    bad += _expect(g.lines == 10 and g.level == 2, "满 10 行升到 2 级")
    bad += _expect(any(e[0] == "levelup" for e in g.events), "产生升级事件")
    bad += _expect(Game(seed=1, start_level=5).level == 5, "可以从第 5 级开局")
    bad += _expect(Game(seed=1).lines_to_next() == (0, LINE_PER_LEVEL), "开局进度 0/10")

    print("== 锁定延迟与手感 ==")
    g = _blank(Game(seed=31))
    _put(g, "O", 0, 4, GRID_ROWS - 2)
    g.grounded = True
    g.update(LOCK_DELAY - 0.05)
    bad += _expect(g.grid[GRID_ROWS - 1][4] == 0, "不到 0.5 秒不锁定")
    g.update(0.06)
    bad += _expect(g.grid[GRID_ROWS - 1][4] != 0 and g.grid[GRID_ROWS - 2][4] != 0,
                   "超过 0.5 秒锁定并留在盘面上")
    g = _blank(Game(seed=32))
    _put(g, "O", 0, 4, GRID_ROWS - 2)
    g.grounded = True
    for _ in range(LOCK_RESET_MAX + 8):          # 每次贴地移动都重置计时器
        g.move(-1)
        g.move(1)
        g.update(0.2)
    bad += _expect(g.grid[GRID_ROWS - 1][4] != 0, f"最多重置 {LOCK_RESET_MAX} 次后必定锁定")
    g = _blank(Game(seed=33))
    _put(g, "I", 1, 2, 6)
    before = g.score
    soft0 = g.stats["soft_cells"]
    g.set_soft(True)
    for _ in range(10):
        g.update(0.05)
    dropped = g.stats["soft_cells"] - soft0
    bad += _expect(dropped >= 5 and g.score - before == SOFT_DROP_POINT * dropped,
                   f"软降每格 1 分（落了 {dropped} 格，+{g.score - before}）")
    bad += _expect(g.grav_acc <= g.gravity_interval() + 1e-9,
                   f"贴地时不再偷偷攒重力（grav_acc={g.grav_acc:.4f}）")
    g.set_soft(False)
    g = _blank(Game(seed=34))
    bad += _expect(g.hold_piece() and g.hold is not None, "第一次 Hold 生效")
    held = g.hold
    bad += _expect(not g.hold_piece(), "同一块不能连续 Hold 两次")
    g.hard_drop()
    g.update(CLEAR_TIME + 0.01)
    bad += _expect(g.hold == held and not g.hold_used, "换到下一块后 Hold 恢复可用")

    print("== 顶死与结算 ==")
    g = _blank(Game(seed=41))
    for y in range(0, 4):
        _fill_row(g, y)
    _put(g, "O", 0, 4, 0)
    g.spawn()
    bad += _expect(g.phase == "dying" and g.dead_reason == "block out", "出生位被占 → Block Out")
    g.update(OVER_TIME + 0.05)
    bad += _expect(g.phase == "over", "结束动画跑完后进入结算")
    bad += _expect(all(all(v == DEAD_ID for v in row) for row in g.grid), "结算动画把盘面填满灰块")
    g = _blank(Game(seed=42))
    _fill_row(g, BUFFER_ROWS)
    _put(g, "O", 0, 4, 0)
    g.lock_piece()
    bad += _expect(g.phase == "dying" and g.dead_reason == "lock out", "整块锁在出生区 → Lock Out")
    g = _blank(Game(seed=43))
    _put(g, "O", 0, 4, 0)
    for _ in range(40):
        g.update(1.0)
    bad += _expect(g.pieces >= 2 and any(any(row) for row in g.grid) and g.phase != "dying",
                   f"方块落到底会锁定并继续出块（出了 {g.pieces} 个，没顶死）")

    print("== 随机压力测试 ==")
    g = Game(seed=99)
    rnd = random.Random(7)
    pieces = 0
    for i in range(24000):
        g.update(1.0 / 60.0)
        g.events.clear()
        if g.phase in ("dying", "over"):
            break
        r = rnd.random()
        if r < 0.25:
            g.move(rnd.choice((-1, 1)))
        elif r < 0.35:
            g.rotate(rnd.choice((-1, 1, 2)))
        elif r < 0.40:
            g.hold_piece()
        elif r < 0.50:
            g.hard_drop()
            pieces += 1
    ok = all(len(row) == FIELD_COLS and all(0 <= v <= DEAD_ID for v in row) for row in g.grid)
    bad += _expect(ok, "长时间乱按后棋盘数据仍然合法")
    bad += _expect(g.phase in ("dying", "over"), "乱按最终会顶死（不会卡死）")
    bad += _expect(g.pieces >= 10, f"乱按仍然出了 {g.pieces} 个方块")

    print(f"\n{'全部通过' if bad == 0 else str(bad) + ' 项失败'}")
    return 1 if bad else 0


# ---------------------------------------------------------------- 版面体检
OVERLAY_PREFIX = ("设置", "帮助", "计分", "暂停", "结束", "统计", "新纪录")


def ui_check(w: "TetrisWidget") -> int:
    bad = 0
    canvas = QRectF(0, 0, BASE_W, BASE_H)
    field_zone = QRectF(FIELD_X, STRIP_TOP, FIELD_W, FIELD_H + BUFFER_ROWS * CELL)
    g = w.game

    # 极值状态：满位数、满连击、满堆叠 + 有暂存
    g.score = 9_999_999
    g.lines = 199
    g.level = MAX_LEVEL
    g.pieces = 9999
    g.elapsed = 5999.0
    g.combo = 12
    g.b2b = True
    g.stats["tspin"] = 8
    g.stats["tspin_mini"] = 3
    g.stats["tetris"] = 7
    g.stats["perfect"] = 2
    g.stats["combo_max"] = 12
    g.hold = "I"
    g.hold_used = True
    w.high = 9_999_999
    for y in range(GRID_ROWS - 20, GRID_ROWS):
        _fill_row(g, y)
    g.grid[GRID_ROWS - 20][0] = 0
    g.grid[GRID_ROWS - 19][4] = 0
    bad += _expect(g.danger() > 0.9, f"堆到顶时危险度拉满（{g.danger():.2f}）")

    def group(name: str) -> str:
        if name.startswith(OVERLAY_PREFIX):
            return "overlay"
        if name in ("出生区", "危险"):
            return "field"
        return "base"

    def zone_of(r: QRectF) -> tuple[str, QRectF]:
        if r.bottom() <= HEADER_BOTTOM:
            return "顶栏", QRectF(0, 0, BASE_W, HEADER_BOTTOM)
        if r.top() >= FOOTER_TOP:
            return "底栏", QRectF(0, FOOTER_TOP, BASE_W, BASE_H - FOOTER_TOP)
        if r.center().x() < BASE_W / 2:
            return "左面板", PANEL_L
        return "右面板", PANEL_R

    def scan(tag: str, card: QRectF | None = None) -> int:
        """检查当前状态下所有文字的着墨矩形：出界 / 同组重叠 / 压场地 / 超出所属区域。"""
        n = 0
        items = w.text_items()
        boxes = [(it.name, ink_rect(it)) for it in items]
        for name, r in boxes:
            if not canvas.contains(r):
                n += _expect(False, f"[{tag}] {name} 溢出画布 {r}")
            if card is not None and group(name) == "overlay" \
                    and not card.adjusted(4, 4, -4, -4).contains(r):
                n += _expect(False, f"[{tag}] {name} 超出卡片 {r}")
            if group(name) != "base":
                continue
            zone, zone_rect = zone_of(r)
            if not zone_rect.adjusted(-1, -1, 1, 1).contains(r):
                n += _expect(False, f"[{tag}] {name} 超出{zone} {r}")
        for i in range(len(boxes)):
            for j in range(i):
                if group(boxes[i][0]) != group(boxes[j][0]):
                    continue                      # 覆盖层压住的面板文字不算冲突
                if boxes[i][1].intersects(boxes[j][1]):
                    n += _expect(False, f"[{tag}] {boxes[i][0]} 与 {boxes[j][0]} 重叠 "
                                        f"{boxes[i][1]} ∩ {boxes[j][1]}")
        for name, r in boxes:
            if group(name) != "base":
                continue
            if r.intersects(field_zone):
                n += _expect(False, f"[{tag}] {name} 压到场地上 {r}")
        if n == 0:
            print(f"  [ok ] [{tag}] {len(boxes)} 处文字：都在画布内、同组互不重叠、"
                  f"面板文字不压场地且不越界")
        return n

    print("== 普通对局版面 ==")
    bad += scan("对局")
    # 底栏小贴士会轮播：每一条都必须放得下，且不和左右两端的文字打架
    for i in range(len(TIPS)):
        w.t = i * 12 + 1
        bad += scan(f"底栏提示{i}")
    w.t = 1.0

    print("== 覆盖层版面 ==")
    w.paused = True
    bad += scan("暂停", card=overlay_geom("pause"))
    w.paused = False
    w.overlay = "settings"
    bad += scan("设置", card=overlay_geom("settings"))
    rows = w.setting_rows()
    for i, (name, val, desc) in enumerate(rows):
        r = setting_row_rect(overlay_geom("settings"), i)
        bad += _expect(overlay_geom("settings").contains(r), f"设置行 {i}「{name}」在卡片内")
    # ⚠️ 行数不写死：设置项会随版本增减，而这里要验的是「每一行都画得下」，
    #    不是「恰好 N 行」。写死一个数字只会让每次加设置都误报（原先写死 7，
    #    在「螺螺头像」那行加进来之后就一直误报，却没人发现）。
    bad += _expect(len(rows) >= 8, f"设置面板 {len(rows)} 行（至少 8）")
    w.overlay = "help"
    bad += scan("帮助", card=overlay_geom("help"))
    w.overlay = None

    g.phase = "over"
    g.dead_reason = "block out"
    w.new_record = True
    bad += scan("结算", card=overlay_geom("over"))
    g.phase = "play"
    w.new_record = False

    print("== 面板与预览 ==")
    bad += _expect(PANEL_L.contains(HOLD_BOX.adjusted(-6, -6, 6, 6)), "HOLD 框含边框仍在左面板内")
    for i in range(5):
        slot = QRectF(NEXT_BOX.x(), NEXT_BOX.y() + i * NEXT_SLOT_H, NEXT_BOX.width(),
                      NEXT_SLOT_H - 8)
        bad += _expect(PANEL_R.contains(slot), f"NEXT 第 {i + 1} 格在右面板内")
        for k in KINDS:
            minx, miny, maxx, maxy = piece_bounds(k)
            wpx = (maxx - minx + 1) * PREVIEW_CELL
            hpx = (maxy - miny + 1) * PREVIEW_CELL
            box = QRectF(slot.center().x() - wpx / 2.0, slot.center().y() - hpx / 2.0, wpx, hpx)
            if not slot.adjusted(2, 2, -2, -2).contains(box):
                bad += _expect(False, f"{k} 在 NEXT 第 {i + 1} 格里放不下 {box}")
    if bad == 0:
        print("  [ok ] 7 种方块在 5 个 NEXT 格与 HOLD 框里都居中放得下")

    bad += _expect(field_zone.bottom() <= FOOTER_TOP and field_zone.contains(
        QRectF(FIELD_X, FIELD_Y, FIELD_W, FIELD_H)), "场地与底栏不重叠")
    return bad


# ---------------------------------------------------------------- 真键盘事件打一局
def _key(w, code: int, press: bool = True) -> None:
    QApplication.sendEvent(w, QKeyEvent(
        QEvent.Type.KeyPress if press else QEvent.Type.KeyRelease, code,
        Qt.KeyboardModifier.NoModifier))


def _click(w, x: float, y: float) -> None:
    s, ox, oy = w.canvas_transform()
    QApplication.sendEvent(w, QMouseEvent(
        QEvent.Type.MouseButtonPress, QPointF(x * s + ox, y * s + oy),
        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))


def _run(w, seconds: float) -> None:
    """按 60Hz 推进 seconds 秒：单帧最多补 MAX_SUBSTEPS 步，所以测试也要一帧帧喂。"""
    for _ in range(max(1, int(round(seconds * FPS)))):
        w.advance(1.0 / FPS)


def playthrough_check(w: "TetrisWidget") -> int:
    bad = 0
    w.persist = False
    w.auto_pause = False
    w.new_game()
    g = w.game
    bad += _expect(g.phase == "play" and g.active is not None, "R 之后是新的一局")

    print("== 键盘 ==")
    x0 = g.active["x"]
    _key(w, Qt.Key.Key_Right)
    bad += _expect(g.active["x"] == x0 + 1, "→ 右移一格")
    _key(w, Qt.Key.Key_Left)
    bad += _expect(g.active["x"] == x0, "← 左移回来")
    _key(w, Qt.Key.Key_Up)
    bad += _expect(g.active["rot"] == 1, "↑ 顺时针旋转")
    _key(w, Qt.Key.Key_Z)
    bad += _expect(g.active["rot"] == 0, "Z 逆时针转回来")
    _key(w, Qt.Key.Key_A)
    bad += _expect(g.active["rot"] == 2, "A 旋转 180°")
    _key(w, Qt.Key.Key_A)

    print("== DAS / ARR（按住右键） ==")
    x0 = g.active["x"]
    _key(w, Qt.Key.Key_Right)
    _run(w, 0.40)
    _key(w, Qt.Key.Key_Right, press=False)
    kind, rot = g.active["kind"], g.active["rot"]
    right_edge = max(c for c, _ in Game.cells_of(kind, rot, g.active["x"], g.active["y"]))
    bad += _expect(right_edge == FIELD_COLS - 1 and g.active["x"] > x0,
                   f"按住 0.4 秒后贴到右墙（x={g.active['x']}，右边界 {right_edge}）")

    print("== 软降 / 硬降 ==")
    y0 = g.active["y"]
    _key(w, Qt.Key.Key_Down)
    _run(w, 0.25)
    _key(w, Qt.Key.Key_Down, press=False)
    bad += _expect(g.active["y"] > y0, f"按住 ↓ 下落了 {g.active['y'] - y0} 格")
    before_pieces, before_score = g.pieces, g.score
    _key(w, Qt.Key.Key_Space)
    bad += _expect(g.pieces > before_pieces and g.score > before_score, "空格硬降并锁定")
    bad += _expect(w.particles, "硬降产生了粒子")

    print("== Hold ==")
    _run(w, 0.2)
    kind = g.active["kind"]
    _key(w, Qt.Key.Key_C)
    bad += _expect(g.hold == kind and g.hold_used, "C 键把当前块存进 Hold")
    held, cur = g.hold, g.active["kind"]
    _key(w, Qt.Key.Key_C)
    bad += _expect(g.hold == held and g.active["kind"] == cur, "同一块内再按 C 无效")

    print("== 真消行（造一个四连消） ==")
    _blank(g)
    for y in range(GRID_ROWS - 4, GRID_ROWS):
        _fill_row(g, y, skip=(9,))
    _put(g, "I", 1, 7, GRID_ROWS - 4)
    g.phase = "play"
    lines0, score0 = g.lines, g.score
    _key(w, Qt.Key.Key_Space)
    fx = len(w.particles)
    _run(w, CLEAR_TIME + 0.2)
    bad += _expect(g.lines == lines0 + 4, f"四连消真的消掉 4 行（{g.lines - lines0}）")
    bad += _expect(g.score > score0 + 800, f"得分增加 {g.score - score0}")
    bad += _expect(fx > 0 and w.toasts, f"消行播放了特效（{fx} 个粒子、{len(w.toasts)} 条浮字）")

    print("== 暂停 / 重开 / 结束 ==")
    _key(w, Qt.Key.Key_P)
    bad += _expect(w.paused, "P 暂停")
    x_before = g.active["x"] if g.active else None
    _key(w, Qt.Key.Key_Left)
    _run(w, 0.3)
    bad += _expect(g.active is not None and g.active["x"] == x_before, "暂停时按键不动棋盘")
    _key(w, Qt.Key.Key_P)
    bad += _expect(not w.paused, "P 继续")
    _key(w, Qt.Key.Key_Escape)
    bad += _expect(w.paused, "Esc 也能暂停")
    _key(w, Qt.Key.Key_Escape)
    bad += _expect(not w.paused, "再按 Esc 继续")

    for y in range(0, 5):
        _fill_row(g, y)
    g.grid[BUFFER_ROWS][5] = 0
    _put(g, "O", 0, 4, 0)
    g.spawn()
    bad += _expect(g.phase == "dying", "堆满后顶死")
    _run(w, OVER_TIME + 0.3)
    bad += _expect(g.phase == "over", "结束动画后进入结算界面")

    print("== 结算界面按键 ==")
    _key(w, Qt.Key.Key_R)
    bad += _expect(g.phase == "play" and g.score == 0 and g.lines == 0, "R 重开一局，分数清零")
    bad += _expect(g.pieces >= 1 and g.active is not None, "重开后立刻有方块在场上")

    print("== 鼠标：设置面板 ==")
    _key(w, Qt.Key.Key_F2)
    bad += _expect(w.overlay == "settings", "F2 打开设置")
    ghost0 = w.opt["ghost"]
    r0 = setting_row_rect(overlay_geom("settings"), 0)
    _click(w, r0.center().x(), r0.center().y())
    bad += _expect(w.opt["ghost"] != ghost0, "点第一行切换幽灵块")
    _click(w, r0.center().x(), r0.center().y())
    _click(w, 20, 20)
    bad += _expect(w.overlay is None, "点卡片外关闭设置")
    _key(w, Qt.Key.Key_F1)
    bad += _expect(w.overlay == "help", "F1 打开帮助")
    _key(w, Qt.Key.Key_Escape)
    bad += _expect(w.overlay is None, "Esc 关闭帮助")

    print("== 暂停时不应该继续掉块 ==")
    _key(w, Qt.Key.Key_P)
    y0 = g.active["y"] if g.active else None
    _run(w, 1.0)
    bad += _expect(g.active is not None and g.active["y"] == y0, "暂停 1 秒方块纹丝不动")
    _key(w, Qt.Key.Key_P)
    bad += _expect(not w.paused, "空格之外的按键也能继续")

    print("== 消行冻结期间空格不该顺手暂停 ==")
    _blank(g)
    _fill_row(g, GRID_ROWS - 1, skip=(4,))
    _put(g, "I", 1, 2, GRID_ROWS - 4)
    g.phase = "play"
    _key(w, Qt.Key.Key_Space)                     # 硬降 → 进入 clear 冻结
    bad += _expect(g.phase == "clear", "硬降后进入消行冻结")
    _key(w, Qt.Key.Key_Space)
    bad += _expect(not w.paused, "冻结期间按空格不会误触发暂停")
    _run(w, CLEAR_TIME + 0.2)
    bad += _expect(g.lines == 1 and not w.paused, "冻结结束后正常继续")
    return bad


# =============================================================================
# 11. 演示场景（--shot 用）
# =============================================================================

STACK_MID = (
    "IJLOSTZ...",
    "..SS..TT..",
    "LL..ZZ..SS",
    "IIOO..LL..",
    "SS..III...",
    "TTT..OO...",
    "ZZ..SS..TT",
    "..LL.II.OO",
    "II..ZZ..SS",
    "..TTT.OO..",
    "SS..LL..II",
    "ZZ..OO..TT",
)
STACK_HIGH = (
    "Z..L....T.",
    ".SS.II.OO.",
    "II..ZZ..SS",
    "LL.TT..OO.",
    ".SS..II..T",
    "ZZ..LL..SS",
    "IIOO..TT..",
    "..SS.ZZ.LL",
    "TT..II..OO",
    "LL..SS..TT",
    "..ZZ.II..L",
    "SS.OO..TT.",
)


def _paint_pattern(g: Game, pattern: tuple[str, ...], top: int) -> None:
    for i, pat in enumerate(pattern):
        y = top + i
        if not (0 <= y < GRID_ROWS):
            continue
        for c, ch in enumerate(pat[:FIELD_COLS]):
            if ch in KIND_ID:
                g.grid[y][c] = KIND_ID[ch]


def setup_demo(w: "TetrisWidget", demo: str) -> tuple[str, int]:
    """摆好一个演示局面，返回 (说明, 建议再推进的帧数)。"""
    g = w.game
    w.audio.set_sfx(False)
    w.audio.set_music(False)

    if demo == "stack":
        _blank(g)
        _paint_pattern(g, STACK_MID, GRID_ROWS - len(STACK_MID))
        g.grid[GRID_ROWS - 2][7] = 0
        g.score = 128_450
        g.lines = 57
        g.start_level = 1
        g.level = 1 + g.lines // LINE_PER_LEVEL
        g.pieces = 214
        g.elapsed = 214.0
        g.combo = 3
        g.b2b = True
        g.hold = "T"
        g.hold_used = True
        g.stats.update(tetris=5, tspin=3, combo_max=6)
        g.queue = ["S", "I", "Z", "J", "O", "T"]
        _put(g, "S", 0, 5, 4)
        return "中局：堆了 12 行、连击 3、B2B、Hold 已用", 40

    if demo == "tetris":
        _blank(g)
        g.grid[GRID_ROWS - 5][0] = KIND_ID["J"]
        for y in range(GRID_ROWS - 4, GRID_ROWS):
            _fill_row(g, y, skip=(9,))
        _put(g, "I", 1, 7, GRID_ROWS - 4)
        g.score = 8_200
        g.lines = 11
        g.level = 2
        return "四连消前的最后一格", 12

    if demo == "clear":
        setup_demo(w, "tetris")
        g.hard_drop()
        w._drain_events()
        _run(w, 0.14)
        return "四连消动画中（白闪 + 粒子 + 得分浮字）", 0

    if demo == "tspin":
        _blank(g)
        _fill_row(g, GRID_ROWS - 3, skip=(4, 7))
        _fill_row(g, GRID_ROWS - 2, skip=(3, 4, 5))
        _fill_row(g, GRID_ROWS - 1, skip=(0, 4))
        _put(g, "T", 0, 3, GRID_ROWS - 3, last_rot=True)
        g.score = 24_600
        g.lines = 33
        g.level = 4
        g.combo = 2
        g.b2b = True
        g.lock_piece()
        w._drain_events()
        _run(w, 0.14)
        return "T-Spin 单消：横幅 + 粒子 + B2B", 0

    if demo == "danger":
        _blank(g)
        _paint_pattern(g, STACK_HIGH, 4)
        _paint_pattern(g, STACK_HIGH, GRID_ROWS - len(STACK_HIGH))
        g.grid[4][2] = 0
        g.grid[5][7] = 0
        _put(g, "S", 0, 4, 0)
        g.score = 96_300
        g.lines = 88
        g.level = 9
        g.pieces = 320
        g.elapsed = 420.0
        return "危险：堆到出生区，边框红色脉冲 + 危险提示", 12

    if demo == "hold":
        _blank(g)
        _paint_pattern(g, STACK_MID, GRID_ROWS - len(STACK_MID))
        g.hold = "I"
        g.hold_used = True
        w.hold_flash = 0.28
        g.queue = ["L", "O", "S", "Z", "T", "J"]
        return "Hold 已使用（变暗）+ 闪光", 6

    if demo == "pause":
        setup_demo(w, "stack")
        w.paused = True
        return "暂停覆盖层", 6

    if demo == "over":
        _blank(g)
        _paint_pattern(g, STACK_HIGH, BUFFER_ROWS)
        for y in range(BUFFER_ROWS, BUFFER_ROWS + 3):
            _fill_row(g, y, skip=(y % 3,))
        g.score = 356_780
        g.lines = 142
        g.level = 15
        g.pieces = 512
        g.elapsed = 733.0
        g.stats.update(tetris=11, tspin=6, tspin_mini=2, perfect=1, combo_max=9, hold=23)
        g.hard_drop()
        w._drain_events()
        _run(w, OVER_TIME + 0.4)
        w._drain_events()
        w.new_record = True
        w.high = 356_780
        return "结算界面：完整统计 + 新纪录", 6

    if demo == "help":
        setup_demo(w, "stack")
        w.overlay = "help"
        return "帮助覆盖层：键位与计分", 6

    if demo == "settings":
        setup_demo(w, "stack")
        w.overlay = "settings"
        w.hover_row = 4
        return "设置覆盖层", 6

    _blank(g)
    _paint_pattern(g, STACK_MID, GRID_ROWS - len(STACK_MID))
    return "开局", 40


# =============================================================================
# 12. zmlx 界面接线（菜单「帮助 → 打开 → 方块」）
# =============================================================================

#: 标签页标题，同时也是 ``gui.get_widget`` 的 caption。
CAPTION = '方块'


class TetrisView(TetrisWidget):
    """螺螺是方块控件（给 zmlx 用的那个）。

    ``TetrisWidget`` 是原版游戏控件，规则一行未改；本子类只补**标签页生命周期**：
    切走时停表 + 暂停、切回来续表并取消暂停、关标签页时收尾，以及把"退出游戏"
    接到宿主的关标签流程上（见 :meth:`TetrisWidget.request_close`）。

    ⚠️ **为什么必须停表**：原版是独立窗口，开着一局就一直是 60 FPS 重绘；放进
    标签页后它可能被切到后台、甚至从未被打开（``gui_restore`` 恢复的标签）。
    不停表就是让一个没人在看的游戏白烧 CPU（20 级下每帧要跑 10 个逻辑子步）。

    ⚠️ **为什么必须重置 ``last_ms``**：``TetrisWidget._frame`` 拿"距上一帧的
    毫秒数"当 dt。计时器在后台停了几分钟，切回来第一次 ``_frame`` 就会拿到那
    几分钟 —— 虽然有 0.25 秒上限，但仍会一次补满 ``MAX_SUBSTEPS`` 步，看起来
    就是"一切回来方块猛地往下掉了一大截"。所以续表前先把基准时间对齐到当下。

    ⚠️ **本控件有"被关过"与"被切走"两种隐藏，语义完全不同**：切走（切标签）
    后切回来应当继续玩；被关掉之后就不该再回来。两者都表现为 ``hideEvent``，
    所以用一个 :attr:`_closing` 标志区分 —— 见 :meth:`hideEvent`。
    """

    def __init__(self, parent=None):
        super().__init__()
        #: 宿主注入的"关掉本标签页"回调（``TabWidget.close_tab``）。
        #: ⚠️ 由 :func:`show_tetris` 在 ``gui.get_widget`` 的 ``oper`` 里
        #: 注入；没有它时 ``request_close`` 只能退回 ``self.close()``。
        self.close_callback = None
        #: 是否正在被关闭（``cleanup_before_tab_close`` 置位）。
        #: ⚠️ 用它把"关标签"与"切标签"两种 ``hideEvent`` 区分开：
        #: 前者要彻底安静下来，后者只是暂时离开。
        self._closing = False
        if parent is not None:
            self.setParent(parent)

    def _bind_close_callback(self):
        """把自己接到宿主的关标签流程上（由 :func:`show_tetris` 调用）.

        沿 ``parent()`` 往上找 ``TabWidget``（要的是 ``close_tab_object``）。
        ⚠️ 找不到就保持 ``None``：那时 ``request_close`` 会退回 ``self.close()``，
        在独立窗口（``test_1()``）场景下正是对的。

        顺手在这儿接上"系统 / 宿主换主题"的信号：本函数由 :func:`show_tetris`
        保证**只调一次**（控件已经进标签页了），正好是连线的好时机 —— 放进
        ``__init__`` 也行，但那时控件还没进窗口，连了也要等一次事件才生效。
        """
        self._connect_palette_signal()
        node = self.parent()
        while node is not None:
            close = getattr(node, 'close_tab_object', None)
            if callable(close):
                self.close_callback = lambda: close(self)
                return
            node = node.parent()

    def _connect_palette_signal(self) -> None:
        """监听 ``QApplication.paletteChanged``：用户换样式表 / 系统切深色时换肤。

        ⚠️ 信号源是 **QApplication 单例**（不是自己），生命周期长于本控件，所以
        控件销毁时要断开 —— 见 :meth:`cleanup_before_tab_close`。否则关掉标签页后
        再换主题，Qt 会去调一个已经析构的控件（抛 ``RuntimeError`` 或直接崩）。
        """
        if self._palette_hooked:
            return
        try:
            app = QApplication.instance()
            if app is not None:
                app.paletteChanged.connect(self._on_palette_changed)
                self._palette_hooked = True
        except Exception as err:            # pragma: no cover - 没 QApplication 就跳过
            print(f'Tetris: 未能监听主题变化（{err}）')

    def _disconnect_palette_signal(self) -> None:
        """断开主题信号（控件销毁前必须做，理由见 :meth:`_connect_palette_signal`）。"""
        if not self._palette_hooked:
            return
        self._palette_hooked = False
        try:
            app = QApplication.instance()
            if app is not None:
                app.paletteChanged.disconnect(self._on_palette_changed)
        except Exception:
            pass                            # 已断连 / 已销毁都无所谓

    def showEvent(self, event):             # noqa: N802
        """进入标签页：对齐时钟、续上计时器、取消自动暂停、抢焦点。

        ⚠️ **必须在这里取消暂停**（而不是在 ``hideEvent`` 里不暂停）：``hideEvent``
        里的自动暂停是给"切到后台"用的，若不在这里配一个"切回来就恢复"，玩家切回来
        会看到一个暂停卡片、要再按一次 P —— 更糟的是计时器已经在跑，游戏却是停的
        （状态自相矛盾）。

        ⚠️ 正在被关闭（``_closing``）时什么都不做：那时 ``hideEvent``/``showEvent``
        可能因为标签页被移除而交错触发，去启动计时器只会给一个即将销毁的控件续命。
        """
        super().showEvent(event)
        if self._closing:
            return
        self.last_ms = self.clock.elapsed()
        self.acc = 0.0
        if self.paused and self.game.phase not in ('dying', 'over'):
            self.paused = False             # 切回来即继续（不发音效，见下）
            self.audio.set_music(bool(self.opt['music']))
        if not self.timer.isActive():
            self.timer.start(max(1, int(1000 / FPS)))
        self.setFocus()

    def hideEvent(self, event):             # noqa: N802
        """离开标签页：停表，并**静默地**暂停。

        ⚠️ 这里**不走 ``toggle_pause()``**：那个函数会 ``audio.play('pause')`` 与
        ``set_music()``，而 ``hideEvent`` 在关标签页销毁控件的过程中也会被调到 ——
        往一个正在销毁的控件上播声音，正是"关闭时卡死/崩溃"的典型来源。
        状态直接改 ``self.paused``，声音一概不碰（关标签那条路径由
        :meth:`cleanup_before_tab_close` 统一静音）。

        ⚠️ 停表省 CPU，暂停则是不让玩家回来时看到一局已经堆死 —— 两者缺一不可。
        已经在结算动画 / 结算界面时不动暂停状态（那里本来就不接暂停）。
        """
        if self.timer.isActive():
            self.timer.stop()
        if not self._closing and not self.paused and self.game.phase not in ('dying', 'over'):
            self.paused = True
            self.game.release_all()         # 松开方向键，避免回来时"卡键"
        super().hideEvent(event)

    def cleanup_before_tab_close(self):
        """关闭标签页前的收尾（``TabWidget.close_tab`` 会 duck-typing 探测并调用）.

        ⚠️ 不许阻塞：这里只停表、断连、掐声音、存盘，不等任何东西。
        ⚠️ 不 ``wait()`` 任何东西 —— 本控件没有后台线程。

        ⚠️ **顺序要紧**：先置 ``_closing`` 并**停表断连**，再动音频。置位之后再
        触发的 ``hideEvent`` 就不会去改状态；停在计时器则保证 ``_frame`` 不会在
        销毁过程中再次进来（``deleteLater`` 与计时器回调都在事件循环里，抢到了
        就会操作一个半死的控件）。
        """
        self._closing = True
        try:
            self.timer.stop()
            try:
                self.timer.timeout.disconnect()
            except Exception:
                pass                        # 没连过 / 已断连都无所谓
            # ⚠️ 必须断开主题信号：它连在 **QApplication 单例**上，比本控件活得久，
            #    不断的话关掉标签页后再换主题就会调到一个已析构的控件上。
            self._disconnect_palette_signal()
            self.audio.set_music(False)
            self.audio.enabled = False      # 之后 play() 直接空转
            self.audio.players.clear()
            self.write_save(why='close_tab')     # 最高分 / 设置落盘
        except Exception as err:
            print(f'Error when closing tetris tab: {err}')

    def refresh(self):
        """GUI 刷新钩子（``MainWindow`` 每次切到本页都会调）.

        ⚠️ 必须**非常轻**：切标签是高频动作，里面不能读磁盘、不能重画。游戏的
        画面本来就每帧自己重绘，这里只需让控件重绘一次即可。
        """
        if not self._closing:
            self.update()


def show_tetris():
    """显示「方块」标签页（螺螺是方块游戏）—— 一个彩蛋.

    入口在「关于」页面的**「彩蛋」按钮**（见 ``zmlx/ui/tabs/about.py``），
    故意不挂菜单：它不是功能，是留给翻到「关于」页的人的惊喜。

    这个函数同时是 GUI 命令（``gui.show_tetris()``）。

    ⚠️ **刻意不设 ``widget.gui_restore``**：那是「重启后自动恢复本标签页」用的
    （``main.py`` 的 ``__save_tabs`` 会 ``getattr(widget, 'gui_restore', None)``
    并只收字符串，所以**不设就等于不恢复**）。游戏是个彩蛋：用户上次随手点开
    不代表下次启动还想接着玩，每次开机自动弹一个吃 CPU 的游戏标签页更不合适。
    要接着玩，再点一次「彩蛋」即可。

    ⚠️ 只通过 ``gui.get_widget`` 打开（而不是直接 ``TetrisView()``）：
    这样标签页只会有**一个**，重复调用只是把已有页面切到前面 —— 对游戏尤其
    重要，开两局会各跑一个 60 FPS 的计时器。
    """

    def oper(widget):
        # ★ 把"退出游戏"接到宿主的关标签流程上（见 TetrisWidget.request_close）。
        #   ⚠️ 必须在这里做：控件此时已经 addTab 进 TabWidget，parent() 链才通得了。
        #   放在 __init__ 里太早（那时还没有 parent，找不到宿主）。
        widget._bind_close_callback()

    gui.get_widget(
        TetrisView, caption=CAPTION, on_top=True,
        icon='demo', oper=oper,
        tooltip='螺螺是方块（Tetris）：← → 移动、↑ 旋转、空格硬降、C 暂存、P 暂停、F1 帮助')


@execute_once(file=__file__)
def setup_ui():
    """注册 GUI 命令并挂菜单「**帮助 → 彩蛋 → 螺螺是方块**」.

    ⚠️ 本插件声明了 ``# ** enabled = False``（默认不加载）。用户若在「设置 →
    插件」里勾上它，本函数才会被 ``run_setup`` 执行 —— 于是菜单才出现。
    换句话说：**菜单的可见性就是「用户有没有启用这个彩蛋」**，不需要另外的开关。

    ⚠️ 作为插件，顶层**必须自己调**这个函数（见文件末尾）—— 没有谁会替它调。

    ⚠️ 本函数在**控制台内核线程**里执行，``gui.add_func`` / ``gui.add_action``
    会被 GuiApi 派发到主线程执行（见 ``zmlx/ui/main.py`` 的 ``__console_kernel``）。
    """
    gui.add_func('show_tetris', show_tetris)
    gui.add_action(
        menu=['帮助', '彩蛋'],
        text='螺螺是方块',
        slot=show_tetris,
        tooltip='彩蛋游戏：俄罗斯方块（← → 移动、↑ 旋转、空格硬降、C 暂存、P 暂停）',
    )


def test_1():
    """直接运行本文件时的自测：单独开一个窗口把游戏跑起来。"""
    if QtWidgets is None:
        print('No Qt binding available.')
        return
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    widget = TetrisView()
    widget.resize(BASE_W, BASE_H)
    widget.show()
    app.exec()


if __name__ == '__zml_plugin__':
    # 插件机制执行时 ``__name__`` 是 ``'__zml_plugin__'``：只注册命令，别开窗口。
    setup_ui()
elif __name__ == '__main__':
    # ``python tetris.py`` 直接运行：开一个窗口自测。
    test_1()
