text = '播放图片'


def slot():
    from zmlx.alg.fsys import list_files
    from zmlx.ui.gui_buffer import gui

    def task():
        files = list_files(exts=['.jpg', '.png'])
        for idx in range(len(files)):
            print(files[idx])
            gui.open_image(files[idx], caption='播放图片',
                           on_top=False)
            gui.break_point()
            gui.progress(val_range=[0, len(files)], value=idx,
                         visible=True, label="Playing Figures ")

        gui.progress(visible=False)

    gui.start_func(task)
