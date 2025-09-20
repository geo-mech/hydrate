from PIL import Image

import zmlx.alg.sys as warnings
from zmlx.exts.base import np
from zmlx.alg.image import get_data

warnings.warn(f'{__name__} will be removed after 2026-4-15', DeprecationWarning,
              stacklevel=2)


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
    from zmlx.data.path import get_path

    test(get_path('cloud.png'), get_path('cm1.png'))
