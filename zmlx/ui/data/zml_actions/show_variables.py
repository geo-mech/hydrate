# ** is_sys = True
# ** tooltip = '显示工作区的中的变量'
# ** text = '显示Workspace变量'

def show_variables():
    from zml import gui
    space = gui.window().console_widget.workspace
    print('Variables in workspace: ')
    n = 0
    for key in list(space.keys()):
        print(f'\t{key}: {type(space[key])}')
        n += 1
    print(f'Totally {n} Variables\n')


show_variables()
