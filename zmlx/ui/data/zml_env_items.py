import os.path


def main():
    from zmlx.io.json_ex import write
    data = [
        dict(label='主界面标签位置', key='TabPosition',
             items=['', 'North', 'East', 'South', 'West'],
             note='标签页在窗口中的停靠位置，默认 North（顶部），可选东/南/西/北四个方向'),
        dict(label='主界面标签形状', key='TabShape',
             items=['', 'Rounded', 'Triangular'],
             note='标签页的形状样式。默认 Rounded（圆角），可选 Triangular（三角）。注：仅对 PyQt5 有效'),
        dict(label='控制台内核优先级', key='console_priority',
             items=['', 'LowestPriority', 'LowPriority',
                    'InheritPriority', 'NormalPriority',
                    'HighPriority', 'HighestPriority'],
             note='后台计算线程的系统优先级。默认 LowPriority（低优先级），提高可加速计算，但可能影响界面响应流畅度'),
        dict(label='是否禁用计时器', key='disable_timer',
             items=['', 'Yes', 'No'],
             note='禁用后不再统计各函数的 CPU 耗时，可略微减轻运行时开销。默认 No（启用计时）'),
        dict(label='是否禁用启动画面', key='disable_splash',
             items=['', 'Yes', 'No'],
             note='控制启动时是否显示 IGG-Hydrate 启动画面（闪屏）。默认 No（显示启动画面）'),
        dict(label='使用WebEngine', key='use_web_engine',
             items=['', 'Yes', 'No'],
             note='控制打开网页/PDF 时是否在软件内部渲染。默认 Yes（内嵌显示）；No 时调用系统默认浏览器打开'),
        dict(label='恢复关闭时的标签', key='restore_tabs',
             items=['', 'Yes', 'No'],
             note='重启软件时自动恢复上次关闭前打开的文件和标签页。默认 Yes。注意：并非所有标签类型都支持恢复'),
        dict(label='启动时显示ReadMe', key='show_readme',
             items=['', 'Yes', 'No'],
             note='启动软件时自动打开 ReadMe 帮助页面（如无其他标签恢复）。默认 Yes'),
        dict(label='启动时恢复控制台输出', key='restore_console_output',
             items=['', 'Yes', 'No'],
             note='重启后恢复上次会话的控制台输出历史（仅恢复小于 0.5MB 的输出文件）。默认 Yes'),
        dict(label='启动时检查授权', key='check_lic_when_start',
             items=['', 'Yes', 'No'],
             note='启动时联网校验许可证有效性。默认 No（跳过检查，启动更快）；Yes 时需联网并可能增加启动耗时'),
        dict(label='不向开发者反馈', key='disable_auto_feedback',
             items=['', 'Yes', 'No'],
             note='控制是否自动向开发者发送程序错误日志，仅用于改进软件质量。默认 No（允许反馈）；Yes 时完全不发送任何信息'),
        dict(label='Qt版本', key='Qt_version',
             items=['', 'PyQt5', 'PyQt6'],
             note='优先使用的 Qt 绑定版本。默认 PyQt6。注意：即将停止对 PyQt5 的支持'),
        dict(label='启动时恢复上次视窗大小', key='restore_window_geometry',
             items=['', 'Yes', 'No'],
             note='重启时恢复上次关闭时的窗口大小和屏幕位置。默认 Yes（恢复）；No 时使用默认位置（屏幕中央，约 3/4 屏幕大小）'),
        dict(label='启动时载入窗口的风格', key='load_window_style',
             items=['', 'Yes', 'No'],
             note='控制是否加载用户自定义的 QSS 窗口样式表。默认 Yes（加载自定义风格）；No 时使用 Qt 原生默认风格'),
        dict(label='打开脚本后显示提示', key='show_info_after_code_open',
             items=['', 'Yes', 'No'],
             note='打开 Python 脚本后在控制台显示"文件已打开，请点击运行按钮"的提示信息。默认 Yes'),
        dict(label='导出 Matplotlib 绘图时的默认 DPI', key='plt_export_dpi',
             note='导出 Matplotlib 图片时的默认分辨率（每英寸像素数），值越大图片越清晰但文件越大。也可在绘图页面右键菜单中单独设置'),
    ]
    fname = os.path.join(os.path.dirname(__file__), 'zml_env_items.json')
    write(fname, data, encoding='utf-8')


if __name__ == '__main__':
    main()
