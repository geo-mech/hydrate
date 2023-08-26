# ** text = '控制台'
# ** on_toolbar = False
# ** icon = 'console.png'
# ** dependency = """from pyqtgraph.console import ConsoleWidget"""
# ** is_sys = True

from zmlx.ui.Widgets.PgConsole import PgConsole
from zml import gui

if PgConsole is not None:
    gui.get_widget(type=PgConsole, caption='控制台', on_top=True)
