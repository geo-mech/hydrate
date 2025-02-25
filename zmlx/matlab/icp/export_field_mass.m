
folder = 'cells';
dirs = dir(folder);
result = [];
for i = 3: 1: length(dirs)
    name = dirs(i).name;
    count = length('00000000007061_45085');
    disp(name);
    key = name(1: count);
    key = replace(key, '_', '.');
    day = str2double(key);
    data = load(fullfile(folder, name));
    % 去除掉虚拟单元
    data = data(abs(data(:, 3)) < 100, :);
    vm = [day / 365];
    for icol = 7: 13
        m = data(:, 6) .* data(:, icol);
        m = sum(m);
        vm(end+1) = m;
    end
    result(end+1, :) = vm;
end

save('field_mass.txt', "result", '-ascii')
