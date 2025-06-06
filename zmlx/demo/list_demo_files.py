import os.path

from zmlx.alg.fsys import list_files
from zmlx.alg.base import code_config
from zmlx.demo.path import get_path


def list_demo_files():
    """
    列出demo文件的路径和说明
    """
    files = list_files(get_path(), exts=['.py'])
    results = []
    for file in files:
        if '__Trash' in file or 'debugging' in file:
            continue
        cfg = code_config(path=file, encoding='utf-8')
        desc = cfg.get('desc', '')
        if isinstance(desc, str):
            if len(desc) > 0:
                results.append([file, desc])
    return results


def test():
    files = list_demo_files()
    folder = get_path()
    for idx in range(len(files)):
        file, desc = files[idx]
        print(idx, os.path.relpath(file, folder), desc)


if __name__ == '__main__':
    test()
