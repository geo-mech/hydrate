function show_col(name, index)


data = load(name);

% 去除掉虚拟单元
data = data(abs(data(:, 3)) < 100, :);

% 找到数据的范围
x_min = min(data(:,1));
x_max = max(data(:,1));

y_min = min(data(:,2));
y_max = max(data(:,2));

% 生成绘图数据
x = linspace(x_min, x_max, 200);
y = linspace(y_min, y_max, 300);
[x, y] = meshgrid(x, y);
if length(index) == 1
    z = data(:, index);
else
    if index(2) > 0
        z = data(:, index(1)) .* data(:, index(2));  % 此时为两列的乘积
    else
        z = data(:, index(1));
    end
end
if length(index) >= 3
    z = z * index(3);
end
z = griddata(data(:, 1), data(:, 2), z, x, y);

% 绘图
surf(x, y, z, 'EdgeColor','none', 'FaceColor', 'interp')
view(0, 90)
% xlim([x_min-1, x_max+1])
% ylim([y_min-1, y_max+1])
% axis equal

box on 
cm = slanCM('coolwarm', 20);
colormap(cm)

xlabel('x [m]')
ylabel('y [m]')

set(gca,'unit', 'centimeters', 'position', [2, 2, 3, 5]);

% colorbar



