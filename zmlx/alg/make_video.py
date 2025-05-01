import warnings

from zmlx.alg.image import make_video

warnings.warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)

from zmlx.alg.sys import log_deprecated

log_deprecated(__name__)




def test():
    # 设置图片文件夹和输出视频文件名
    image_folder = r'D:\MyData\co2\base\inh'  # 替换为你的图片文件夹路径
    video_name = r'D:\MyData\co2\base\inh.mp4'

    # 调用函数
    make_video(image_folder=image_folder, video_name=video_name)


if __name__ == '__main__':
    test()
