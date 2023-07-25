def zml_names():
    try:
        space = {}
        exec('from zmlx import *', space)
        return list(set(space.keys()))
    except:
        return []


if __name__ == '__main__':
    print(zml_names())
