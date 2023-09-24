### 介绍

[IggHydrate](https://gitee.com/geomech/hydrate): 储层及样品尺度水合物形成/分解计算模块. @[中科院地质地球所(Iggcas)](http://www.igg.cas.cn/)

### 主要功能

多相多组分渗流；反应；热传导/对流；扩散；应力/变形. 

### 特点

1) 支持任意多相态、组分、反应；且单元和流体均支持自定义属性;
2) 基于数据定义流体、反应，不需要公式;
3) 支持[Python](https://www.python.org/)二次开发，并提供单元、流体、组分、反应、流程控制等底层API;
4) 支持结构/非结构网格; 支持一维/二维/三维计算; 
5) 支持水合物、页岩油气、干热岩等流动/传热/反应耦合问题;
 
### 版本

ZmlVersion=230924

### 联系

如遇bug、疑问或建议，以及建模需求，请[联系作者](http://sourcedb.igg.cas.cn/cn/zjrck/201703/t20170306_4755492.html).

### 使用

#### Python配置(Windows系统): 
1) 安装[Python](https://www.python.org/) 3.7及以上版本，并安装numpy, scipy, PyQt5, matplotlib等第三方模块; 建议使用[WinPython](https://winpython.github.io/)(方便管理第三方模块). 
2) 安装[VC_redist.x64.exe](https://gitee.com/geomech/hydrate/attach_files);
3) 如需要Linux版本，请[联系作者](http://sourcedb.igg.cas.cn/cn/zjrck/201703/t20170306_4755492.html).

#### 拉取/下载代码：

1) [注册Gitee账号](https://gitee.com/signup)并安装配置[Git](https://git-scm.com/);
2) 从[https://gitee.com/geomech/hydrate](https://gitee.com/geomech/hydrate)拉取或者下载代码;
3) 将`zml.py`所在文件夹添加到Python搜索路径(运行`UI.pyw`可自动执行该操作).

#### 建模：

1) 所有功能均封装在模块`zml`和`zmlx`里，可在 [Python](https://www.python.org/) 3.7+环境中`import`来使用；
2) 参考[zmlx/demo](https://gitee.com/geomech/hydrate/tree/master/zmlx/demo)
   中的例子来建模，有问题请[咨询作者](http://sourcedb.igg.cas.cn/cn/zjrck/201703/t20170306_4755492.html).

### 授权

免费用于非商业用途。使用前请[联系作者](http://sourcedb.igg.cas.cn/cn/zjrck/201703/t20170306_4755492.html)，并承诺：

1) 帮助改进程序，并[报告bug](https://gitee.com/geomech/hydrate/issues/new);
2) 使用[最新版](https://gitee.com/geomech/hydrate)(每月请至少更新一次). 

### 成为开发者

欢迎并感谢您成为开发者。请注意:

1) 请使用Gitee推荐的[Fork + Pull 模式](https://help.gitee.com/base/pullrequest/Fork+Pull)参与开发；
2) 只修改[zmlx](https://gitee.com/geomech/hydrate/tree/master/zmlx)文件夹里面的内容；
3) 只修改自己创建的文件; 如果在其它文件里发现bug，请[新建Issue](https://gitee.com/geomech/hydrate/issues/new)来反馈;
