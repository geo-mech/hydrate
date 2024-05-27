% 在一个cell中，寻找和那么匹配的值，如果找到，则返回true，否则返回false。其
% 中的vals主要为参数列表varargin！！Name是一个字符串

function val = has_tag(vals, name)
assert(ischar(name), 'name should be a string');
val = false;
for i = 1: numel(vals)
    if ~ischar(vals{i})
        continue;
    end
    if strcmp(vals{i}, name)
        val = true;
        return;
    end
end