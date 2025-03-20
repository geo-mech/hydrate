icon = 'info'
text = '关于'


def slot():
    from zmlx.ui.window.start_func import start_func
    xx = """
from zml import lic
print(lic.summary)
gui.show_about()
    """
    start_func(xx)


def enabled():
    from zmlx.ui.window.is_running import is_running
    return not is_running()
