try:
    from pyqtgraph.console import ConsoleWidget
    from zmlx.system import app_data


    class PgConsole(ConsoleWidget):
        def __init__(self, parent=None):
            text = app_data.getenv(
                key='PgConsoleText',
                encoding='utf-8',
                default="""
这是一个交互的Python控制台。请在输入框输入Python命令并开始。特别注意，输入的代码将直接在主线程中执行，因此，请不要输入耗时较长的代码，否则会导致界面响应卡死。

---\n\n""")
            code = app_data.getenv(
                key='PgConsoleInit',
                encoding='utf-8',
                default="from zmlx import *"
            )
            super().__init__(parent, namespace=app_data.space, text=text)
            try:
                exec(code, app_data.space)
            except Exception as err:
                print(err)

except ImportError:
    PgConsole = None
