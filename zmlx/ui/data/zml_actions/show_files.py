import os

from zml import gui

print(f'Work Directory: {os.path.abspath(os.getcwd())}')
dirs = os.listdir()
for i in range(len(dirs)):
    print(f'\t{i + 1}: {dirs[i]}')
    if i + 1 >= 9:
        print(f'\t...\nTotally {len(dirs)} Files in Work Directory')
        break
gui.show_files()
