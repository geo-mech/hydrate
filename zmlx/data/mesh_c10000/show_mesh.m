xy = load('xy'); tri=load('tri');

trimesh(tri, xy(:,1), xy(:,2))
axis equal
xlabel('x')
xlabel('y')
