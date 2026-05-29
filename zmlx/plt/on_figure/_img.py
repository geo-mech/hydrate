def show_image(fig, file_path):
    """
    在给定的 matplotlib figure 上显示图片，保持比例不变，页边距尽可能为 0

    参数:
        fig: matplotlib 的 Figure 对象
        file_path: 图片文件路径
    """
    import matplotlib.image as mpimg
    # 清空 figure，避免重叠
    fig.clf()

    # 读取图片
    img = mpimg.imread(file_path)

    # 获取图片原始宽高
    h, w = img.shape[:2]
    aspect_ratio = w / h  # 宽高比

    # 创建子图，占据整个 figure，不留边距
    ax = fig.add_subplot(111)

    # 显示图片，保持原始比例
    ax.imshow(img)
    ax.axis('off')  # 关闭坐标轴

    # 设置子图完全占满画布，无边距
    ax.set_position([0, 0, 1, 1])

    # 强制保持图片宽高比，防止拉伸
    ax.set_aspect(aspect_ratio, adjustable='box')

    # 让布局紧凑，消除所有默认边距
    fig.tight_layout(pad=0)
