# ** text = '控制台'
# ** on_toolbar = 1
# ** icon = 'console.png'
# ** dependency = """from pyqtgraph.console import ConsoleWidget"""

from zmlx.ui.Widgets.PgConsole import PgConsole
from zml import gui

if PgConsole is not None:
    gui.get_widget(type=PgConsole, caption='控制台', on_top=True)
else:
    gui.warning('错误', '请确保正确安装了 pyqtgraph')
