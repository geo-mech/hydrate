from zml import read_text
import os

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
