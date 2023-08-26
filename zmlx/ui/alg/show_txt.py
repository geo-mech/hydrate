from zmlx.ui.alg.read_text import read_text
from zmlx.ui.alg.show_fileinfo import show_fileinfo
import os
from zml import gui


def show_txt(filepath):
    try:
        if os.path.getsize(filepath) / 1024 < 100:
            if gui.exists():
                gui.open_text(filepath)
            else:
                print(f'{filepath}:\n\n')
                print(read_text(path=filepath, encoding='utf-8'))
                print('\n')
        else:
            show_fileinfo(filepath)
    except:
        pass
