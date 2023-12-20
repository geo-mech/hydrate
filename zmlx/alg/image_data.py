import os
import numpy as np
from PIL import Image
from scipy.interpolate import NearestNDInterpolator


def get_data(img_name, map_name, vmin=0, vmax=1):
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
    """
    if not os.path.isfile(img_name) or not os.path.isfile(map_name):
        return
    image = np.array(Image.open(img_name))
    assert 1 <= image.shape[2] <= 4
    points = [image[:, :, i] for i in range(image.shape[2])]
    cmap = _create_cm(map_name)
    return cmap(*points) * (vmax - vmin) + vmin


def _create_cm(name):
    """
    读取colormap，并作为NearestNDInterpolator返回
    """
    if not os.path.isfile(name):
        return
    image = np.array(Image.open(name))
    rows, cols, dims = image.shape
    assert 1 <= dims <= 4
    points = np.hstack([image[:, :, i].reshape(rows * cols, 1) for i in range(dims)])
    [i0, i1] = np.meshgrid(range(cols), range(rows))
    if rows < cols:
        values = i0.reshape(rows * cols, 1) / cols
    else:
        values = 1 - i1.reshape(rows * cols, 1) / rows
    return NearestNDInterpolator(points, values, rescale=False)


def test(img_name, map_name):
    import matplotlib.pyplot as plt
    data = get_data(img_name, map_name)

    plt.figure(figsize=(10, 5))

    plt.subplot(1, 2, 1)
    plt.imshow(np.array(Image.open(img_name)))
    plt.title('Original Cloud Image')
    plt.axis('off')

    plt.subplot(1, 2, 2)
    plt.imshow(data, vmin=0, vmax=1)
    plt.title('Mapped Cloud Image')
    plt.axis('off')

    plt.show()


if __name__ == '__main__':
    from zmlx.data.get_path import get_path
    test(get_path('cloud.png'), get_path('cm1.png'))
