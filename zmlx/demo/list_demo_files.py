from zmlx.demo.get_path import get_path
from zmlx.filesys.list_files import list_files
from zmlx.ui.alg.code_config import code_config


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
        if len(desc) > 0:
            results.append([file, desc])
    return results


def test():
    for file, desc in list_demo_files():
        print(file, desc)


if __name__ == '__main__':
    test()
