def write_py(path, data=None, **kwargs):
    """
    Save the data to a file in .py format. Note that the data must be correctly converted to a string.
    If data is a string, make sure it does not contain special characters such as ' and "
    """
    if path is None:
        return
    if data is None and len(kwargs) == 0:
        return
    if data is None:
        data = {}
    if isinstance(data, dict):
        data.update(kwargs)
    else:
        assert len(kwargs) == 0
    with open(path, 'w', encoding='UTF-8') as file:
        if isinstance(data, str):
            file.write(f'"""{data}"""')
        else:
            file.write(f'{data}')


def read_py(path=None, data=None, encoding='utf-8', globals=None, text=None,
            key=None):
    """
    Read data from .py format. For specific format, refer to the description of the write_py function
    """
    assert key is None or isinstance(key, str)
    if text is None and path is not None:
        try:
            with open(path, 'r', encoding=encoding) as file:
                text = file.read()
        except:
            pass
    if text is None:
        if key is None:
            return data
        else:
            return {} if key == '*' or key == '' else data
    else:
        assert isinstance(text, str)
    if key is None:
        try:
            return eval(text, globals)
        except:
            return data
    else:
        space = {}
        try:
            exec(text, globals, space)
            return space if key == '*' or key == '' else space.get(key, data)
        except:
            return space if key == '*' or key == '' else data
