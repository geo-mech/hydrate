
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
if ~has_tag(varargin, 'keep')
    close;
end
