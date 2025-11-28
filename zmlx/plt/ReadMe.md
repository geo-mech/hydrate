### 简介

用于Matplotlib绘图的代码集合。

### 格式

为了使得绘图的代码可以在不同的位置显示，对于绘图函数，后续，应该逐步做成如下的形式：

contour.py:
on_axes(ax, *args, **kwargs):       在ax上绘图
on_figure(figure, *args, **kwargs): 在figure上绘图

