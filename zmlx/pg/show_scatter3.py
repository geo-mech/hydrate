from zml import *
from zmlx.pg.colormap import coolwarm
from zmlx.pg.get_color import get_color
from zmlx.pg.plot3 import *


def show_scatter3(pos=None, size=None, color=None, alpha=None, pxMode=True, cmap=None, caption=None, on_top=None,
                  reset_dist=True, reset_cent=True):
    """
    显示三维的散点(仅仅在gui模式下执行)
    """
    if not gui.exists() or pos is None:
        return

    shape = pos.shape

    assert len(shape) == 2
    assert shape[1] == 3
    assert shape[0] >= 0
    count = shape[0]

    if count == 0:
        return

    if color is None:
        color = 1

    if len(np.shape(color)) == 0:
        color = np.ones(shape=count, dtype=float) * color

    if size is None:
        size = 1

    if len(np.shape(size)) == 0:
        size = np.ones(shape=count, dtype=float) * size

    if alpha is None:
        alpha = 1

    if len(np.shape(alpha)) == 0:
        alpha = np.ones(shape=count, dtype=float) * alpha

    cl = np.min(color)
    cr = np.max(color)
    if cl + 1.0e-10 >= cr:
        cl = cr - 1.0

    if cmap is None:
        cmap = coolwarm()

    colors = []
    for i in range(count):
        c1 = get_color(cmap, cl, cr, color[i])
        assert len(c1) >= 4
        colors.append(c1)

    colors = np.array(colors)
    colors[:, 3] = alpha
    color = colors

    x_min = np.min(pos[:, 0])
    x_max = np.max(pos[:, 0])

    y_min = np.min(pos[:, 1])
    y_max = np.max(pos[:, 1])

    z_min = np.min(pos[:, 2])
    z_max = np.max(pos[:, 2])

    widget = get_widget(caption=caption, on_top=on_top)
    if widget is None:
        warnings.warn(f'The widget is None. caption = {caption}, on_top = {on_top}')
        return

    if hasattr(widget, 'scatter_1'):
        widget.scatter_1.setData(pos=pos, color=color, size=size, pxMode=pxMode)
        if reset_dist:
            set_distance(get_distance([x_min, y_min, z_min], [x_max, y_max, z_max]) * 1.5)
        if reset_cent:
            set_center([(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2])
    else:
        widget.scatter_1 = Scatter(pos=pos, color=color, size=size, pxMode=pxMode)
        add_item(widget.scatter_1)
        set_distance(get_distance([x_min, y_min, z_min], [x_max, y_max, z_max]) * 1.5)
        set_center([(x_min + x_max) / 2, (y_min + y_max) / 2, (z_min + z_max) / 2])

    if hasattr(widget, 'line_1'):
        add_box([x_min, y_min, z_min], [x_max, y_max, z_max], line=widget.line_1)
    else:
        widget.line_1 = add_box([x_min, y_min, z_min], [x_max, y_max, z_max])


def demo(count=1000):
    gui.execute(lambda:
                show_scatter3(pos=np.random.uniform(size=(count, 3)),
                              size=np.random.uniform(size=count) * 0.04,
                              color=np.random.uniform(size=count),
                              alpha=np.random.uniform(size=count),
                              pxMode=False, caption='scatter3_demo'),
                close_after_done=False)


if __name__ == '__main__':
    demo()
