"""把 ``shapes.py`` 里的图标渲染成 PNG，写进 ``zmlx/ui/data/zml_icons/``。

用法（在仓库根 ``projects/zml/`` 下）::

    python zmlx/ui/data/zml_icons/icons_src/build.py

输出
----
- ``icons_src/svg/<name>.svg``：工具栏图标的 SVG 源文件（可单独编辑 / 浏览）；
- ``../<name>.png``：**每个工具栏图标只有这一张**，128x128、透明底、浅灰白圆角底衬。
  显示时由 Qt 缩放到工具栏的实际尺寸（本机实测 24px）；
- ``../app.png``：应用图标（窗口图标），128x128、透明底。它自己就是完整画面
  （整块渐变圆角方块），不套工具栏图标的底衬。

⚠️ ``app`` 是应用图标，不是工具栏图标 —— 规则不同（自己就是完整画面、
不套底衬、带渐变），单独在 :func:`make_app` 里处理。
⚠️ 这里**只新增文件**：删不删旧图标是人工决定的事（见 ``README.md``）。
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.dirname(HERE)
SVG_DIR = os.path.join(HERE, 'svg')

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import shapes  # noqa: E402

# 由 PyQt 提供渲染能力；无 PyQt 时脚本给出明确提示而不是一堆 ImportError
try:
    from PyQt6 import QtCore, QtGui, QtSvg, QtWidgets
except ImportError:  # pragma: no cover
    print('需要 PyQt6 才能渲染图标（本项目 GUI 自带该依赖）')
    raise

ICON_SIZE = 128         # 工具栏图标唯一的尺寸（显示时由 Qt 缩放到实际大小）
APP_SIZE = 128          # 应用图标（窗口图标）的边长


def render(svg_text, size):
    """把 SVG 文本渲染成 QImage（透明底）。"""
    renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(svg_text.encode('utf-8')))
    if not renderer.isValid():
        raise ValueError(f'invalid svg at {size}px')
    img = QtGui.QImage(size, size, QtGui.QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(img)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter, QtCore.QRectF(0, 0, size, size))
    painter.end()
    return img


def build_toolbar_icons():
    """工具栏图标：SVG 源 + 每个图标一张 128px PNG。返回写出的文件数。

    ⚠️ 不画底衬（``plate=None``）：图标只有图形本身，其余部分是**透明**的，
    这样它会跟着所在位置的底色走 —— 白色 / 深色主题、工具栏、菜单里都不会
    露出一块多余的浅色方块。
    """
    os.makedirs(SVG_DIR, exist_ok=True)
    written = 0
    for name, body in shapes.ICONS.items():
        with open(os.path.join(SVG_DIR, name + '.svg'), 'w', encoding='utf-8') as f:
            f.write(shapes.svg(body, size=ICON_SIZE))
        img = render(shapes.svg(body, size=ICON_SIZE), ICON_SIZE)
        img.save(os.path.join(TARGET, name + '.png'), 'PNG')
        written += 1
    return written


def make_app():
    """应用图标：一张 ``app.png``。返回写出的文件数。

    ⚠️ 不用 ``.ico``：``settings.find_icon_file`` 只找 ``.png`` / ``.jpg``，
    ``load_icon('app')`` 根本不会去读 ``app.ico`` —— 窗口图标会静默变成空的。
    """
    img = render(shapes.svg(shapes.APP_ICON, size=APP_SIZE), APP_SIZE)
    img.save(os.path.join(TARGET, 'app.png'), 'PNG')
    return 1


def main():
    # QGuiApplication 必须先建：QPixmap / QImage 都不能在没有应用对象时构造
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)  # noqa: F841
    print('toolbar icons:', build_toolbar_icons(), 'files')
    print('app icon:', make_app(), 'file')


if __name__ == '__main__':
    main()
