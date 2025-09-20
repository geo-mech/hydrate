
import os

def get_path(*args):
    return os.path.join(os.path.dirname(__file__), *args)


def get_files():
    folder = os.path.dirname(__file__)
    files = []
    for name in os.listdir(folder):
        if name.endswith('.py'):
            if name != '__init__.py':
                files.append(get_path(name))
    return files


if __name__ == '__main__':
    print(get_files())
