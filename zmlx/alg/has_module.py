def has_module(name):
    """
    测试是否存在给定名字的库
    """
    try:
        import importlib
        importlib.import_module(name)
        return True
    except:
        return False


# 是否存在numpy
has_numpy = has_module('numpy')

# 是否存在scipy
has_scipy = has_module('scipy')

# 是否存在PyQt5
has_PyQt5 = has_module('PyQt5')

# 是否存在 matplotlib
has_matplotlib = has_module('matplotlib')
