import os


def list_files(path=None, keywords=None, exts=None):
    """
    列出给定路径下的所有的文件的路径。其中这些文件的完整路径中，应该包含所有给定的关键字 keywords
    另外，如果指定了扩展名exts，则将只在给定的这些文件类型中搜索
    """
    if path is None:
        path = os.getcwd()

    if os.path.isfile(path):
        try:
            is_ok = True
            if keywords is not None:
                for key in keywords:
                    if key not in path:
                        is_ok = False
                        break
            if is_ok:
                if exts is not None:
                    try:
                        ext = os.path.splitext(path)[1]
                        if ext not in exts:
                            is_ok = False
                    except:
                        is_ok = False
            if is_ok:
                return [path, ]
            else:
                return []
        except:
            return []
    elif os.path.isdir(path):
        files = []
        for name in os.listdir(path):
            files = files + list_files(os.path.join(path, name), keywords=keywords, exts=exts)
        return files
    else:
        return []


if __name__ == '__main__':
    for file in list_files('..', keywords=['pyc', 'plot']):
        print(file)
