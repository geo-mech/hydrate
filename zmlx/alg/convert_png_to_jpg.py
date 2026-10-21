"""已弃用的模块，请改用 zmlx.alg.image.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.alg.image import convert_png_to_jpg

warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

if __name__ == '__main__':
    from zmlx.ui.data import get_path

    folder_path = get_path('zml_icons')
    convert_png_to_jpg(folder_path)
