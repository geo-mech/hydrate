import numpy as np

from icp_xz.iterate import iterate
from icp_xz.show import show
from zmlx.alg.join_cols import join_cols
from zmlx.config import seepage
from zmlx.filesys.join_paths import join_paths
from zmlx.filesys.tag import print_tag
from zmlx.ui import gui
from zmlx.utility.GuiIterator import GuiIterator
from zmlx.utility.SaveManager import SaveManager
from zmlx.utility.SeepageCellMonitor import SeepageCellMonitor


def save_reaction_dm(space: dict, folder=None):
    if folder is not None:
        t2dm = space.get('reaction_dm', None)
        if t2dm is not None:
            assert isinstance(t2dm, list)
            data = join_cols(*t2dm)
            np.savetxt(join_paths(folder, 'reaction_dm.txt'),
                       data, fmt='%.5e')


def solve(space: dict, folder=None,
          time_max=3600.0 * 24.0 * 365.0 * 20.0):
    """
    在工作区内执行求解操作.
    """
    if folder is not None:  # 输出标签.
        print_tag(folder)
        if gui.exists():
            gui.title(f'Data folder: {folder}')

    def do_show():
        show(space,
             folder=join_paths(folder, 'figures'))

    # 在迭代的同时绘图
    gui_iter = GuiIterator(iterate, do_show)

    # 模型
    model = space.get('model')

    def get_day():
        return seepage.get_time(model) / (3600 * 24)

    save_model = SaveManager(join_paths(folder, 'models'),
                             30, get_day,
                             save=model.save,
                             ext='.seepage', time_unit='d')

    def do_save_cells(f_name):
        seepage.print_cells(f_name,
                            model,
                            export_mass=True)

    save_cells = SaveManager(join_paths(folder, 'cells'),
                             30, get_day,
                             save=do_save_cells,
                             ext='.txt', time_unit='d')

    def save(**kwargs):
        save_model(**kwargs)
        save_cells(**kwargs)

    # 监视生产状况.
    monitor = space.get('monitor')
    assert isinstance(monitor, SeepageCellMonitor)

    # 迭代到给定的时间
    while seepage.get_time(model) < time_max:
        r = gui_iter(space)
        save()  # 根据给定的间隔去保存
        step = seepage.get_step(model)
        if step % 10 == 0:
            print(
                f'step = {step}, '
                f'dt = {seepage.get_dt(model, as_str=True)}, '
                f'time = {seepage.get_time(model, as_str=True)}, '
                f'report={r}')

        if step % 200 == 0:
            monitor.save(join_paths(folder, 'prod.txt'))
            save_reaction_dm(space, folder)

    # 最后，保存最终的状态.
    save(check_dt=False)
    monitor.save(join_paths(folder, 'prod.txt'))
    save_reaction_dm(space, folder)
