from zmlx.base.seepage import Seepage
from zmlx.base.zml import clock, ThreadPool


@clock
def iterate(*models, pool=None):
    """
    根据gr更新cond
    """
    if len(models) <= 1:
        pool = None

    for model in models:
        assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'

        if model.gr_number > 0:
            # 此时，各个Face的导流系数是可变的
            #       (并且，这里由于已经弹出了固体，因此计算体积使用的是流体的数值).
            # 注意：
            #     在建模的时候，务必要设置Cell的v0属性，Face的g0属性和igr属性，
            #     并且，在model中，应该有相应的gr和它对应。
            if model.get_cell_key('fv0') is not None and model.get_face_key('g0') is not None and model.get_face_key(
                    'igr') is not None:
                model.update_cond(
                    ca_v0=model.get_cell_key('fv0'),
                    fa_g0=model.get_face_key('g0'),
                    fa_igr=model.get_face_key('igr'),
                    relax_factor=0.3,
                    pool=pool
                )

    if isinstance(pool, ThreadPool):
        pool.sync()  # 等待放入pool中的任务执行完毕

    for model in models:
        assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'
        updaters = model.temps['cond_updaters']
        if updaters is not None:
            for update in updaters:  # 施加cond的更新操作
                assert callable(
                    update), f'The update in cond_updaters must be callable. However, it is: {update}'
                update(model)
