from zmlx.filesys.get_lines import get_lines
from zmlx.filesys.list_code_files import list_code_files
from zmlx.ui.GuiBuffer import gui


def count_lines(path=None, exts=None):
    lines = 0
    for path in list_code_files(path=path, exts=exts):
        n = get_lines(path)
        lines += n
        print(f'{path}: {n}')
        gui.break_point()
    print(f'\n\nAll lines is: {lines}')


if __name__ == '__main__':
    from zml import get_dir

    count_lines(path=get_dir())
