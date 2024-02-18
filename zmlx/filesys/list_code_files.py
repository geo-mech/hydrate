from zmlx.filesys.list_files import list_files


def list_code_files(path=None, exts=None):
    if exts is None:
        return list_files(path=path, exts={'.h', '.hpp', '.c', '.cpp', '.py', '.pyw', '.m'})
    else:
        return list_files(path=path, exts=exts)


if __name__ == '__main__':
    for file in list_code_files(path='..'):
        print(file)
