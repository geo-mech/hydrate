"""
matplotlib 字体配置工具。
"""
from zmlx.system import execute_once, in_windows, in_linux, in_macos


@execute_once
def set_chinese_font():
    """设置 matplotlib 中文字体，确保图表中的中文能正常显示。"""
    try:
        import matplotlib
        import matplotlib.font_manager as fm

        font_list = fm.findSystemFonts(fontext='ttf') + fm.findSystemFonts(fontext='otf')
        available_fonts = set()
        for font_path in font_list:
            try:
                available_fonts.add(fm.FontProperties(fname=font_path).get_name())
            except Exception:
                pass

        if in_windows():
            preferred_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi', 'DejaVu Sans']
        elif in_linux():
            preferred_fonts = [
                'Noto Sans CJK SC', 'Noto Sans CJK SC Regular', 'Noto Serif CJK SC',
                'Noto Sans CJK TC', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei',
                'AR PL UKai CN', 'AR PL UMing CN', 'DejaVu Sans', 'DejaVu Serif',
                'Liberation Sans', 'Liberation Serif', 'Droid Sans Fallback',
            ]
        elif in_macos():
            preferred_fonts = ['PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'Apple SD Gothic Neo', 'Songti SC',
                               'DejaVu Sans']
        else:
            preferred_fonts = ['DejaVu Sans']

        selected_fonts = [font for font in preferred_fonts if font in available_fonts] or ['DejaVu Sans']

        matplotlib.rcParams.update({
            'font.sans-serif': selected_fonts,
            'font.family': 'sans-serif',
            'axes.unicode_minus': False,
            'axes.labelsize': 'large',
            'legend.fontsize': 'large',
        })
    except Exception as font_err:
        print(f'Error when set font: {font_err}')
