
data = load('field_mass.txt');


X1 = data(:,1);
YMatrix1 = data(:,2:end) / 1e3;

%CREATEFIGURE(X1, YMatrix1)
%  X1:  x 数据的向量
%  YMATRIX1:  y 数据的矩阵

%  由 MATLAB 于 05-Feb-2024 22:26:16 自动生成

% 创建 figure
figure1 = figure;

% 创建 axes
axes1 = axes('Parent',figure1);
hold(axes1,'on');

% 使用 plot 的矩阵输入创建多行
plot1 = plot(X1,YMatrix1,'LineWidth',1.5,'Parent',axes1);
set(plot1(1),'DisplayName','甲烷');
set(plot1(2),'DisplayName','蒸汽', 'lineStyle', '-.');
set(plot1(3),'DisplayName','水', 'lineStyle', '-.');
set(plot1(4),'DisplayName','轻油');
set(plot1(5),'DisplayName','重油');
set(plot1(6),'DisplayName','干酪根', 'lineStyle', ':');
set(plot1(7),'DisplayName','焦炭', 'lineStyle', ':');

% 取消以下行的注释以保留坐标区的 X 范围
xlim(axes1,[0 20]);
% 取消以下行的注释以保留坐标区的 Y 范围
ylim(axes1,[0 50]);
box(axes1,'on');
hold(axes1,'off');
% 创建 legend
legend1 = legend(axes1,'show');
set(legend1,...
    'Position',[0.633884778318049 0.634007967814577 0.128793484718159 0.282396080113565], 'EdgeColor', [1,1,1] );

xlabel('时间 [年]')
ylabel('物质质量 [吨/米]')
% set(gca,'unit', 'centimeters', 'position', [2, 2, 8, 6]);


