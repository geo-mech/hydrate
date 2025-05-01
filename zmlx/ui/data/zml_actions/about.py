icon = 'info'
text = '关于'


def slot():
    from zmlx.ui.window_functions import start_func
    xx = """
from zml import lic
print(lic.desc)
gui.show_about()
    """
    start_func(xx)


def enabled():
    from zmlx.ui.window_functions import is_running
    return not is_running()
