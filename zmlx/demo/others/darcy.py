# ** desc = '测试仅仅在重力作用下的单相渗流过程'

# 本案例模拟单相流体在纯重力驱动下的垂向渗流过程，用于验证达西定律的正确性。
# 物理问题：充满水的直立柱体，顶部和底部保持高渗透性（模拟开放边界），
# 流体在重力作用下从顶部向底部渗流。通过标记流体注入时间，追踪流体运移时间。
# 理论估算：基于达西定律 Q = dp*k*S/(L*mu)，压差dp=1e4 Pa（由水柱重力产生），
# 渗透率k=1e-14 m2，截面积S=1 m2，长度L=1 m，粘度mu=1e-3 Pa·s，
# 计算达西流速约为1e-7 m3/s。流体体积0.2 m3，因此穿透时间约为2e6秒。
# 模型结果与理论估算一致，验证了达西定律和重力驱动流的正确实现。
# 建模方法：使用tfc框架建立垂向渗流模型，在顶部和底部设置极高的孔隙度
# （模拟开放边界条件），通过追踪流体属性记录运移时间。

"""
经过测试，流体从顶部在重力的作用下，渗透到底部用时大约2e6秒，下面，基于达西定律来估算.

Q = dp*k*S/(L*mu) = 1e4 * 1e-14 * 1 / (1 * 1e-3) = 1e-7 m3/s

流体体积为 0.2方米， 因此，时间为 0.2 / 1e-7 = 2e6 s

这与计算出的结果一致。
"""

from zmlx import *

# 最大时间步数，超过此值强制停止迭代
STEP_MAX = 100000000


def create():
    """
    创建重力驱动单相渗流模型。

    构建一个垂直方向100层的细长柱体模型，仅包含水一种流体。
    顶部和底部边界设置为极高孔隙度（模拟开放边界，允许流体自由进出），
    中间部分为正常多孔介质。通过追踪流体属性记录流体从顶部运移至底部的时间。

    返回:
        Seepage: 创建好的渗流模型对象
    """
    # 创建10x2x100的网格，x方向10个单元，z方向100个单元，模拟细长柱体
    mesh = create_cube(
        x=linspace(-0.5, 0.5, 10), y=[-0.5, 0.5], z=linspace(-0.5, 0.5, 100)
    )
    z_min, z_max = get_pos_range(mesh, 2)

    # 定义孔隙度分布：顶部和底部边界处设为极大值以模拟开放边界
    def porosity(*pos):
        if abs(pos[2] - z_min) < 1.0e-4 or abs(pos[2] - z_max) < 1.0e-4:
            return 1.0e10  # 开放边界：极高的孔隙度
        else:
            return 0.2  # 内部正常孔隙度

    model = tfc.create(
        mesh=mesh, cfl=0.5,
        fludefs=[FluDef(name='h2o')],
        porosity=porosity,
        p=2e6, s=1.0,  # 初始压力2MPa，完全饱和
        perm=10e-15,  # 渗透率10e-15 m2
        gravity=[0, 0, -10]  # z方向重力加速度
    )
    # 禁用流体密度更新、粘度更新和温度计算，保持流体物性恒定
    model.add_tag('disable_update_den', 'disable_update_vis', 'disable_ther')

    # 注册一个流体属性键用于存储流体"时间"标记
    key = model.reg_flu_key('time')
    top_ids = []
    btm_ids = []

    # 遍历所有单元，初始化时间标记，并记录顶部和底部单元的ID
    for cell in model.cells:
        assert isinstance(cell, Seepage.Cell)
        cell.get_fluid(0).set_attr(key, 0)  # 初始化时间标记为0
        if abs(cell.z - z_max) < 1.0e-4:
            top_ids.append(cell.index)  # 记录顶部单元的索引
        if abs(cell.z - z_min) < 1.0e-4:
            btm_ids.append(cell.index)  # 记录底部单元的索引

    # 添加迭代步骤回调：在每个迭代步后设置顶部流体的时间标记
    step_iteration.add_setting(
        model, start=0, step=1, stop=999999999, name='set_fluid_time',
        args=['@model', top_ids, btm_ids, key]
    )
    return model


def set_fluid_time(model, top_ids, btm_ids, key):
    """
    在每个迭代步中更新流体的时间标记，并检测流体是否到达底部。

    当顶部注入的流体到达底部时（底部单元的时间标记值之和>1e-4），
    将当前时间步设为极大值以终止计算。

    参数:
        model: 渗流模型对象
        top_ids: 顶部单元的索引列表
        btm_ids: 底部单元的索引列表
        key: 流体时间属性的键
    """
    time = tfc.get_time(model)  # 获取当前模拟时间
    # 更新顶部单元的流体时间标记为当前模拟时间（标识新注入的流体）
    for idx in top_ids:
        model.get_cell(idx).get_fluid(0).set_attr(key, time)
    # 检查底部单元中是否有流体到达（时间标记非零）
    value = 0
    for idx in btm_ids:
        value += model.get_cell(idx).get_fluid(0).get_attr(key)
    # 如果有流体到达底部，则结束计算
    if value > 1.0e-4:
        tfc.set_step(model, STEP_MAX * 2)


def show(model):
    """
    显示当前的流体时间标记分布云图。

    参数:
        model: 渗流模型对象
    """
    title = f'Time = {tfc.get_time(model, as_str=True)}'
    x = as_numpy(model).cells.x
    z = as_numpy(model).cells.z
    # 获取流体的时间标记值，反映流体从顶部注入后经过的时间
    time = as_numpy(model).fluids(0).get_attr(model.get_flu_key('time'))
    tricontourf(
        x, z, time, caption='流体time', title=title)


def main():
    """
    主函数：创建并求解重力驱动渗流模型。

    使用tfc.solve进行自动迭代求解，在计算过程中实时显示流体运移状态。
    达西流穿透时间约2e6秒，与理论估算一致。
    """
    model = create()
    tfc.solve(model, step_max=STEP_MAX,
              extra_plot=lambda: show(model),
              slots={'set_fluid_time': set_fluid_time}
              )


if __name__ == '__main__':
    gui.execute(main, close_after_done=False)
