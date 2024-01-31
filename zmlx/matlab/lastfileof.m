
function y = lastfileof(path, NumberLast)

y = dir(path);
assert(length(y) >= 3, 'can not be empty directory');
assert(nargin == 1 || nargin == 2);
if nargin == 1
    y = [path, '\', y(end).name];
else
    if length(y) >= 3 + NumberLast
        y = [path, '\',y(end-NumberLast).name];
    else
        y = [path, '\',y(3).name];
    end
end


