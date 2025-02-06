from zml import *


# core = DllCore(dll=load_cdll(name='beta.dll',
#                              first=os.path.dirname(__file__)))


def update_sand(model: Seepage, *args, **kwargs):
    model.update_sand(*args, **kwargs)

# if __name__ == '__main__':
#     print(core.time_compile)
