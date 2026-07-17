from zmlx.system import execute_once


@execute_once(file=__file__)
def _install():
    from zmlx.ui import gui

    def show_sphere(plotter):
        import pyvista as pv
        sphere = pv.Sphere()
        sphere["高程"] = sphere.points[:, 2]
        plotter.add_mesh(sphere, scalars="高程", cmap="terrain")
        plotter.add_axes()
        plotter.add_scalar_bar("高程")

    gui.add_action(
        menu=['帮助', 'VtkView'], text='显示球体1',
        slot=lambda: gui.get_vtk_view(caption='球体1', init=show_sphere),
    )

    gui.add_action(
        menu=['帮助', 'VtkView'], text='显示球体2',
        slot=lambda: gui.get_vtk_view(caption='球体2', init=show_sphere),
    )


@execute_once(file=__file__)
def setup_ui():
    from zmlx.ui import gui
    gui.add_action(
        menu=['帮助', '加载'],
        text='VtkView',
        slot=_install,
    )
