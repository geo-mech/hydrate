def item(name, *args, **kwargs):
    """
    生成一个绘图的item.
    Args:
        name: 项目的名称，字符串形式
        *args: 传递给项目的参数
        **kwargs: 传递给项目的关键字参数

    Returns:
        一个元组，包含项目的名称、参数和关键字参数
    """
    return name, args, kwargs
