
function filename = lastfileof(folder, index_from_end)

if nargin <= 1
    index_from_end = 1;
end

dirs = dir(folder);
assert(length(dirs) >= 3, 'can not be empty directory');

if index_from_end <= 1
    filename = fullfile(folder, dirs(end).name);
else
    index_from_end = index_from_end - 1;
    assert(index_from_end >= 1)
    if length(dirs) >= 3 + index_from_end
        filename = fullfile(folder, dirs(end-index_from_end).name);
    else
        filename = fullfile(folder, dirs(3).name);
    end
end
