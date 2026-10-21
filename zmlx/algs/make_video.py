"""已弃用的模块，请改用 zmlx.algs.image.

Modified by DeepSeek, 2026-10-17: warnings.warn -> zmlx.system.warn（弃用统计）
"""

from zmlx.system import warn
from zmlx.algs.image import make_video

warn(f'The module {__name__} will be removed after 2026-4-15',
              DeprecationWarning, stacklevel=2)


def test():
    # 设置图片文件夹和输出视频文件名
    image_folder = r'D:\MyData\co2\base\inh'  # 替换为你的图片文件夹路径
    video_name = r'D:\MyData\co2\base\inh.mp4'

    # 调用函数
    make_video(image_folder=image_folder, video_name=video_name)


if __name__ == '__main__':
    test()
