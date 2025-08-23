"""
图像相关的工具函数
"""
import os

import zmlx.alg.sys as warnings
from zmlx.io import json_ex
from zml import make_parent, np

try:
    from PIL import Image
except ImportError as err:
    Image = None
    warnings.warn(f'{err}', ImportWarning)

try:
    from scipy.interpolate import NearestNDInterpolator
except ImportError as err:
    NearestNDInterpolator = None
    warnings.warn(f'{err}', ImportWarning)

import glob

try:
    import cv2  # python -m pip install opencv-python
except ImportError as err:
    cv2 = None
    warnings.warn(f'{err}', ImportWarning)


def make_video(video_name, image_folder, fps=30, img_ext='.jpg'):
    """
    将给定文件夹中的给定扩展名的图片合成一个视频.
    """
    # 获取图片列表
    images = [img for img in glob.glob(f"{image_folder}/*{img_ext}")]

    # 按文件名排序，确保图片按正确顺序添加
    images.sort()

    # 获取一张图片以获取视频尺寸
    frame = cv2.imread(images[0])
    height, width, layers = frame.shape

    # 定义视频编码器和输出视频
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 定义编码器
    video = cv2.VideoWriter(video_name, fourcc, fps, (width, height))

    for image in images:
        print(image)
        video.write(cv2.imread(image))

    # 释放视频文件
    video.release()


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
                    crop_image(opath, ipath, left=left, upper=upper,
                               right=right, lower=lower)
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


def get_data(img_name, map_name, *, vmin=0.0, vmax=1.0, xmin=None, xmax=None, ymin=None, ymax=None):
    """
    读取云图和对应的colormap，将之转化为矩阵。其中:
        img_name: 云图的文件名(图片)
        map_name: colormap的文件名(图片). 应该尽量保证colormap图片为长方形. 当
            图片宽度>高度的时候: 左侧颜色对应数值vmin，右侧对应数值vmax
            图片宽度<高度的时候: 下方颜色对应数值vmin，上方对应数值vmax
    返回:
        一个矩阵（大小和fig_name图片一致），矩阵的元素从vmin到vmax.
    注意:
        此算法采用NearestNDInterpolator来进行插值，因此如果colormap的颜色比较少，则会
        有数据精度的损失.
    Since 2023-12-17. by ZZB
    最后修改  2025-8-23  新增功能：可以指定xmin, xmax, ymin, ymax
    """
    if not os.path.isfile(img_name) or not os.path.isfile(map_name):
        return None

    # 创建cmap
    cmap_image = np.array(Image.open(map_name))
    rows, cols, cmap_dims = cmap_image.shape
    assert 1 <= cmap_dims <= 4
    points = np.hstack(
        [cmap_image[:, :, i].reshape(rows * cols, 1) for i in range(cmap_dims)])
    [i0, i1] = np.meshgrid(range(cols), range(rows))
    if rows < cols:
        values = i0.reshape(rows * cols, 1) / cols
    else:
        values = 1 - i1.reshape(rows * cols, 1) / rows
    cmap = NearestNDInterpolator(points, values, rescale=False)

    # 读取数据
    field_image = np.array(Image.open(img_name))
    field_dims = field_image.shape[2]
    assert field_dims == cmap_dims
    assert 1 <= field_dims <= 4
    points = [field_image[:, :, i] for i in range(field_dims)]

    # 插值
    data = cmap(*points) * (vmax - vmin) + vmin

    # 获取结果
    if len(data.shape) == 3:
        data = data[:, :, 0]  # 转换称为二维的

    # 如果没有给定x或者y的范围，则直接返回矩阵
    if xmin is None or xmax is None or ymin is None or ymax is None:
        return data

    # 给定了范围，则尝试将结果转化为后续更加方便使用的插值体
    assert xmin < xmax
    assert ymin < ymax

    vx = np.linspace(xmin, xmax, data.shape[1])
    vy = np.linspace(ymax, ymin, data.shape[0])
    x, y = np.meshgrid(vx, vy)

    # 转化为数据点，后续插值
    x = x.flatten()
    y = y.flatten()
    v = data.flatten()

    # 返回插值，后续作为函数使用
    return NearestNDInterpolator((x, y), v, rescale=False)


def load_field(option, folder=None):

    if folder is None:
        if isinstance(option, str):
            assert os.path.isfile(option)
            folder, ext = os.path.splitext(option)
            assert len(ext) >= 2
            assert ext[0] == '.'
            option = json_ex.read(option)

    if isinstance(option, str):
        option = json_ex.read(option)

    if not isinstance(option, dict):
        return None

    img_name = option.get('img_name', 'field.jpg')
    map_name = option.get('map_name', 'cmap.jpg')
    assert isinstance(img_name, str)
    assert isinstance(map_name, str)

    if not os.path.isfile(img_name):
        img_name = os.path.join(folder, img_name)
        assert os.path.isfile(img_name)

    if not os.path.isfile(map_name):
        map_name = os.path.join(folder, map_name)
        assert os.path.isfile(map_name)

    vmin = option.get('vmin')
    vmax = option.get('vmax')
    assert isinstance(vmin, (int, float))
    assert isinstance(vmax, (int, float))
    assert vmin < vmax

    xmin = option.get('xmin')
    xmax = option.get('xmax')
    assert isinstance(xmin, (int, float))
    assert isinstance(xmax, (int, float))
    assert xmin < xmax

    ymin = option.get('ymin')
    ymax = option.get('ymax')
    assert isinstance(ymin, (int, float))
    assert isinstance(ymax, (int, float))
    assert ymin < ymax

    return get_data(img_name, map_name, vmin=vmin, vmax=vmax, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax)

