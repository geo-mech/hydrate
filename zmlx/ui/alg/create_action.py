from zmlx.ui.Config import load_icon
from zmlx.ui.QtWidgets.QAction import QAction


def create_action(parent, text, icon=None, slot=None):
    ac = QAction(text, parent)
    if icon is not None:
        ac.setIcon(load_icon(icon))
    else:
        ac.setIcon(load_icon('python'))
    if slot is not None:
        ac.triggered.connect(slot)
    return ac
