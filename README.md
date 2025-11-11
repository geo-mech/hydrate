### 简介

[**IGG-Hydrate**](https://gitee.com/geomech/hydrate): 天然气水合物成藏/开发计算模块。用于：1、天然气水合物[成藏](https://doi.org/10.3390/w16192822)/[开发](https://doi.org/10.1016/j.apenergy.2024.122963)/[碳封存](https://doi.org/10.1021/acs.energyfuels.4c04288); 2、页岩油[原位转化](https://doi.org/10.1016/j.petsci.2024.05.025)；3、其它流动/传热/化学/变形(THMC)耦合问题.

### 作者

[张召彬](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201703/t20170306_4755492.html)<sup>1,2,x</sup>, [李守定](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201412/t20141218_4278784.html)<sup>1,2</sup>, [李晓](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/200907/t20090713_2065538.html)<sup>1,2</sup>, [赫建明](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201203/t20120302_3448658.html)<sup>1,2</sup>, 李关访<sup>1,2</sup>, [郑博](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/202303/t20230322_6706946.html)<sup>1,2</sup>, 毛天桥<sup>1,2</sup>, 徐涛<sup>1,2</sup>, 李宇轩<sup>1,2</sup>, Maryelin<sup>1,2</sup>, 谢卓然<sup>1,2</sup>

<sup>1</sup>[中国科学院地质与地球物理研究所](https://igg.cas.cn/)(北京, 100029);

<sup>2</sup>[中国科学院大学](https://www.ucas.ac.cn/)(北京, 101408).

<sup>x</sup>
联系人: [张召彬](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201703/t20170306_4755492.html), 邮箱: [zhangzhaobin@mail.iggcas.ac.cn](zhangzhaobin@mail.iggcas.ac.cn); [或添加**微信**](https://gitee.com/geomech/hydrate/issues/ID5HZX).   

### 反馈

技术问题建议[**新建Issue**](https://gitee.com/geomech/hydrate/issues/new)，另外，也欢迎[添加**微信**](https://gitee.com/geomech/hydrate/issues/ID5HZX). 

### 授权

使用前请[联系作者](https://gitee.com/geomech/hydrate/issues/ID5HZX)。

### 反馈

使用过程中遇到问题，请[新建Issue](https://gitee.com/geomech/hydrate/issues/new)或者[联系作者](https://gitee.com/geomech/hydrate/issues/ID5HZX)来提问/反馈。非常感谢您[提出质疑及反馈bug](https://gitee.com/geomech/hydrate/issues/new)！

### 功能

1. 多相多组分流动，支持: 水/蒸气/水冰，ch4/ch4水合物，co2/co2水合物，盐度/砂，油/重油/干酪根，或其它自定义组分;
2. 反应: 水的蒸发/结冰/融化; ch4水合物形成/分解; co2水合物形成/分解; 干酪根/重油裂解，或其它自定义的反应;
3. 热传导/对流;
4. 应力/应变/振动等静力学和动力学过程.

### 特点

1. 接口完备，可编程，方便应用到不同场景;
2. 支持任意多个相，每个相支持任意多组分，每个组分支持多个属性.

### 环境

1. Windows 10/11, x64; 需安装[VC_redist.x64.exe](https://gitee.com/geomech/hydrate/attach_files) (程序必要的运行的环境);
2. 建议安装[git](https://git-scm.com/)：官方下载，默认安装即可（默认安装的时候会添加文件夹的右键菜单，可以取消勾选；git安装之后，建议安装辅助工具[TortoiseGit](https://tortoisegit.org/)，会添加更加好用的右键菜单）;
3. 安装[Python](https://www.python.org/) (64位, 3.8+, 推荐3.10及更新的版本)，推荐使用[WinPython](https://gitee.com/geomech/hydrate/attach_files) (绿色免安装); 
4. 推荐提前安装好`PyQt6(不再支持PyQt5), PyQt6-WebEngine, pyqt6-qscintilla, numpy, scipy, matplotlib, pyqtgraph, PyOpenGL, pypiwin32, pywin32, dulwich`等第三方的Python包. 

注：如有在Linux上运行的需求，请联系作者. 

### 安装

1. 作为用户，如果只是单纯使用，可[cmd](https://blog.csdn.net/qq_43546721/article/details/131536857)执行如下命令来安装(可自动处理Python的依赖项)：`python -m pip install git+https://gitee.com/geomech/hydrate.git`.
注意：如果python.exe不在[PATH](https://blog.csdn.net/flame_007/article/details/106401215)中，可以先[cd](https://blog.csdn.net/zdy219727/article/details/98605287)到python.exe所在的目录，再执行上述命令.
2. 如果要参与开发，或者希望更加清晰地看到源代码，请使用[git](https://git-scm.com/)将代码[clone到本地](https://gitee.com/help/articles/4111#article-header0)，并添加到Python的搜索路径。

### 建模

1. 参考[`zmlx/demo`](https://gitee.com/geomech/hydrate/tree/master/zmlx/demo)建模 (在此基础上，推荐向前追溯函数的实现);
2. 运行[`zml_ui.pyw`](https://gitee.com/geomech/hydrate/blob/master/zml_ui.pyw)打开界面.

### 编程环境 (IDE)

推荐使用[PyCharm](https://www.jetbrains.com/pycharm)集成开发环境([官网下载PyCharm Community Edition](https://www.jetbrains.com/pycharm/download)默认安装即可)，之后，推荐安装 [Trae AI](https://www.trae.com.cn/)插件 (在PyCharm的插件管理中搜索下载)，其中集成了DeepSeek等AI工具，使用友好。

### 开发

欢迎并感谢您成为[IGG-Hydrate](https://gitee.com/geomech/hydrate)的开发者：

1. 请只修改自己创建的文件(以避免冲突);
2. 请务必熟悉[git](https://git-scm.com/)，在[Gitee帮助中心](https://gitee.com/help#article-header0)有不少git的入门资料；新手建议安装[TortoiseGit](https://tortoisegit.org/)，它会在文件管理器添加右键菜单，可以满足大部分操作;
3. 如果直接向[IGG-Hydrate](https://gitee.com/geomech/hydrate)推送代码，可能会报错（因为没有权限）；此时，可以在页面右上角，点击[申请加入仓库](https://gitee.com/geomech/hydrate)，成为开发者；或者，你也可以使用[Fork + Pull 模式](https://help.gitee.com/base/pullrequest/Fork+Pull)参与开发（这也是[Gitee](https://gitee.com/)推荐的方式）。
