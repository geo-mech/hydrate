from zmlx.base.zml import Seepage


def backup(model: Seepage):
    """
    将最后一种流体备份到solid_buffer中
    Args:
        model: 待处理的模型

    Returns:
        None
    """
    buffer = model.temps.get('solid_buffer', None)
    if buffer is None:
        buffer = Seepage.CellData()
    model.pop_fluids(buffer)
    model.temps['solid_buffer'] = buffer


def restore(model: Seepage):
    """
    从solid_buffer中恢复备份的固体物质
    Args:
        model: 待处理的模型

    Returns:
        None
    """
    buffer = model.temps.get('solid_buffer', None)
    assert isinstance(buffer, Seepage.CellData), 'You must set solid_buffer before iterate'
    model.push_fluids(buffer)
