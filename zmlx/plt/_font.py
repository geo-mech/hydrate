"""
matplotlib 字体配置工具。

Modified by Claude, 2026-08-12

Modified by DeepSeek, 2026-11-02: 字体族名改读字体管理器缓存（.ttc 里的多字族原先匹配不上，
中文于是退到楷体或 DejaVu）；新增 ensure_chinese_font()，供「每次绘制前」幂等地补回来
"""

import sys

from zmlx.system import execute_once, in_windows, in_linux, in_macos

#: 进程内缓存：当前系统**实际存在**的候选中文字体名（按优先级）。
_cjk_fonts = None


def list_chinese_fonts():
    """返回当前系统里存在的中文字体名（按优先级排序，可能为空）.

    只在首次调用时读一次 matplotlib 的字体缓存，之后返回同一份列表的副本。

    Returns:
        List[str]: 字体族名，例如 ``['Noto Sans CJK SC', 'AR PL UKai CN']``。

    Notes:
        ⚠️ 一律从字体管理器的**缓存**取名字，不要扫盘逐个字体文件去建集合：一个
        ``.ttc`` 里打包了多个字族（如 ``NotoSansCJK-Regular.ttc`` 同时提供
        SC/TC/JP/KR 四套名字），而 ``FontProperties(fname=...).get_name()`` 只返回
        其中排在最前的那一个 —— 实测扫盘结果里整个 Noto CJK 集合只剩
        ``Noto Sans CJK JP``，``Noto Sans CJK SC`` 永远匹配不上，Linux 于是退到
        ``AR PL UKai CN``（楷体），与候选顺序的意图正好相反。
    """
    global _cjk_fonts
    if _cjk_fonts is None:
        try:
            import matplotlib.font_manager as fm
            available_fonts = set(fm.get_font_names())
        except Exception:
            available_fonts = set()

        if in_windows():
            preferred_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi']
        elif in_linux():
            preferred_fonts = [
                'Noto Sans CJK SC', 'Noto Sans CJK SC Regular', 'Noto Serif CJK SC',
                'Noto Sans CJK TC', 'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei',
                'AR PL UKai CN', 'AR PL UMing CN', 'Droid Sans Fallback',
            ]
        elif in_macos():
            preferred_fonts = ['PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'Apple SD Gothic Neo', 'Songti SC']
        else:
            preferred_fonts = []

        _cjk_fonts = [font for font in preferred_fonts if font in available_fonts]
    return list(_cjk_fonts)


@execute_once
def set_chinese_font():
    """设置 matplotlib 中文字体，确保图表中的中文能正常显示。

    ⚠️ 本函数带 ``@execute_once``，进程内只真正执行一次；之后若有
    ``plt.style.use('default')`` 之类把 ``font.sans-serif`` 重置回 ``DejaVu Sans``，
    这里**补不回来** —— 那种场合请在每次绘制前调用幂等的
    :func:`ensure_chinese_font`（GUI 的 ``MatplotWidget`` 就是这么做的）。
    """
    try:
        import matplotlib

        selected_fonts = list_chinese_fonts()
        # ``DejaVu Sans`` 没有中文字形，只能做兜底，**必须排在最后**：它排在候选前面时
        # 中文会画成方框（``Glyph ... missing from font(s) DejaVu Sans``）。
        if 'DejaVu Sans' not in selected_fonts:
            selected_fonts.append('DejaVu Sans')

        matplotlib.rcParams.update({
            'font.sans-serif': selected_fonts,
            'font.family': 'sans-serif',
            'axes.unicode_minus': False,
            'axes.labelsize': 'large',
            'legend.fontsize': 'large',
        })
    except Exception as font_err:
        print(f'Error when set font: {font_err}', file=sys.stderr)


def ensure_chinese_font():
    """把中文字体排到 ``font.sans-serif`` 队首，并让负号用 ASCII ``-``（**幂等**）.

    与 :func:`set_chinese_font` 的区别是**没有** ``@execute_once``：它每次调用都检查
    当前 ``rcParams``，已经正确时什么都不改，被 ``style.use(...)`` 重置过就重新补回来。
    成本只是一次列表比较（字体名走 :func:`list_chinese_fonts` 的进程内缓存），
    可以直接放在「每次绘制前」的路径上。

    Returns:
        List[str]: 最终排在队首的中文字体名；系统里一个都没有时返回 ``[]``。
    """
    try:
        import matplotlib as mpl

        # 负号：``axes.unicode_minus=True`` 时写成 U+2212（数学减号），而 SimHei
        # 这类中文字体恰好没有这个字形，刻度会画成小方框。换 ASCII '-' 则所有
        # 中文字体都覆盖。
        mpl.rcParams['axes.unicode_minus'] = False
        mpl.rcParams['axes.labelsize'] = 'large'
        mpl.rcParams['legend.fontsize'] = 'large'

        found = list_chinese_fonts()

        family = list(mpl.rcParams['font.family'])
        if 'sans-serif' not in family:
            mpl.rcParams['font.family'] = ['sans-serif'] + [
                name for name in family if name != 'sans-serif']

        if len(found) == 0:  # 没有任何中文字体可用，保持现状（告警无意义，只会刷屏）
            return []

        current = list(mpl.rcParams['font.sans-serif'])
        if current[:len(found)] == found:  # 已经排在队首，什么都不改
            return found
        mpl.rcParams['font.sans-serif'] = found + [
            name for name in current if name not in found]
        return found
    except Exception as font_err:
        print(f'Error when ensure chinese font: {font_err}', file=sys.stderr)
        return []
