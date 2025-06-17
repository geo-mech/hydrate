text = """
这是一个交互的Python控制台。请在输入框输入Python命令并开始！

---
"""

code = """
from zmlx import *
"""

try:
    from pyqtgraph.console import ConsoleWidget
    from zml import app_data


    class PgConsole(ConsoleWidget):
        def __init__(self, parent=None):
            super().__init__(
                parent,
                namespace=app_data.space,
                text=app_data.getenv(
                    key='PgConsoleText',
                    encoding='utf-8',
                    default=text))

            try:
                exec(app_data.getenv(
                    key='PgConsoleInit', encoding='utf-8',
                    default=code),
                    app_data.space)
            except:
                pass

except:
    PgConsole = None
