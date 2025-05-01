import warnings

from zmlx.alg.image import crop_image

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)




def test():
    output_image_path = "output.jpg"  # 输出图像的路径
    input_image_path = "input.jpg"  # 输入图像的路径
    left_coord = 100  # 矩形区域左上角的x坐标
    upper_coord = 50  # 矩形区域左上角的y坐标
    right_coord = 300  # 矩形区域右下角的x坐标
    lower_coord = 200  # 矩形区域右下角的y坐标

    crop_image(output_image_path, input_image_path, left_coord, upper_coord,
               right_coord, lower_coord)
