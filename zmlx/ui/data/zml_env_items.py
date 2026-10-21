"""环境变量模板生成（生成 zml_env_items.json 配置文件）.

⚠️⚠️ **本表是「设置 → 系统」界面的唯一真值来源**。每一项里的 ``default``
必须与 **zmlx 代码里真正采用的默认值** 逐字一致 —— 界面就是按它来初始化控件
的，写错了界面就会撒谎（显示一个代码根本不会用的值）。

写法约定
--------
每个条目：

- ``label``  / ``key`` / ``note``：展示用的文字；
- ``kind``：控件类型，决定界面画什么控件、怎么读值 / 写值：

  ==========  ==============================  ==================
  ``kind``    控件                             默认值放在哪
  ==========  ==============================  ==================
  ``bool``    ``QCheckBox``                  ``default`` = ``True`` / ``False``
  ``enum``    ``QComboBox``（首项「默认」）    ``default`` = 某项的文字
  ``int``     ``QSpinBox``                    ``default`` + ``min``/``max``
  ``str``     ``QLineEdit``                   ``default`` = 字符串
  ==========  ==============================  ==================

- ``default``：**代码真正采用的值**（键未设置 / 为空时生效的那个值），必填；
- ``note``：说明文字，末尾统一写出「默认 …」。

判据来源（改本表前先去读这几处，别凭印象写）：

======================  ========================================================
key                     判定代码
======================  ========================================================
``TabPosition``         ``zmlx/ui/alg.py`` 的 ``set_position()``
``TabShape``            ``zmlx/ui/alg.py`` 的 ``set_shape()``
``console_priority``    ``zmlx/ui/settings.py`` 的 ``load_priority()``
``Qt_version``          ``zmlx/ui/pyqt.py``（空 → 优先 PyQt6，再退 PyQt5）
``disable_timer``       ``zmlx/exts/__init__.py``（``== 'Yes'`` 才禁用）
``disable_splash``      ``zmlx/ui/main.py`` 的 ``__make_splash()``（``== 'Yes'`` 才禁用）
``use_web_engine``      ``zmlx/ui/alg.py`` 的 ``open_url()``（``!= 'No'`` 即启用）
``restore_tabs``        ``zmlx/ui/gui_buffer.py`` 的 ``open_gui()``
``init_check``          同上
``show_readme``         ``zmlx/ui/main.py``（``!= 'No'``）
``restore_console_output``  ``zmlx/ui/main.py`` 的 ``__restore_history()``
``disable_auto_feedback``   ``zmlx/__init__.py`` 底部（``!= 'Yes'`` 才发送）
``restore_window_geometry`` ``zmlx/ui/settings.py`` 的 ``load_window_size()``
``load_window_style``   ``zmlx/ui/main.py`` 的 ``__on_show()``
``show_info_after_code_open``  ``zmlx/ui/main.py``（``!= 'No'``）
``plt_export_dpi``      ``zmlx/io/env/plt_export_dpi.py``（合法区间 50~3000）
======================  ========================================================

Modified by Claude, 2026-08-12
Modified by DeepSeek, 2026-10-18: 新增 ``kind`` / ``default`` 字段 —— 界面按
「代码真正采用的值」初始化控件，不再一律显示空 / 未勾选。
"""

import os.path


def main():
    from zmlx.io.json_ex import write
    data = [
        dict(label='主界面标签位置', key='TabPosition', kind='enum',
             items=['North', 'East', 'South', 'West'],
             default='North',
             note='标签页在窗口中的停靠位置。可选东/南/西/北四个方向，默认 North（顶部）'),
        dict(label='主界面标签形状', key='TabShape', kind='enum',
             items=['Rounded', 'Triangular'],
             default='Rounded',
             note='标签页的形状样式。可选 Rounded（圆角）或 Triangular（三角），默认 Rounded。'
                  '注：仅对 PyQt5 有效'),
        dict(label='控制台内核优先级', key='console_priority', kind='enum',
             items=['LowestPriority', 'LowPriority',
                    'InheritPriority', 'NormalPriority',
                    'HighPriority', 'HighestPriority'],
             default='LowPriority',
             note='后台计算线程的系统优先级。默认 LowPriority（低优先级）—— 保证整机稳定。'
                  '提高可加速计算，但可能影响界面响应流畅度'),
        dict(label='是否禁用计时器', key='disable_timer', kind='bool',
             default=False,
             note='禁用后不再统计各函数的 CPU 耗时，可略微减轻运行时开销。默认 No（启用计时）'),
        dict(label='是否禁用启动画面', key='disable_splash', kind='bool',
             default=False,
             note='控制启动时是否显示 IGG-Hydrate 启动画面（闪屏）。默认 No（显示启动画面）'),
        dict(label='使用WebEngine', key='use_web_engine', kind='bool',
             default=True,
             note='控制打开网页/PDF 时是否在软件内部渲染。默认 Yes（内嵌显示）；'
                  'No 时调用系统默认浏览器打开'),
        dict(label='恢复关闭时的标签', key='restore_tabs', kind='bool',
             default=True,
             note='重启软件时自动恢复上次关闭前打开的文件和标签页。默认 Yes。'
                  '注意：并非所有标签类型都支持恢复'),
        dict(label='启动时显示ReadMe', key='show_readme', kind='bool',
             default=True,
             note='启动软件时自动打开 ReadMe 帮助页面（如无其他标签恢复）。默认 Yes'),
        dict(label='启动时恢复控制台输出', key='restore_console_output', kind='bool',
             default=True,
             note='重启后恢复上次会话的控制台输出历史（仅恢复小于 0.5MB 的输出文件）。默认 Yes'),
        dict(label='不向开发者反馈', key='disable_auto_feedback', kind='bool',
             default=False,
             note='控制是否自动向开发者发送程序错误日志，仅用于改进软件质量。'
                  '默认 No（允许反馈）；Yes 时完全不发送任何信息'),
        dict(label='Qt版本', key='Qt_version', kind='enum',
             items=['PyQt6', 'PyQt5'],
             default='PyQt6',
             note='优先使用的 Qt 绑定版本。默认 PyQt6；若指定的版本没有安装，'
                  '会自动回退到另一个已安装的版本。注：即将停止对 PyQt5 的支持'),
        dict(label='启动时恢复上次视窗大小', key='restore_window_geometry', kind='bool',
             default=True,
             note='重启时恢复上次关闭时的窗口大小和屏幕位置。默认 Yes（恢复）；'
                  'No 时使用默认位置（屏幕中央，约 3/4 屏幕大小）'),
        dict(label='启动时载入窗口的风格', key='load_window_style', kind='bool',
             default=True,
             note='控制是否加载用户自定义的 QSS 窗口样式表。默认 Yes（加载自定义风格）；'
                  'No 时使用 Qt 原生默认风格'),
        dict(label='打开脚本后显示提示', key='show_info_after_code_open', kind='bool',
             default=True,
             note='打开 Python 脚本后在控制台显示"文件已打开，请点击运行按钮"的提示信息。默认 Yes'),
        dict(label='导出 Matplotlib 绘图时的默认 DPI', key='plt_export_dpi', kind='int',
             default=300, min=50, max=3000,
             note='导出 Matplotlib 图片时的默认分辨率（每英寸像素数），取值范围 50~3000，'
                  '默认 300。值越大图片越清晰但文件越大。也可在绘图页面右键菜单中单独设置'),
    ]
    fname = os.path.join(os.path.dirname(__file__), 'zml_env_items.json')
    write(fname, data, encoding='utf-8')


if __name__ == '__main__':
    main()
