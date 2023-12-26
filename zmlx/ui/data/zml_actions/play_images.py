# ** text = '播放图片'
# ** is_sys = False


from zmlx.filesys.list_files import list_files
from zmlx.ui.GuiBuffer import gui


files = list_files(exts=['.jpg', '.png'])
for file in files:
    print(file)
    gui.open_image(file, caption='播放图片', on_top=False)
    gui.break_point()
