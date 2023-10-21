# ** is_sys = False
# ** text = '依赖项检查'
# ** menu = '帮助'
# ** on_toolbar = False
# ** tooltip = '检查程序运行所需要的各个依赖项是否存在'


from zmlx.alg.has_module import has_module
from zmlx.alg.pip_install import pip_install

names = ['numpy', 'scipy', 'matplotlib', 'pyqtgraph', 'PyQt5']

print('\n\n')

for name in names:
    if has_module(name):
        print(f'module exists: {name}')
    else:
        print('')
        print(f'module <{name}> not found, try to install by pip ... please wait')
        pip_install(name)

print('\n\n')
