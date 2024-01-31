
% 将当前绘图打印到一个jepg文件中

function printfig(varargin)

% 设置输出的图片的大小
figsize = get_val(varargin, 'size', [0, 0]);
if ~isempty(figsize)
    assert(numel(figsize) >= 2);
    set(gcf, 'PaperPositionMode', 'manual');
    set(gcf, 'PaperUnits', 'centimeters');
    if figsize(1) > 1 && figsize(2) > 1
        set(gcf, 'PaperPosition', [0, 0, figsize(1), figsize(2)]);
    end
end

% 打印图片
thedpi = sprintf('-r%d', get_val(varargin, 'dpi', 600));
thedir = get_val(varargin, 'dir', 'fig_print');
assert(ischar(thedir));
print('-djpeg', thedpi, [thedir, '.jpg']);

% 可选择关闭绘图，默认关闭
if ~zexist(varargin, 'keep')
    close;
end

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

% 在一个cell中，寻找和那么匹配的值，如果找到，则返回true，否则返回false。其
% 中的vals主要为参数列表varargin！！Name是一个字符串

function val = zexist(vals, name)
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
