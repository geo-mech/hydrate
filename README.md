### 介绍

[Hydrate](https://gitee.com/geomech/hydrate): 储层及样品尺度水合物形成/分解计算模块.

### 主要功能

多相多组分渗流；反应；传热；扩散；应力/变形. 

### 特点

1. 支持任意多种流体和反应;
2. 基于数据插值来定义流体和反应，不需要公式;
3. 支持[Python](https://www.python.org/)二次开发，并提供单元、流体、组分、反应、流程控制等底层API;
4. 支持结构/非结构网格.
 
### 版本

ZmlVersion=231007

### 联系

zhangzhaobin@mail.iggcas.ac.cn

### 运行环境

1. Windows 7/10/11, x64, 安装[VC_redist.x64.exe](https://gitee.com/geomech/hydrate/attach_files);
2. [Python](https://www.python.org/) 3.7+, 安装numpy, scipy, PyQt5, matplotlib.

### 使用

1. [下载代码](https://gitee.com/geomech/hydrate);
2. 将`zml.py`所在文件夹添加到Python[搜索路径](https://zhuanlan.zhihu.com/p/530589364);
3. 用[Python](https://www.python.org/)打开`UI.pyw`以启动主界面;
4. 参考[zmlx/demo](https://gitee.com/geomech/hydrate/tree/master/zmlx/demo)来建模. 

### 授权

使用前请[联系作者](http://sourcedb.igg.cas.cn/cn/zjrck/201703/t20170306_4755492.html)，并承诺：

1. 帮助改进程序，并[报告bug](https://gitee.com/geomech/hydrate/issues/new);
2. 使用[最新版](https://gitee.com/geomech/hydrate)(每月请至少更新一次). 

### 成为开发者

1. 使用[Fork + Pull 模式](https://help.gitee.com/base/pullrequest/Fork+Pull)参与开发;
2. 只修改自己创建的文件(如果在其它文件里发现bug，请[新建Issue](https://gitee.com/geomech/hydrate/issues/new)来反馈).
