import zmlx.alg.sys as warnings

from zmlx.alg.image import convert_png_to_jpg

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

if __name__ == '__main__':
    from zmlx.ui.data.path import get_path

    folder_path = get_path('zml_icons')
    convert_png_to_jpg(folder_path)
