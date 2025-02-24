data = [];

d = load('2000.0\prod.txt');
d = d(end,:);
d(1) = 2000.0;
data(end+1,:) = d;

d = load('3000.0\prod.txt');
d = d(end,:);
d(1) = 3000.0;
data(end+1,:) = d;

d = load('4000.0\prod.txt');
d = d(end,:);
d(1) = 4000.0;
data(end+1,:) = d;

d = load('5000.0\prod.txt');
d = d(end,:);
d(1) = 5000.0;
data(end+1,:) = d;

d = load('6000.0\prod.txt');
d = d(end,:);
d(1) = 6000.0;
data(end+1,:) = d;

d = load('7000.0\prod.txt');
d = d(end,:);
d(1) = 7000.0;
data(end+1,:) = d;

d = load('8000.0\prod.txt');
d = d(end,:);
d(1) = 8000.0;
data(end+1,:) = d;

d = load('9000.0\prod.txt');
d = d(end,:);
d(1) = 9000.0;
data(end+1,:) = d;

d = load('10000.0\prod.txt');
d = d(end,:);
d(1) = 10000.0;
data(end+1,:) = d;

data(:,1)=data(:,1)/1000;
data(:,2:end)=data(:,2:end)/1000;

% 绘图
figure

plot(data(:,1), data(:,6), 'linewidth', 2, 'displayname', 'Heavy Oil')
hold on 
plot(data(:,1), data(:,5), 'linewidth', 2, 'displayname', 'Light Oil')
plot(data(:,1), data(:,2), 'linewidth', 2, 'displayname', 'Methane Gas')
plot(data(:,1), data(:,4), 'linewidth', 2, 'displayname', 'Water')

xlabel('Power (kW)')
ylabel('Cumulative Mass (ton)')

legend  EdgeColor none
% xlim([0 6])


