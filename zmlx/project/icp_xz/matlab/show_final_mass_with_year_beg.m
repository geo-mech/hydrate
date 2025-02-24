data = [];

% d = load('1.0\prod.txt');
% d = d(end,:);
% d(1) = 1.0;
% data(end+1,:) = d;
% 
% d = load('2.0\prod.txt');
% d = d(end,:);
% d(1) = 2.0;
% data(end+1,:) = d;
% 
% d = load('3.0\prod.txt');
% d = d(end,:);
% d(1) = 3.0;
% data(end+1,:) = d;
% 
% d = load('4.0\prod.txt');
% d = d(end,:);
% d(1) = 4.0;
% data(end+1,:) = d;

d = load('5.0\prod.txt');
d = d(end,:);
d(1) = 5.0;
data(end+1,:) = d;

d = load('6.0\prod.txt');
d = d(end,:);
d(1) = 6.0;
data(end+1,:) = d;

d = load('7.0\prod.txt');
d = d(end,:);
d(1) = 7.0;
data(end+1,:) = d;

d = load('8.0\prod.txt');
d = d(end,:);
d(1) = 8.0;
data(end+1,:) = d;

d = load('9.0\prod.txt');
d = d(end,:);
d(1) = 9.0;
data(end+1,:) = d;

d = load('10.0\prod.txt');
d = d(end,:);
d(1) = 10.0;
data(end+1,:) = d;

d = load('11.0\prod.txt');
d = d(end,:);
d(1) = 11.0;
data(end+1,:) = d;

d = load('12.0\prod.txt');
d = d(end,:);
d(1) = 12.0;
data(end+1,:) = d;

d = load('13.0\prod.txt');
d = d(end,:);
d(1) = 13.0;
data(end+1,:) = d;

d = load('14.0\prod.txt');
d = d(end,:);
d(1) = 14.0;
data(end+1,:) = d;

d = load('15.0\prod.txt');
d = d(end,:);
d(1) = 15.0;
data(end+1,:) = d;

data(:,2:end)=data(:,2:end)/1000;

% 绘图
figure

plot(data(:,1), data(:,6), 'linewidth', 2, 'displayname', 'Heavy Oil')
hold on 
plot(data(:,1), data(:,5), 'linewidth', 2, 'displayname', 'Light Oil')
plot(data(:,1), data(:,2), 'linewidth', 2, 'displayname', 'Methane Gas')
plot(data(:,1), data(:,4), 'linewidth', 2, 'displayname', 'Water')

xlabel('Time Begin (Year)')
ylabel('Cumulative Mass (ton)')

legend  EdgeColor none
% xlim([0 6])


