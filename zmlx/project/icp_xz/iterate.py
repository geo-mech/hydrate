from zml import ConjugateGradientSolver, Seepage
from zmlx.alg import np
from zmlx.alg.time2str import time2str
from zmlx.config import seepage
from zmlx.utility.PressureController import PressureController
from zmlx.utility.SeepageCellMonitor import SeepageCellMonitor


def reaction_bufs_ok(buffers, model: Seepage):
    """
    反应的缓冲区是否是可用的
    """
    if buffers is None:
        return False

    if len(buffers) != model.reaction_number:
        return False

    for idx in range(model.reaction_number):
        if len(buffers[idx]) != model.cell_number:
            return False

    return True


def iterate(space: dict):
    """
    将这个模型向前迭代一步. 更新所有的操作.
    """
    # 渗流模型对象
    model = space.get('model')
    assert isinstance(model, Seepage)

    # 确保边界压力
    pre_ctrl = space.get('pre_ctrl')
    assert isinstance(pre_ctrl, PressureController)
    pre_ctrl.update(seepage.get_time(model))

    # 更新生产点的监视
    monitor = space.get('monitor')
    assert isinstance(monitor, SeepageCellMonitor)
    monitor.update(dt=3600.0 * 24.0)  # 将更新的时间间隔设置为1天

    # 执行必要的修改操作
    operations = space.get('operations')
    if operations is not None:
        modify = False
        while len(operations) > 0:
            time, key, val = operations[0]
            if seepage.get_time(model) < time:
                break
            print(f'Time = {time2str(time)}, Key = {key}, Value = {val}')
            operations.pop(0)  # 弹出第一个

            if key == 'outlet':  # 打开或者关闭出口
                # 最后一个用以控制生产的face
                virtual_face = model.get_face(model.face_number - 1)
                seepage.set_face(face=virtual_face,
                                 area=1 if val else 0)
                modify = True
                continue

            raise RuntimeError(f'Can not find key: {key}')

        if modify:
            # 这是，修改了边界条件，我们将时间步长降低，让它接下来自动调整.
            seepage.set_dt(model, 1.0)

    # 准备反应发生的缓冲区
    reaction_bufs = space.get('reaction_bufs', None)
    if not reaction_bufs_ok(reaction_bufs, model):
        reaction_bufs = [np.zeros(shape=model.cell_number,
                                  dtype=float) for idx in range(model.reaction_number)]
        space['reaction_bufs'] = reaction_bufs
    assert reaction_bufs_ok(reaction_bufs, model)

    # 线性方程求解器
    solver = space.get('solver')
    if solver is None:
        print('create a new ConjugateGradientSolver')
        solver = ConjugateGradientSolver(tolerance=1.0e-30)
        space['solver'] = solver

    # 向前迭代一次(返回迭代的报告)
    r = seepage.iterate(model=model, solver=solver,
                        react_bufs=[np.get_pointer(item) for item in reaction_bufs],
                        vis_max=1e30, # Modify the vis_max, since 2024-5-22
                        )

    # 记录反应发生的质量
    count = model.cell_number - 1  # 去除最后一个用于生产的虚拟cell
    assert count > 0

    # 在这一步里面，所有发生的质量
    reaction_dm = [np.sum(buf[0: count]) for buf in reaction_bufs]

    # 记录总的反应质量随着时间的变化
    t2dm = space.get('reaction_dm', None)
    if t2dm is None:
        t2dm = [[seepage.get_time(model)]]
        for item in reaction_dm:
            t2dm.append([item])
        space['reaction_dm'] = t2dm
    else:
        assert isinstance(t2dm, list)
        assert len(t2dm) == len(reaction_dm) + 1
        t2dm[0].append(seepage.get_time(model))
        for idx in range(len(reaction_dm)):
            assert len(t2dm[idx + 1]) > 0
            t2dm[idx + 1].append(reaction_dm[idx] + t2dm[idx + 1][-1])  # 累加之前的结果

    # 返回seepage.iterate的结果
    return r
