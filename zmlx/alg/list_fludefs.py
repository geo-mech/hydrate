def __list(fdef):
    data = {}
    for i in range(fdef.component_number):
        name = fdef.get_component(i).name
        data[f'{name}' if len(name) > 0 else f'<{i}>'] = __list(fdef.get_component(i))
    return data


def list_fludefs(model):
    """
    列出模型中流体的定义
    """
    data = {}
    for i in range(model.fludef_number):
        name = model.get_fludef(i).name
        data[f'{name}' if len(name) > 0 else f'<{i}>'] = __list(model.get_fludef(i))
    return data
