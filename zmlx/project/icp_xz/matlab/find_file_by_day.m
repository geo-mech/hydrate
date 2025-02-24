function fname = find_file_by_day(folder, day)
dirs = dir(folder);
for i = 3: 1: length(dirs)
    name = dirs(i).name;
    x = strrep(name, '_', '.');
    y = x(1:length('00000000000000.63521'));
    t = str2double(y);
    if t >= day
        fname = [folder, '/', name];
        break;
    end
end
end
