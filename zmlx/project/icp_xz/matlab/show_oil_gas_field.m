
% 基础模型，绘制蒸汽的饱和度场
%         0. gas: ch4, steam
%         1. h2o
%         2. lo = light oil
%         3. ho = heavy oil
%         4. solid: kg = kerogen, char

dpi = 2000;

% 1年
fname = find_file_by_day('cells', 365);
disp(fname)
d = load(fname);
d=d(1:end-1,:); 

show_field_v240701(d, 'idx', [6, 7], 'cm', parula(20), ...
    'position',[2, 2, 5, 3],'cmin',0,'cmax',15); 
colorbar
printfig('dir', 'ch4-1y', 'dpi', dpi)

show_field_v240701(d, 'idx', [6, 10], 'cm', parula(20), ...
    'position',[2, 2, 5, 3],'cmin',0,'cmax',17); 
colorbar
printfig('dir', 'lo-1y', 'dpi', dpi)

show_field_v240701(d, 'idx', [6, 11], 'cm', parula(20), ...
    'position',[2, 2, 5, 3],'cmin',0,'cmax',34); 
colorbar
printfig('dir', 'ho-1y', 'dpi', dpi)

show_field_v240701(d, 'idx', [6, 12], 'cm', parula(20), ...
    'position',[2, 2, 5, 3],'cmin',0,'cmax',41); 
colorbar
printfig('dir', 'kg-1y', 'dpi', dpi)


% 5年
fname = find_file_by_day('cells', 365*4.8);
disp(fname)
d = load(fname);
d=d(1:end-1,:); 

show_field_v240701(d, 'idx', [6, 7], 'cm', parula(20), ...
    'position',[2, 2, 5, 3],'cmin',0,'cmax',15); 
colorbar
printfig('dir', 'ch4-5y', 'dpi', dpi)

show_field_v240701(d, 'idx', [6, 10], 'cm', parula(20), ...
    'position',[2, 2, 5, 3],'cmin',0,'cmax',17); 
colorbar
printfig('dir', 'lo-5y', 'dpi', dpi)

show_field_v240701(d, 'idx', [6, 11], 'cm', parula(20), ...
    'position',[2, 2, 5, 3],'cmin',0,'cmax',34); 
colorbar
printfig('dir', 'ho-5y', 'dpi', dpi)

show_field_v240701(d, 'idx', [6, 12], 'cm', parula(20), ...
    'position',[2, 2, 5, 3],'cmin',0,'cmax',41); 
colorbar
printfig('dir', 'kg-5y', 'dpi', dpi)

% 6年
fname = find_file_by_day('cells', 365*6);
disp(fname)
d = load(fname);
d=d(1:end-1,:); 

show_field_v240701(d, 'idx', [6, 7], 'cm', parula(20), ...
    'position',[2, 2, 5, 3],'cmin',0,'cmax',15); 
colorbar
printfig('dir', 'ch4-6y', 'dpi', dpi)

show_field_v240701(d, 'idx', [6, 10], 'cm', parula(20), ...
    'position',[2, 2, 5, 3],'cmin',0,'cmax',17); 
colorbar
printfig('dir', 'lo-6y', 'dpi', dpi)

show_field_v240701(d, 'idx', [6, 11], 'cm', parula(20), ...
    'position',[2, 2, 5, 3],'cmin',0,'cmax',34); 
colorbar
printfig('dir', 'ho-6y', 'dpi', dpi)

show_field_v240701(d, 'idx', [6, 12], 'cm', parula(20), ...
    'position',[2, 2, 5, 3],'cmin',0,'cmax',41); 
colorbar
printfig('dir', 'kg-6y', 'dpi', dpi)

