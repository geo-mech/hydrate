"""
多场耦合的求解，采用“数据”+“操作”的组织方式。对于“数据”，就是存储模型的状态；对于“操作”，则是修改模型的状态。求解的过程，就是建立
模型，形成一个初始的“数据”，然后，依次调用各个“操作”，来更新模型的状态。

所谓的各个“操作”，就是那些能够改变“数据”的过程。比如渗流/扩散/传热/化学以及其他一些细分的过程。对于这些“操作”，往往也是需要参数的。
这个模块，就是处理这些“操作”的配置参数的。对于每一类操作，我们定义，它的参数格式，必须是 list[dict]这样的形式。其中list的每一个
元素，都代表这一类操作中的一个（每一类的操作都可以有很多个）；而每个dict，都代表这一个操作的参数。
"""
from zmlx.base.zml import Seepage


def get(model: Seepage, *, text_key: str) -> list:
    """
    读取设置.
    """
    assert isinstance(text_key, str) and len(text_key) >= 1
    text = model.get_text(text_key)
    if len(text) >= 2:
        data = eval(text)
        assert isinstance(data, list)
        return data
    else:
        return []


def put(model: Seepage, *, data: list | None, text_key: str):
    """
    写入设置
    """
    assert isinstance(text_key, str) and len(text_key) >= 1
    if isinstance(data, list):
        model.set_text(text_key, f'{data}')
    else:
        assert data is None
        model.set_text(text_key, '')


def add(model: Seepage, *, text_key: str, **kwargs):
    """
    添加设置
    """
    if len(kwargs) > 0:
        data = get(model, text_key=text_key)
        assert isinstance(data, list)
        data.append(kwargs)
        put(model, text_key=text_key, data=data)
