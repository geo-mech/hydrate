"""
流体加热模块：对储层中所有 Cell 内的特定流体，按指定的功率进行加热。

适用场景：
    - 对整个储层（或部分区域）施加分布式热源，例如微波加热、电磁加热等
    - 需要加热特定的流体组分（如 ch4_hydrate），而非储层基质
    - 功率可以随空间变化（每个 Cell 独立设定）

注意：
    如果只需要在储层中的某一个点（或几个点）进行加热，而且加热的是储层
    基质（而非特定的流体），那么不应该使用此模块，而应该使用 Injector。
    使用 Seepage.add_injector，不设置 fluid_id，仅设置 ca_mc、ca_t 和
    value（功率），即可实现点加热（纯热注入）。

    示例：
        # 点加热（纯热注入），在井位置注入 500W 热量
        model.add_injector(
            cell=target_id,
            ca_mc=model.get_cell_key('mc'),
            ca_t=model.get_cell_key('temperature'),
            value=500.0   # 加热功率 (W)
        )

参考资料：
    - Seepage.add_injector 的文档（zmlx/exts/_seepage.py）
    - prod_v2_electric_heating.py（点加热 demo）
"""

from zmlx.alg.vec import to_numpy
from zmlx.exts import Seepage, np, clock
from zmlx.tfc._base import get_dt, as_numpy, get_configs, add_config

text_key = 'fluid_heating'


def get_settings(model: Seepage):
    """
    读取此模型的流体加热设置（以字典列表形式返回）。
    """
    return get_configs(model, text_key=text_key)


def add_setting(
        model: Seepage, fluid=None, power=None,
        temp_max=None):
    """
    添加流体加热设置：对整个储层中所有 Cell 内的指定流体进行加热。

    **注意**：此函数操作的是整个储层所有 Cell 中的 **流体**。
    如果只需要点加热储层基质，请使用 Seepage.add_injector（见模块文档）。

    Args:
        model: 需要添加设置的 Seepage 模型
        fluid: 即将被加热的流体名称（或流体ID列表）
        power: 加热功率 (W)，一个长度为 cell_number 的数组（或缓冲区名称）。
               非零值表示在该 Cell 中施加的加热功率。
        temp_max: 流体的最高温度 (K)，可选。可以是数组（每 Cell 独立上限）
                  或缓冲区名称。超过此温度后不再继续加热。
    """
    if fluid is not None:
        add_config(
            model, text_key=text_key, fluid=fluid,
            power=power, temp_max=temp_max)


@clock
def iterate(*models):
    """
    迭代更新流体的温度。

    对每个模型，读取流体加热设置，根据功率计算温升：
        dT = (power * dt) / (mass * specific_heat)
    并在温度超过 temp_max 时进行截断。

    此函数由 tfc.seepage.iterate() 自动调用，不需要手动执行。
    """
    assert np is not None, 'numpy is not imported.'
    for model in models:
        assert isinstance(model, Seepage), f'The model is not Seepage. model = {model}'

        dt = get_dt(model)

        the_settings = get_settings(model)
        if len(the_settings) == 0 or dt <= 0:
            continue

        for setting in the_settings:
            assert isinstance(setting, dict)

            # 确定流体
            fluid = setting.get('fluid')
            if not isinstance(fluid, list):
                assert isinstance(fluid, str)
                fluid = model.find_fludef(name=fluid)
                assert isinstance(fluid, list)

            # 确定功率
            power = setting.get('power')

            # 这里，从缓冲区中读取功率的数据
            if isinstance(power, str):
                power = to_numpy(model.get_buffer(key=power))
            else:
                power = np.array(power)

            # 加热流体
            if len(power) == model.cell_number:  # 长度必须和cell的数量一致
                m = as_numpy(model).fluids(*fluid).mass
                c = as_numpy(model).fluids(*fluid).get(
                    model.get_flu_key('specific_heat'))
                d_temp = (power * dt) / (m * c)
                d_temp[d_temp < 0] = 0  # 温度不能降低
                t0 = as_numpy(model).fluids(*fluid).get(
                    model.get_flu_key('temperature'))
                t1 = t0 + d_temp  # 加温之后的温度

                temp_max = setting.get('temp_max')
                if temp_max is not None:
                    if isinstance(temp_max, str):
                        temp_max = to_numpy(model.get_buffer(key=temp_max))
                    else:
                        temp_max = np.array(temp_max)
                    if len(temp_max) == model.cell_number:
                        mask = t1 > temp_max
                        t1[mask] = temp_max[mask]

                as_numpy(model).fluids(*fluid).set(
                    model.get_flu_key('temperature'), t1)
