import glob

import cv2  # python -m pip install opencv-python


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


def test():
    # 设置图片文件夹和输出视频文件名
    image_folder = r'D:\MyData\co2\base\inh'  # 替换为你的图片文件夹路径
    video_name = r'D:\MyData\co2\base\inh.mp4'

    # 调用函数
    make_video(image_folder=image_folder, video_name=video_name)


if __name__ == '__main__':
    test()
