# ** text = '控制台'
# ** on_toolbar = False
# ** icon = 'console.png'
# ** dependency = """from pyqtgraph.console import ConsoleWidget"""
# ** is_sys = True

from zml import gui
from zmlx.ui.Widgets.PgConsole import PgConsole

if PgConsole is not None:
    gui.get_widget(type=PgConsole, caption='控制台', on_top=True, icon='console.png')
