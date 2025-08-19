
import os

def get_path(*args):
    return os.path.join(os.path.dirname(__file__), *args)


def get_files():
    return [
        get_path('message.py'),
        get_path('string_table.py'),
        get_path('seepage.py'),
        get_path('examples.py'),
        get_path('editors.py'),
    ]
