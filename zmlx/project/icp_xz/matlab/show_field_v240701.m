function show_field_v240701(d, varargin)

x = [d(:,1); d(:,1)];
y = [d(:,2); d(:,2)+20];
z = [d(:,3); d(:,3)];

idx = get_val(varargin, 'idx', 11);
if length(idx) == 1
    v = [d(:,idx); d(:,idx)];
else
    v = d(:,idx(1)) .* d(:, idx(2));
    v = [v; v];
end

figure

plot_box3(x, y, z, v, 'z_min', -14.75, 'z_max', 14.75, ...
    'y_min', 0, 'y_max', 8, 'jy', 3)

hold on
[x, y, z] = cylinder(0.2);
surf(x+15, z*8.25-0.25, y+7.5, zeros(size(x)), 'FaceColor', 'red', 'EdgeColor', 'none')
surf(x+15, z*8.25-0.25, y-7.5, zeros(size(x)), 'FaceColor', 'red', 'EdgeColor', 'none')
surf(x+0.25, z*8.25-0.25, y, zeros(size(x)), 'FaceColor', 'black', 'EdgeColor', 'none')

xlabel('x / m')
zlabel('z / m')
yticks([])

axis equal
box on
ax = gca;
ax.BoxStyle = 'full';

view(22, 16)

% xlim([0, 15])
zlim([-15,15])
cmin = get_val(varargin, 'cmin', min(v));
cmax = get_val(varargin, 'cmax', max(v));
caxis([cmin, cmax])

cm = get_val(varargin, 'cm', parula());
colormap(cm)

position = get_val(varargin, 'position', []);
if length(position) == 4
    % [2, 2, 5, 3]
    set(gca, 'unit', 'centimeters', 'position', position);
end
