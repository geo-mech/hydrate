from zml import read_text
from zmlx.filesys.get_size_mb import get_size_mb
from zmlx.filesys.show_fileinfo import show_fileinfo


def show_txt(filepath):
    try:
        if get_size_mb(filepath) < 0.5:
            from zmlx.ui.MainWindow import get_window
            window = get_window()
            if window is not None:
                window.open_text(filepath)
            else:
                print(f'{filepath}:\n\n')
                print(read_text(path=filepath, encoding='utf-8'))
                print('\n')
        else:
            show_fileinfo(filepath)
    except:
        pass
