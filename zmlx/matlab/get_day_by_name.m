function day = get_day_by_name(name)

count = length('00000000007061_45085');
key = name(1: count);
key = replace(key, '_', '.');
day = str2double(key);

