"""
辅助 InvasionPercolation 类的函数.
"""

from ctypes import c_double, POINTER

from zml import InvasionPercolation, get_pointer64, np
from zmlx.plt.on_axes import plot_on_axes


def ip_nodes_write(model: InvasionPercolation, index, pointer=None, buf=None):
    """
    导出属性:
        index=-1, x坐标
        index=-2, y坐标
        index=-3, z坐标
        index=-4, phase
    """
    if pointer is None:
        if buf is None:
            buf = np.zeros(shape=model.node_n, dtype=np.float64)
            buf = np.ascontiguousarray(buf)
        else:
            assert len(buf) == model.node_n
            buf = np.ascontiguousarray(buf)
        assert buf.flags.c_contiguous, f'The buffer must be contiguous for save'
        pointer = buf.ctypes.data_as(POINTER(c_double))

    if index == -1 or index == -2 or index == -3:
        model.write_pos(-index - 1, pointer)
        return buf
    elif index == -4:
        model.write_phase(pointer)
        return buf
    else:
        return None


def _get_buf(count, buf=None):
    if buf is None:
        buf = np.zeros(shape=count, dtype=np.float64)
        buf = np.ascontiguousarray(buf)
    else:
        assert len(buf) == count
        buf = np.ascontiguousarray(buf)
    return buf


def get_pos(model: InvasionPercolation, dim, buf=None):
    """
    获得节点的坐标.
    Args:
        model: InvasionPercolation 模型.
        dim: 需要导出的维度 0、1、2
        buf: 结果缓冲区

    Returns:
        ndarray: 使用numpy的数组表示的坐标
    """
    buf = _get_buf(model.node_n, buf)
    model.write_pos(dim, get_pointer64(buf))
    return buf


def get_x(model: InvasionPercolation, buf=None):
    return get_pos(model, 0, buf)


def get_y(model: InvasionPercolation, buf=None):
    return get_pos(model, 1, buf)


def get_z(model: InvasionPercolation, buf=None):
    return get_pos(model, 2, buf)


def get_phase(model: InvasionPercolation, buf=None):
    buf = _get_buf(model.node_n, buf)
    model.write_phase(get_pointer64(buf))
    return buf


def set_pos(model: InvasionPercolation, dim, pos):
    if np.isscalar(pos):
        pos = np.full(shape=model.node_n, fill_value=pos)
    model.read_pos(dim, get_pointer64(pos, readonly=True))


def set_x(model: InvasionPercolation, pos):
    set_pos(model, 0, pos)


def set_y(model: InvasionPercolation, pos):
    set_pos(model, 1, pos)


def set_z(model: InvasionPercolation, pos):
    set_pos(model, 2, pos)


def set_phase(model: InvasionPercolation, phase):
    if np.isscalar(phase):
        phase = np.full(shape=model.node_n, fill_value=phase)
    model.read_phase(get_pointer64(phase, readonly=True))


def set_node_radi(model: InvasionPercolation, radi):
    if np.isscalar(radi):
        radi = np.full(shape=model.node_n, fill_value=radi)
    model.read_node_radi(get_pointer64(radi, readonly=True))


def set_nodes(model: InvasionPercolation, count,
              x=None, y=None, z=None, phase=None, radi=None):
    assert model.node_n == 0
    model.add_node(count)
    if x is not None:
        set_x(model, x)
    if y is not None:
        set_y(model, y)
    if z is not None:
        set_z(model, z)
    if phase is not None:
        set_phase(model, phase)
    if radi is not None:
        set_node_radi(model, radi)


def set_bonds(model: InvasionPercolation, count, node0, node1, radi=None):
    assert model.bond_n == 0
    model.add_bond(node0=get_pointer64(node0, readonly=True),
                   node1=get_pointer64(node1, readonly=True),
                   count=count)
    if radi is not None:
        model.read_bond_radi(get_pointer64(radi, readonly=True))


def show_xy(model: InvasionPercolation, caption='侵入过程', gui_only=True,
            **kwargs):
    def on_axes(ax):
        x = get_x(model)
        y = get_y(model)
        v = get_phase(model)
        mask = v < 0.5
        ax.scatter(x[mask], y[mask], c='tab:blue', s=3, label='Water',
                   alpha=0.2, edgecolors='none')
        mask = [not m for m in mask]
        ax.scatter(x[mask], y[mask], c='tab:orange', s=8, label='Oil',
                   alpha=0.7, edgecolors='none')

    plot_on_axes(on_axes, show_legend=True, grid=True, axis='equal',
                 caption=caption, gui_only=gui_only, **kwargs)
