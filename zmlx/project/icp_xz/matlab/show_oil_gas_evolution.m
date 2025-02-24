
% 读取数据
d = load('evolution.txt');
idx = d(:,1)<5.8;
d = d(idx,:);

% Years, t_average, t_max, ratio, kg, ho, lo, ch4, steam, h2o, p_average, p_max


% 绘图
figure

plot(d(:,1), d(:,6), 'linewidth', 2, 'displayname', 'Heavy Oil')
hold on 
plot(d(:,1), d(:,7), 'linewidth', 2, 'displayname', 'Light Oil')
plot(d(:,1), d(:,8), 'linewidth', 2, 'displayname', 'Methane Gas')
plot(d(:,1), d(:,5), 'linewidth', 2, 'displayname', 'Kerogen')

xlabel('Time (year)')
ylabel('In-situ Mass (ton)')

legend  EdgeColor none
xlim([0 6])

