"""
迭代更新流体的性质
"""

from zmlx.base.seepage import Seepage, get_vis_min, get_vis_max
from zmlx.base.zml import clock, ThreadPool


@clock
def iterate(*models, pool=None):
    if len(models) == 1:
        pool = None

    for model in models:
        assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'

        if model.not_has_tag('disable_update_den') and model.fludef_number > 0:
            model.update_den(
                relax_factor=0.3,
                fa_t=model.get_flu_key('temperature'),
                pool=pool
            )

    if isinstance(pool, ThreadPool):
        pool.sync()  # 等待放入pool中的任务执行完毕

    for model in models:
        if model.not_has_tag('disable_update_vis') and model.fludef_number > 0:
            # 更新流体的粘性系数(注意，当有固体存在的时候，务必将粘性系数的最大值设置为1.0e30)
            model.update_vis(
                ca_p=model.get_cell_key('pre'),  # 压力属性
                fa_t=model.get_flu_key('temperature'),  # 温度属性
                relax_factor=1.0,
                min=get_vis_min(model),
                max=get_vis_max(model),
                pool=pool
            )

    if isinstance(pool, ThreadPool):
        pool.sync()  # 等待放入pool中的任务执行完毕
