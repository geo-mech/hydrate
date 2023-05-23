% function showf3(data)
% 
% if nargin == 0
%     data = load(lastfileof('data'));
% end

% data = load(lastfileof('data'));
clear
data = load(lastfileof('h2o_inj', 1));
% data = load('hf2\fractures.c14');

figure

xx = [];
yy = [];
zz = [];
cc = [];
aa = [];
a_min = 0;
a_max = max(a_min+1.0e-10, max(data(:, 14)));


for i = 1: size(data, 1)
    x = reshape(data(i, 1:4), 2, 2);
    y = reshape(data(i, 5:8), 2, 2);
    z = reshape(data(i, 9:12), 2, 2);
    x(end+1, :)=nan;
    y(end+1, :)=nan;
    z(end+1, :)=nan;
    c = ones(size(x)) * data(i, 13);
    a = ones(size(x)) * data(i, 14);
    a = (a - a_min)/(a_max - a_min);
    a = 1-(1-a).^4;
    xx(end+1:end+3, :) = x;
    yy(end+1:end+3, :) = y;
    zz(end+1:end+3, :) = z;
    cc(end+1:end+3, :) = c;
    aa(end+1:end+3, :) = a;
end

n_alpha = 20;
for i = n_alpha:-1:1
    a0 = (i-1)/n_alpha;
    a1 = i / n_alpha;
    ind = a0 <= aa & aa <= a1;
    x = xx(ind);
    y = yy(ind);
    z = zz(ind);
    c = cc(ind);
    if numel(x) < 4
        continue
    end
    x = reshape(x, length(x)/2, 2);
    y = reshape(y, length(y)/2, 2);
    z = reshape(z, length(z)/2, 2);
    c = reshape(c, length(c)/2, 2);
    surf(x, y, z, c, 'FaceAlpha', min(1, max(0.03, (a0+a1)/2)), 'EdgeAlpha', 0.05);
    if i == 2
        shading interp
    end
    hold on
end
axis equal
% shading interp
box on 
ax = gca;
ax.BoxStyle = 'full';
cm = [0 0 1;0 0.1875 1;0 0.375 1;0 0.5625 1;0 0.75 1;0 0.9375 1;0.125 1 0.875;
    0.3125 1 0.6875;0.5 1 0.5;0.6875 1 0.3125;0.875 1 0.125;1 0.9375 0;
    1 0.75 0;1 0.5625 0;1 0.375 0;1 0.1875 0];
colormap(cm)
% colorbar
xlabel('x [m]')
ylabel('y [m]')
zlabel('z [m]')

view(-50, 70)
