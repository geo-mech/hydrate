from zmlx.base.seepage import Seepage, get_dt, get_time
from zmlx.base.zml import clock, ThreadPool


@clock
def iterate(*models, pool=None):
    if len(models) <= 1:
        pool = None

    for model in models:
        assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'

        if model.injector_number > 0:
            # 实施流体的注入操作.
            model.apply_injectors(dt=get_dt(model), time=get_time(model), pool=pool)

    if isinstance(pool, ThreadPool):
        pool.sync()  # 等待放入pool中的任务执行完毕
