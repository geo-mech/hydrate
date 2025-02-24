
% 读取数据
d = load('prod.txt');
d(:,1)=d(:,1)/(3600*24*365);
d(:,2:end)=d(:,2:end)/1000;


% 绘图
figure

% yyaxis left
plot(d(:,1), d(:,6), 'linewidth', 2, 'displayname', 'Heavy Oil')
hold on
plot(d(:,1), d(:,5), 'linewidth', 2, 'displayname', 'Light Oil')
plot(d(:,1), d(:,2), 'linewidth', 2, 'displayname', 'Methane Gas')
plot(d(:,1), d(:,3)+d(:,4), 'linewidth', 2, 'displayname', 'Water')

xlabel('Time (year)')
ylabel('Cumulative Mass (ton)')

% yyaxis right
% plot(d(2:end,1), diff(d(:,6))./diff(d(:,1)), 'linewidth', 2, 'displayname', 'Heavy Oil')
% hold on
% plot(d(2:end,1), diff(d(:,5))./diff(d(:,1)), 'linewidth', 2, 'displayname', 'Light Oil')
% plot(d(2:end,1), diff(d(:,2))./diff(d(:,1)), 'linewidth', 2, 'displayname', 'Methane Gas')
% % plot(d(2:end,1), diff(d(:,3)+d(:,4))./diff(d(:,1)), 'linewidth', 2, 'displayname', 'Water')
% ylabel('Mass Rate (ton/year)')
% ylim([0,400])



legend  EdgeColor none
xlim([6 7])

