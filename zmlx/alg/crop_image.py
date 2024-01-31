from PIL import Image
import os
from zmlx.filesys.make_parent import make_parent


def crop_image(output_path, input_path, left, upper, right, lower):
    """
    从输入图像中裁剪矩形区域，并保存为新的图像

    参数：
    output_path: str，输出图像的文件路径
    input_path: str，输入图像的文件路径
    left: int，矩形区域左上角的x坐标
    upper: int，矩形区域左上角的y坐标
    right: int，矩形区域右下角的x坐标
    lower: int，矩形区域右下角的y坐标
    """
    if os.path.isdir(input_path):
        for name in os.listdir(input_path):
            ipath = os.path.join(input_path, name)
            if os.path.isfile(ipath):
                ext = os.path.splitext(name)[1]
                if ext in ['.jpg', '.png']:
                    opath = os.path.join(output_path, name)
                    make_parent(opath)
                    crop_image(opath, ipath, left=left, upper=upper, right=right, lower=lower)
        return
    else:
        try:
            print(f'Crop "{input_path}" -> "{output_path}" .. ', end='')
            # 打开输入图像
            input_image = Image.open(input_path)

            # 使用crop函数裁剪指定的矩形区域
            cropped_image = input_image.crop((left, upper, right, lower))

            # 保存裁剪后的图像
            cropped_image.save(output_path)
            # print(f"成功裁剪并保存到 {output_path}")
            print('Succeed!')
        except Exception as e:
            print(f'Failed. Reason: {e}')


def test():
    output_image_path = "output.jpg"  # 输出图像的路径
    input_image_path = "input.jpg"  # 输入图像的路径
    left_coord = 100  # 矩形区域左上角的x坐标
    upper_coord = 50  # 矩形区域左上角的y坐标
    right_coord = 300  # 矩形区域右下角的x坐标
    lower_coord = 200  # 矩形区域右下角的y坐标

    crop_image(output_image_path, input_image_path, left_coord, upper_coord, right_coord, lower_coord)
