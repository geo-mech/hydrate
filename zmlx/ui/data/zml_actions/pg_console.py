# ** text = 'Python控制台'

from pyqtgraph.console import ConsoleWidget

import zml
import zmlx
from zml import gui

text = """
这是一个交互的Python控制台，模块zml和zmlx已经引入。请在输入框输入Python命令并开始!!

---
"""
gui.get_widget(type=ConsoleWidget,
               type_kw={'namespace': {'space': gui.window().console_widget.workspace,
                                      'gui': gui,
                                      'zml': zml, 'zmlx': zmlx, },
                        'text': text},
               caption='Python控制台')
