import os


def read_text(path, encoding=None, default=None):
    """
    Read text from a file in text format
    """
    try:
        if os.path.isfile(path):
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        return default
    except:
        return default
