
from zml import Seepage


def get(model: Seepage, *, text_key: str):
    """
    读取设置
    """
    text = model.get_text(text_key)
    if len(text) > 2:
        data = eval(text)
        assert isinstance(data, list)
        return data
    else:
        return []


def put(model: Seepage, *, data: list, text_key: str):
    """
    写入设置
    """
    if isinstance(data, list):
        model.set_text(text_key, f'{data}')
    else:
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

