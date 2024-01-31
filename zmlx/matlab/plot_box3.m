function plot_box3(x, y, z, v, varargin)

% 获得参数的范围
x_min = get_val(varargin, 'x_min', min(x));
x_max = get_val(varargin, 'x_max', max(x));

y_min = get_val(varargin, 'y_min', min(y));
y_max = get_val(varargin, 'y_max', max(y));

z_min = get_val(varargin, 'z_min', min(z));
z_max = get_val(varargin, 'z_max', max(z));

% 各个方向的插值网格数
jx = get_val(varargin, 'jx', 100);
jy = get_val(varargin, 'jy', 100);
jz = get_val(varargin, 'jz', 100);


% z 方向
[xx, yy] = meshgrid(linspace(x_min, x_max, jx), linspace(y_min, y_max, jy));
zz = ones(size(xx)) * z_min;
vv = griddata(x, y, z, v, xx, yy, zz);
surf(xx, yy, zz, vv, "EdgeColor", "none", 'FaceColor', 'interp');
hold on

zz = ones(size(xx)) * z_max;
vv = griddata(x, y, z, v, xx, yy, zz);
surf(xx, yy, zz, vv, "EdgeColor", "none", 'FaceColor', 'interp');


% y 方向
[xx, zz] = meshgrid(linspace(x_min, x_max, jx), linspace(z_min, z_max, jz));
yy = ones(size(xx)) * y_min;
vv = griddata(x, y, z, v, xx, yy, zz);
surf(xx, yy, zz, vv, "EdgeColor", "none", 'FaceColor', 'interp');

yy = ones(size(xx)) * y_max;
vv = griddata(x, y, z, v, xx, yy, zz);
surf(xx, yy, zz, vv, "EdgeColor", "none", 'FaceColor', 'interp');


% x 方向
[yy, zz] = meshgrid(linspace(y_min, y_max, jy), linspace(z_min, z_max, jz));
xx = ones(size(yy)) * x_min;
vv = griddata(x, y, z, v, xx, yy, zz);
surf(xx, yy, zz, vv, "EdgeColor", "none", 'FaceColor', 'interp');

xx = ones(size(yy)) * x_max;
vv = griddata(x, y, z, v, xx, yy, zz);
surf(xx, yy, zz, vv, "EdgeColor", "none", 'FaceColor', 'interp');

