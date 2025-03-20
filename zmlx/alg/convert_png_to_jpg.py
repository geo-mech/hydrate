import os

from PIL import Image


def convert_png_to_jpg(folder_path):
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.endswith('.png'):
            # 构造 PNG 图片的完整路径
            png_path = os.path.join(folder_path, filename)

            # 打开 PNG 图片并转换为 JPEG 格式
            with Image.open(png_path) as img:
                # 构造 JPEG 图片的文件名
                jpg_filename = os.path.splitext(filename)[0] + '.jpg'
                jpg_path = os.path.join(folder_path, jpg_filename)

                # 将 PNG 图片转换为 JPEG 格式
                img.convert('RGB').save(jpg_path, 'JPEG')

            # 删除原始的 PNG 图片
            os.remove(png_path)
            print(f"{filename} 转换为 {jpg_filename}，并删除原始 PNG 图片")


if __name__ == '__main__':
    from zmlx.ui.data.get_path import get_path

    folder_path = get_path('zml_icons')
    convert_png_to_jpg(folder_path)
