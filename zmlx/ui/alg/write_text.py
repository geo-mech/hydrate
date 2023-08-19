import os
from zmlx.ui.alg.make_dirs import make_dirs


def write_text(path, text, encoding=None):
    """
    Write the given text to a file. Automatically created when the folder where the file is located does not exist
    """
    folder = os.path.dirname(path)
    if len(folder) > 0 and not os.path.isdir(folder):
        make_dirs(folder)
    with open(path, 'w', encoding=encoding) as f:
        if text is None:
            f.write('')
        else:
            f.write(text)
