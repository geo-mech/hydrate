
% 读取数据
d = load('evolution.txt');
idx = d(:,1)<5.8;
d = d(idx,:);

% Years, t_average, t_max, ratio, kg, ho, lo, ch4, steam, h2o, p_average, p_max


% 绘图
figure

yyaxis left 

plot(d(:,1), d(:,9), 'linewidth', 2, 'displayname', 'Steam')

xlabel('Time (year)')
ylabel('Steam Mass (ton)')

yyaxis right 
plot(d(:,1), d(:,10), 'linewidth', 2, 'displayname', 'Water')
ylabel('Water Mass (ton)')


legend  EdgeColor none
xlim([0 6])

