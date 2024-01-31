% 辅助函数，在参数列表varargin中寻找和name匹配的位置的下一个值！其中vals为
% 参数列表varargin，name为名称，val为默认参数

function val = get_val(vals, name, val)
assert(ischar(name), 'name should be a string');
if nargin < 3
    val = [];
end
for i = 1: numel(vals) - 1
    if ~ischar(vals{i})
        continue;
    end
    if strcmp(vals{i}, name)
        val = vals{i+1};
        return;
    end
end