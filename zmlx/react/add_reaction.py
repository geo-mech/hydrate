from zml import Seepage
from zmlx.react.create_reaction import create_reaction


def add_reaction(model: Seepage, data, need_id=False):
    """
    添加一个反应
    """
    if not isinstance(data, Seepage.Reaction):
        data = create_reaction(model, **data)
    return model.add_reaction(data=data, need_id=need_id)
