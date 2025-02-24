
% 基础模型，绘制蒸汽的饱和度场

% 1年
fname = find_file_by_day('cells', 365);
disp(fname)
d = load(fname);
d=d(1:end-1,:); 
show_field_v240701(d, 'idx', [6, 8], 'cm', parula(20), ...
    'position',[2, 2, 5, 3], 'cmin', 0, 'cmax', 8); 
colorbar
printfig('dir', 'steam-1y', 'dpi', 2000)


% 5年
fname = find_file_by_day('cells', 365*4.8);
disp(fname)
d = load(fname);
d=d(1:end-1,:); 
show_field_v240701(d, 'idx', [6, 8], 'cm', parula(20), ...
    'position',[2, 2, 5, 3], 'cmin', 0, 'cmax', 8); 
colorbar
printfig('dir', 'steam-5y', 'dpi', 2000)

% 6年
fname = find_file_by_day('cells', 365*6);
disp(fname)
d = load(fname);
d=d(1:end-1,:); 
show_field_v240701(d, 'idx', [6, 8], 'cm', parula(20), ...
    'position',[2, 2, 5, 3], 'cmin', 0, 'cmax', 8); 
colorbar
printfig('dir', 'steam-6y', 'dpi', 2000)
