# ** desc = '天然气藏的降压开发过程模拟'

from scipy.interpolate import NearestNDInterpolator

from zmlx import *


def create(jx, jz):
    mesh = create_cube(
        x=np.linspace(-50, 50, jx + 1),
        y=[-0.5, 0.5],
        z=np.linspace(-15, 15, jz + 1)
    )
    perms = []
    for face in mesh.faces:
        assert isinstance(face, SeepageMesh.Face)
        x0, y0, z0 = face.get_cell(0).pos
        x1, y1, z1 = face.get_cell(1).pos
        if abs(x0 - x1) < 1.0e-3:
            perms.append(1.0e-15)
        else:
            perms.append(1.0e-14)

    for cell in mesh.cells:
        assert isinstance(cell, SeepageMesh.Cell)
        x, y, z = cell.pos
        dz = math.cos(x * math.pi / 50) * 15
        cell.pos = [x, y, z + dz]

    points = np.array([face.pos for face in mesh.faces])
    interp = NearestNDInterpolator(points, perms)

    def get_perm(*pos):
        return interp(pos)

    center = mesh.get_nearest_cell(pos=[0, 0, 20]).pos

    def is_prod(*pos):
        return point_distance(pos, center) < 0.1

    def porosity(*pos):
        return 1e6 if is_prod(*pos) or abs(pos[0]) > 49 else 0.3

    def pressure(*pos):
        return 3e6 if is_prod(*pos) else 10e6

    gas = create_ch4(name='gas')
    wat = Seepage.FluDef(den=1000.0, vis=1.0e-3, specific_heat=4200, name='wat')

    fludefs = [gas, wat]

    def get_s(*pos):
        if pos[2] > 0:
            return {'gas': 1}
        else:
            return {'wat': 1}

    # 创建模型
    model = seepage.create(
        mesh=mesh,
        fludefs=fludefs,
        porosity=porosity,
        pore_modulus=100e6,
        denc=5e6,
        temperature=285.0,
        p=pressure,
        s=get_s,
        perm=get_perm,
        dt_min=1, dt_max=24 * 3600 * 5, dv_relative=0.1,
    )
    return model


def show(model: Seepage, jx, jz, folder=None):
    def on_figure(fig):
        fig.suptitle(f'Model when time = {seepage.get_time(model, as_str=True)}')
        opts = dict(ncols=2, nrows=1, xlabel='x/m', ylabel='z/m', aspect='equal')
        shape = [jx, jz]
        x = seepage.get_x(model, shape=shape)
        y = seepage.get_z(model, shape=shape)
        p = seepage.get_p(model, shape=shape) / 1e6
        v = seepage.get_v(model, shape=shape)
        s = seepage.get_v(model, shape=shape, fid=1) / v
        args = [fig, add_contourf, x, y]
        add_axes2(*args, p, title='压力 (MPa)', cbar=dict(label='Pressure', shrink=0.5), index=1, **opts)
        add_axes2(*args, s, title='水饱和度', cbar=dict(label='Saturation', shrink=0.5), index=2, **opts)

    fname = make_fname(time=seepage.get_time(model) / (3600 * 24), folder=folder, ext='jpg', unit='d')
    plot(on_figure, caption=f'Seepage({model.handle})', clear=True, fname=fname, tight_layout=True)


def main(folder=None):
    fig_folder = os.path.join(folder, 'all_figures') if folder is not None else None
    jx, jz = 100, 30
    model = create(jx, jz)
    seepage.solve(
        model, close_after_done=False,
        folder=folder,
        time_unit='d',
        extra_plot=lambda: show(model, jx, jz, fig_folder),
        time_forward=3600 * 24 * 365
    )


if __name__ == '__main__':
    main()
