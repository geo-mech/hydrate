from zmlx import *


def create():
    config = TherFlowConfig()
    config.add_fluid(TherFlowConfig.FluProperty(den=50, vis=1.0e-4))
    config.add_fluid(TherFlowConfig.FluProperty(den=1000, vis=1.0e-3))
    config.set(disable_update_den=True, disable_update_vis=True,
               disable_ther=True, disable_heat_exchange=True)

    mesh = create_cube(
        np.linspace(0, 100, 101),
        np.linspace(0, 100, 101),
        (-0.5, 0.5))

    x0, x1 = mesh.get_pos_range(0)
    y0, y1 = mesh.get_pos_range(1)

    for cell in mesh.cells:
        x, y, z = cell.pos
        if abs(x - x0) < 0.1 or abs(x - x1) < 0.1 or abs(y - y0) < 0.1 or abs(
                y - y1) < 0.1:
            cell.vol = 1.0e8

    model = config.create(mesh, porosity=0.2, pore_modulus=100e6, p=1e6,
                          temperature=280,
                          s=(1, 0), perm=1e-14)

    cell = model.get_nearest_cell((50, 50, 0))
    model.add_injector(fluid_id=1, flu=cell.get_fluid(1), pos=cell.pos,
                       radi=0.1, opers=[(0, 1.0e-5)])

    config.set_dt_max(model, 3600 * 24)

    return config, model


def show(config, model):
    kwargs = {'gui_only': True,
              'title': f'plot when model.time={time2str(config.get_time(model))}'}
    xy = [c.pos[0] for c in model.cells], [c.pos[1] for c in model.cells]
    tricontourf(*xy, [c.pre for c in model.cells], caption='压力', **kwargs)
    for i in range(2):
        tricontourf(*xy, [c.get_fluid(i).vol_fraction for c in model.cells],
                    caption=f'饱和度{i}', **kwargs)


def solve(config, model):
    iterate = GuiIterator(iterate=config.iterate,
                          plot=lambda: show(config, model))

    while config.get_time(model) < 365 * 24 * 3600:
        r = iterate(model)
        step = config.get_step(model)
        if step % 10 == 0:
            dt, t = time2str(config.get_dt(model)), time2str(
                config.get_time(model))
            print(f'step = {step}, dt = {dt}, time = {t}, report={r}')


def execute(gui_mode=True, close_after_done=False):
    if gui_mode:
        gui.execute(lambda: solve(*create()), close_after_done=close_after_done)
    else:
        solve(*create())


if __name__ == '__main__':
    execute()
