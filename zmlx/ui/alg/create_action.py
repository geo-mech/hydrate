from zmlx.ui.Config import load_icon
from zmlx.ui.QtWidgets.QAction import QAction


def create_action(parent, text, icon, slot):
    ac = QAction(text, parent)
    ac.setIcon(load_icon(icon))
    ac.triggered.connect(slot)
    return ac
