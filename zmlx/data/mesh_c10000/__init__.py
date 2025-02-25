import os

from zml import read_text, Mesh3
from zmlx.seepage_mesh.from_mesh3 import face_centered

xy_data = read_text(os.path.join(os.path.dirname(__file__), 'xy'))
tri_data = read_text(os.path.join(os.path.dirname(__file__), 'tri'))

x = []
y = []

for line in xy_data.splitlines():
    values = [float(s) for s in line.split()]
    if len(values) == 2:
        x.append(values[0])
        y.append(values[1])

tri = []
for line in tri_data.splitlines():
    values = [int(s) - 1 for s in line.split()]
    if len(values) == 3:
        tri.append(tuple(values))


def get_mesh3(z=0):
    mesh = Mesh3()

    for idx in range(len(x)):
        mesh.add_node(x[idx], y[idx], z=z)

    for t in tri:
        links = [mesh.add_link([mesh.get_node(t[i]), mesh.get_node(t[j])]) for (i, j) in [(0, 1), (1, 2), (2, 0)]]
        mesh.add_face(links=links)

    return mesh


def get_face_centered_seepage_mesh(z=0, thick=1.0):
    mesh3 = get_mesh3(z=z)
    return face_centered(mesh=mesh3, thick=thick)


if __name__ == '__main__':
    print(get_face_centered_seepage_mesh())
