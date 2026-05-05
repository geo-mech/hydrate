"""
辅助 InvasionPercolation 类的函数.
"""

from ctypes import c_double, POINTER
from typing import Union

from zml import InvasionPercolation, np, f64_ptr, const_f64_ptr


def ip_nodes_write(model: InvasionPercolation, index: Union[int, str], pointer=None, buf=None):
    """
    导出InvasionPercolation模型的节点的属性:
        index=-1, x坐标
        index=-2, y坐标
        index=-3, z坐标
        index=-4, phase
    """
    if pointer is None:
        assert np is not None
        if buf is None:
            buf = np.zeros(shape=model.node_n, dtype=np.float64)
            buf = np.ascontiguousarray(buf)
        else:
            assert len(buf) == model.node_n
            buf = np.ascontiguousarray(buf)
        assert buf.flags.c_contiguous, f'The buffer must be contiguous for save'
        pointer = buf.ctypes.data_as(POINTER(c_double))

    if isinstance(index, str):
        if index == 'x':
            index = -1
        elif index == 'y':
            index = -2
        elif index == 'z':
            index = -3
        elif index == 'phase':
            index = -4

    if index == -1 or index == -2 or index == -3:
        model.write_pos(-index - 1, pointer)
        return buf
    elif index == -4:
        model.write_phase(pointer)
        return buf
    else:
        return None


def _get_buf(count: int, buf=None):
    assert np is not None
    if buf is None:
        buf = np.zeros(shape=count, dtype=np.float64)
        buf = np.ascontiguousarray(buf)
    else:
        assert len(buf) == count
        buf = np.ascontiguousarray(buf)
    return buf


def get_pos(model: InvasionPercolation, dim: int, buf=None):
    """
    获得节点的坐标.
    Args:
        model: InvasionPercolation 模型.
        dim: 需要导出的维度 0、1、2
        buf: 结果缓冲区

    Returns:
        ndarray: 使用numpy的数组表示的坐标
    """
    assert dim in [0, 1, 2], f'dim must be 0, 1, or 2, but got {dim}'
    buf = _get_buf(model.node_n, buf)
    model.write_pos(dim, f64_ptr(buf))
    return buf


def get_x(model: InvasionPercolation, buf=None):
    return get_pos(model, 0, buf)


def get_y(model: InvasionPercolation, buf=None):
    return get_pos(model, 1, buf)


def get_z(model: InvasionPercolation, buf=None):
    return get_pos(model, 2, buf)


def get_phase(model: InvasionPercolation, buf=None):
    buf = _get_buf(model.node_n, buf)
    model.write_phase(f64_ptr(buf))
    return buf


def set_pos(model: InvasionPercolation, dim, pos):
    assert np is not None
    assert dim in [0, 1, 2], f'dim must be 0, 1, or 2, but got {dim}'
    if np.isscalar(pos):
        pos = np.full(shape=model.node_n, fill_value=pos)
    model.read_pos(dim, const_f64_ptr(pos))


def set_x(model: InvasionPercolation, pos):
    set_pos(model, 0, pos)


def set_y(model: InvasionPercolation, pos):
    set_pos(model, 1, pos)


def set_z(model: InvasionPercolation, pos):
    set_pos(model, 2, pos)


def set_phase(model: InvasionPercolation, phase):
    assert np is not None
    if np.isscalar(phase):
        phase = np.full(shape=model.node_n, fill_value=phase)
    model.read_phase(const_f64_ptr(phase))


def set_node_radi(model: InvasionPercolation, radi):
    assert np is not None
    if np.isscalar(radi):
        radi = np.full(shape=model.node_n, fill_value=radi)
    model.read_node_radi(const_f64_ptr(radi))


def set_nodes(model: InvasionPercolation, count, x=None, y=None, z=None, phase=None, radi=None):
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
    model.add_bond(
        node0=const_f64_ptr(node0),
        node1=const_f64_ptr(node1),
        count=count)
    if radi is not None:
        model.read_bond_radi(const_f64_ptr(radi))


def show_xy(
        model: InvasionPercolation, caption='Invasion Process',
        jx=None, jy=None, cmap=None, clabel='Phase', grid=True,
        xlabel='x (m)', ylabel='y (m)', title='Fluid Invasion'
):
    from zmlx.plt.on_axes.data import contourf, tricontourf
    from zmlx.plt.on_axes import plot2d
    x = get_x(model)
    y = get_y(model)
    v = get_phase(model)
    if cmap is None:
        cmap = 'coolwarm'
    if jx is not None and jy is not None:
        assert np is not None
        o = contourf(np.reshape(x, (jx, jy)),
                     np.reshape(y, (jx, jy)),
                     np.reshape(v, (jx, jy)), cmap=cmap, cbar=dict(label=clabel))
    else:
        o = tricontourf(x, y, v, cmap=cmap, cbar=dict(label=clabel))

    plot2d(o, aspect='equal', xlabel=xlabel, ylabel=ylabel, title=title, grid=grid, caption=caption)
