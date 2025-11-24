"""
图像相关的工具函数
"""
import os

import zmlx.alg.sys as warnings
from zmlx.base.zml import make_parent, np
from zmlx.io import json_ex

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


def make_video(video_name, image_folder, fps=30, img_ext='.jpg'):
    """
    将给定文件夹中的给定扩展名的图片合成一个视频.
    """
    import cv2  # python -m pip install opencv-python

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


def get_data(img, cmap, *, vmin=0.0, vmax=1.0, xmin=None, xmax=None, ymin=None, ymax=None, values=None):
    """
    读取云图和对应的colormap，将之转化为矩阵或者插值
    Args:
        img: 云图（一个三维的numpy矩阵）或者路径（一个图片的路径）
        cmap: colormap或者colormap的图片路径
        vmin: colormap的最小值
        vmax: colormap的最大值
        xmin: 云图的x最小值
        xmax: 云图的x最大值
        ymin: 云图的y最小值
        ymax: 云图的y最大值
        values: colormap的数值
    返回:
        一个矩阵或者一个插值
    注意:
        此算法采用NearestNDInterpolator来进行插值，因此如果colormap的颜色比较少，则会
        有数据精度的损失.
    Since 2023-12-17. by ZZB
    最后修改  2025-8-23  新增功能：可以指定xmin, xmax, ymin, ymax
    """
    if isinstance(cmap, str):  # 读取图片
        assert os.path.isfile(cmap)
        cmap = np.array(Image.open(cmap))
        assert len(cmap.shape) == 2 or len(cmap.shape) == 3
        if len(cmap.shape) == 2:
            cmap = cmap[:, :, np.newaxis]
        # 压扁
        if cmap.shape[0] < cmap.shape[1]:
            points = np.mean(cmap, axis=0)
            if values is None:
                values = np.linspace(vmin, vmax, cmap.shape[1])
        else:
            points = np.mean(cmap, axis=1)
            if values is None:
                values = np.linspace(vmax, vmin, cmap.shape[0])
    else:  # 直接假设它就是一些颜色，从上到下，对应的值从小到大
        cmap = np.asarray(cmap)
        points = cmap
        if values is None:
            values = np.linspace(vmin, vmax, cmap.shape[0])
    # 生成插值
    cmap_interp = NearestNDInterpolator(points, values, rescale=True)  # 确保数值范围为[0, 1]

    if isinstance(img, str):  # 读取图片
        assert os.path.isfile(img)
        img = np.array(Image.open(img))

    assert len(img.shape) == 2 or len(img.shape) == 3
    if len(img.shape) == 2:
        img = img[:, :, np.newaxis]

    # 插值获取值
    points = [img[:, :, i] for i in range(img.shape[2])]
    data = cmap_interp(*points)
    assert len(data.shape) == 2

    # 如果没有给定x或者y的范围，则直接返回矩阵
    if xmin is None or xmax is None or ymin is None or ymax is None:
        return data

    vx = np.linspace(xmin, xmax, data.shape[1])
    vy = np.linspace(ymax, ymin, data.shape[0])
    x, y = np.meshgrid(vx, vy)
    x = x.flatten()
    y = y.flatten()
    v = data.flatten()

    # 返回插值，后续作为函数使用
    return NearestNDInterpolator((x, y), v, rescale=False)


def load_field(option, folder=None):
    """
    读取图片，并且转化为一个插值场
    """
    if folder is None:
        if isinstance(option, str):
            assert os.path.isfile(option)
            folder, ext = os.path.splitext(option)
            assert len(ext) >= 2
            assert ext[0] == '.'
            option = json_ex.read(option)

    if isinstance(option, str):
        if os.path.isfile(option):
            option = json_ex.read(option)
        else:
            if isinstance(folder, str):
                if os.path.isfile(os.path.join(folder, option)):
                    option = json_ex.read(os.path.join(folder, option))

    if not isinstance(option, dict):
        return None

    img = option.pop('img', 'field.jpg')
    cmap = option.pop('cmap', 'cmap.jpg')

    assert isinstance(img, str)
    if not os.path.isfile(img):
        if os.path.isfile(os.path.join(folder, img)):
            img = os.path.join(folder, img)

    if isinstance(cmap, str):
        if not os.path.isfile(cmap):
            if os.path.isfile(os.path.join(folder, cmap)):
                cmap = os.path.join(folder, cmap)

    return get_data(img, cmap, **option)
