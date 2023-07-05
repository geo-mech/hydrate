from zml import gui
import os


def list_files(folder=os.getcwd(), exts=None):
    if exts is None:
        exts = ['.h', '.hpp', '.c', '.cpp', '.py', '.pyw']
    if not os.path.isdir(folder):
        return []
    paths = []
    for name in os.listdir(folder):
        gui.break_point()
        path = os.path.join(folder, name)
        if os.path.isdir(path):
            for subpath in list_files(path, exts):
                paths.append(subpath)
            continue
        if os.path.isfile(path):
            if os.path.splitext(path)[1] in exts:
                paths.append(path)
            continue
    return paths


def get_lines(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return len(file.readlines())
    except:
        return 0


def count_lines(folder=os.getcwd(), exts=None):
    lines = 0
    for path in list_files(folder=folder, exts=exts):
        n = get_lines(path)
        lines += n
        print(f'{path}: {n}')
        gui.break_point()
    print(f'\n\nAll lines is: {lines}')


if __name__ == '__main__':
    count_lines()

