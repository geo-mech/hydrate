
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
if ~zexist(varargin, 'keep')
    close;
end

% �����������ڲ����б�varargin��Ѱ�Һ�nameƥ���λ�õ���һ��ֵ������valsΪ
% �����б�varargin��nameΪ���ƣ�valΪĬ�ϲ���

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

% ��һ��cell�У�Ѱ�Һ���ôƥ���ֵ������ҵ����򷵻�true�����򷵻�false����
% �е�vals��ҪΪ�����б�varargin����Name��һ���ַ���

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
