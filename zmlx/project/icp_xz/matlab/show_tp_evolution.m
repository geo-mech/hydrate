
% 读取数据
d = load('evolution.txt');
idx = d(:,1)<5.8;
d = d(idx,:);

% Years, t_average, t_max, ratio, kg, ho, lo, ch4, steam, h2o, p_average, p_max


% 绘图
figure

yyaxis left 

plot(d(:,1), d(:,2), 'linewidth', 2, 'displayname', 'T_{average}')
hold on
plot(d(:,1), d(:,3), 'linewidth', 2, 'LineStyle', '-.', 'displayname', 'T_{max}')

xlabel('Time (year)')
ylabel('Temperature (K)')

yyaxis right 
plot(d(:,1), d(:,11)/1e6, 'linewidth', 2, 'displayname', 'Pressure')
ylabel('Pressure (MPa)')


legend  EdgeColor none
xlim([0 6])

