from zmlx.base.zml import Seepage, clock, ThreadPool


@clock
def backup(*models, pool=None):
    """
    将最后一种流体备份到  solid_buffer 中
    Args:
        models: 待处理的模型
        pool: 线程池

    Returns:
        None
    """
    if len(models) == 0:
        pool = None

    for model in models:
        assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'

        if model.has_tag('has_solid'):
            buffer = model.temps.get('solid_buffer', None)
            if buffer is None:
                buffer = Seepage.CellData()
            model.pop_fluids(buffer, pool=pool)
            model.temps['solid_buffer'] = buffer

    if isinstance(pool, ThreadPool):
        pool.sync()  # 等待放入pool中的任务执行完毕


@clock
def restore(*models, pool=None):
    """
    从solid_buffer中恢复备份的固体物质
    Args:
        models: 待处理的模型
        pool: 线程池

    Returns:
        None
    """
    if len(models) == 0:
        pool = None

    for model in models:
        assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'

        if model.has_tag('has_solid'):
            buffer = model.temps.get('solid_buffer', None)
            assert isinstance(buffer, Seepage.CellData), 'You must set solid_buffer before iterate'
            model.push_fluids(buffer, pool=pool)

    if isinstance(pool, ThreadPool):
        pool.sync()  # 等待放入pool中的任务执行完毕
