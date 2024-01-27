import os

from zmlx.ui.GuiBuffer import gui


def first_only(path='please_delete_this_file_before_run'):
    """
    when it is executed for the second time, an exception is given to ensure that the result is not easily overwritten
    """
    if os.path.exists(path):
        y = gui.question('Warning: The existed data will be Over-Written. continue? ')
        if not y:
            assert False
    else:
        with open(path, 'w') as file:
            file.write('\n')
