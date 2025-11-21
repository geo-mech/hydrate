from pyvistaqt import QtInteractor

from zmlx.ui import gui


def get_vtk_view(caption=None, on_top=None, init=None, oper=None):
    gui.get_widget(
        the_type=QtInteractor, caption=caption,
        on_top=on_top, init=init, oper=oper)


def setup_ui():
    gui.add_func('get_vtk_view', get_vtk_view)

    def show_sphere(plotter):
        import pyvista as pv
        sphere = pv.Sphere()
        sphere["高程"] = sphere.points[:, 2]
        plotter.add_mesh(sphere, scalars="高程", cmap="terrain")
        plotter.add_axes()
        plotter.add_scalar_bar("高程")

    gui.add_action(
        menu=['帮助', 'VtkView'], text='显示球体1', slot=lambda: gui.get_vtk_view(caption='球体1', init=show_sphere),
    )

    gui.add_action(
        menu=['帮助', 'VtkView'], text='显示球体2', slot=lambda: gui.get_vtk_view(caption='球体2', init=show_sphere),
    )


def main():
    from zmlx.alg.sys import first_execute
    if first_execute(__file__):
        gui.execute(func=setup_ui, keep_cwd=False, close_after_done=False)


if __name__ == '__main__':
    main()
