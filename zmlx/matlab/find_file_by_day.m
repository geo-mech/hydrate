function fname = find_file_by_day(folder, day)

fname = '';
dt = 1.0e100;

dirs = dir(folder);
for i = 1: length(dirs)
    name = dirs(i).name;
    if ~strcmp(name, '.') && ~strcmp(name, '..')
        try
            x = strrep(name, '_', '.');
            y = x(1:length('00000000000000.63521'));
            t = str2double(y);
            if abs(t - day) < dt   % 找到最为接近的
                dt = abs(t - day);
                fname = [folder, '/', name];
            end
        catch exception
            % 捕获异常后执行的代码
            fprintf('An error occurred: %s\n', exception.message);
        end
    end
end
end
