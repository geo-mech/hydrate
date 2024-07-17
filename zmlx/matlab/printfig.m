
% ����ǰ��ͼ��ӡ��һ��jepg�ļ���

function printfig(varargin)

% ���������ͼƬ�Ĵ�С
figsize = get_val(varargin, 'size', [0, 0]);
if ~isempty(figsize)
    assert(numel(figsize) >= 2);
    set(gcf, 'PaperPositionMode', 'manual');
    set(gcf, 'PaperUnits', 'centimeters');
    if figsize(1) > 1 && figsize(2) > 1
        set(gcf, 'PaperPosition', [0, 0, figsize(1), figsize(2)]);
    end
end

% ��ӡͼƬ
thedpi = sprintf('-r%d', get_val(varargin, 'dpi', 600));
thedir = get_val(varargin, 'dir', 'fig_print');
assert(ischar(thedir));
print('-djpeg', thedpi, [thedir, '.jpg']);

% ��ѡ��رջ�ͼ��Ĭ�Ϲر�
if ~has_tag(varargin, 'keep')
    close;
end
