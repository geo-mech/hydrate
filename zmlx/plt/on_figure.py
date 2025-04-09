from zmlx.ui import plot, gui


def plot_on_figure(on_figure, gui_mode=None, **opts):
    """
    绘制图形。使用在坐标轴上绘图的回调函数.

    Args:
        on_figure: 在figure上绘图的回调函数，函数的原型为:
            def on_figure(fig):
                ...
                其中fig为matplotlib的Figure实例
        gui_mode (bool): 是否强制在zml的界面上绘图(即如果界面不存在，则自动自动一个界面)
        opts: 传递给底层plot函数的附加参数，主要包括：
            caption(str): 在界面绘图的时候的标签 （默认为untitled）
            clear(bool): 是否清除界面上之前的axes （默认清除）
            on_top (bool): 是否将标签页当到最前面显示 (默认为否)
            fname (str|None): 保存的文件名，默认为None (即仅仅绘图，不保存文件)
            dpi (int): 保存的图片的分辨率 (默认为300)
    Returns:
        None
    """

    def f():
        plot(on_figure, **opts)

    if gui_mode:
        gui.execute(f, close_after_done=False)
    else:
        f()


def test_1():
    def on_figure(fig):
        ax = fig.subplots()
        ax.plot([1, 2, 3], [4, 5, 6])

    plot_on_figure(on_figure, caption='Caption', gui_mode=True)


if __name__ == '__main__':
    test_1()
