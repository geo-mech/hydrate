import os


def list_files(path=None, keywords=None):
    """
    列出给定路径下的所有的文件的路径。其中这些文件的完整路径中，应该包含所有给定的关键字 keywords
    """
    if path is None:
        path = os.getcwd()

    if os.path.isfile(path):
        try:
            if keywords is None:
                return [path, ]
            else:
                for key in keywords:
                    if key not in path:
                        return []
                return [path, ]
        except:
            return []
    elif os.path.isdir(path):
        files = []
        for name in os.listdir(path):
            files = files + list_files(os.path.join(path, name), keywords=keywords)
        return files
    else:
        return []


if __name__ == '__main__':
    for file in list_files('..', keywords=['pyc', 'plot']):
        print(file)

