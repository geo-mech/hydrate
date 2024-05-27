function show_rect3(rect3, varargin)
% 
% 显示三维的矩形. 示例：
%     d = load('show_rect3.txt')
%     show_rect3(d);
%
% 对于每一个矩形，有颜色和透明度. 如果需要指定颜色，则使用color选项；
%     要使用透明度，则使用alpha选项. 
% 

% 默认参数值
color = get_val(varargin, 'color', 0);
alpha = get_val(varargin, 'alpha', 1);
FaceColor = get_val(varargin, 'face', 'flat');
edge = get_val(varargin, 'edge', 'none');
linewidth = get_val(varargin, 'linewidth', 0.1);


if length(color) == 1
    color = ones(size(rect3, 1), 1) * color;
end

if length(alpha) == 1
    alpha = ones(size(rect3, 1), 1) * alpha;
end

alphaLevels = 30;

xx = cell(alphaLevels, 1);
yy = cell(alphaLevels, 1);
zz = cell(alphaLevels, 1);
cc = cell(alphaLevels, 1);
for i = 1: alphaLevels
    xx{i} = [];
    yy{i} = [];
    zz{i} = [];
    cc{i} = [];
end

for i = 1: size(rect3, 1)
    o = rect3(i, 1:3);
    a = rect3(i, 4:6);
    b = rect3(i, 7:9);
    c = a + b - o;
    d = o * 2 - c;
    e = b * 2 - c;
    f = a * 2 - c;
    if alpha(i) <= 0
        continue
    end
    ind = round(alpha(i)*alphaLevels);
    ind = max(1, min(alphaLevels, ind));

    x = [e(1), c(1); d(1), f(1)];
    y = [e(2), c(2); d(2), f(2)];
    z = [e(3), c(3); d(3), f(3)];
    c = [color(i), color(i); color(i), color(i)];

    xx{ind} = [xx{ind}; x; [nan, nan]];
    yy{ind} = [yy{ind}; y; [nan, nan]];
    zz{ind} = [zz{ind}; z; [nan, nan]];
    cc{ind} = [cc{ind}; c; [nan, nan]];
end

for ind =1: alphaLevels
    if ind < alphaLevels
        surf(xx{ind}, yy{ind}, zz{ind}, cc{ind}, 'FaceColor', FaceColor, 'EdgeColor', edge, 'FaceAlpha', ind/alphaLevels)
    else
        surf(xx{ind}, yy{ind}, zz{ind}, cc{ind}, 'FaceColor', FaceColor, 'EdgeColor', 'none', 'FaceAlpha', ind/alphaLevels, 'linewidth', linewidth)
    end
    hold on 
end

xlabel(get_val(varargin, 'xlabel', 'x / m'))
ylabel(get_val(varargin, 'ylabel', 'y / m'))
zlabel(get_val(varargin, 'zlabel', 'z / m'))

axis equal; 
box on
ax = gca;
ax.BoxStyle = 'full';

colormap(get_val(varargin, 'cm', jet()));

h = colorbar; % 显示 colorbar

% 修改 colorbar 的标签
ylabel(h, get_val(varargin, 'clabel', ''))

% 添加 colorbar 的标题
title(h, get_val(varargin, 'ctitle', ''));

