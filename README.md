### 简介

[**IGG-Hydrate**](https://gitee.com/geomech/hydrate): 天然气水合物成藏/开发计算模块。用于：1、天然气水合物[成藏](https://doi.org/10.3390/w16192822)/[开发](https://doi.org/10.1016/j.apenergy.2024.122963)/[碳封存](https://doi.org/10.1021/acs.energyfuels.4c04288); 2、页岩油[原位转化](https://doi.org/10.1016/j.petsci.2024.05.025)；3、其他流动/传热/化学/变形(THMC)耦合问题.

### 作者

[张召彬](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201703/t20170306_4755492.html)<sup>1,2,x</sup>, [李守定](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201412/t20141218_4278784.html)<sup>1,2</sup>, [李晓](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/200907/t20090713_2065538.html)<sup>1,2</sup>, 徐涛<sup>1,2</sup>, 李宇轩<sup>1,2</sup>, Maryelin<sup>1,2</sup>, 谢卓然<sup>1,2</sup>

<sup>1</sup>[中国科学院地质与地球物理研究所](https://igg.cas.cn/)(北京, 100029);

<sup>2</sup>[中国科学院大学](https://www.ucas.ac.cn/)(北京, 101408).

<sup>x</sup>
联系人: [张召彬](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201703/t20170306_4755492.html), 邮箱: [zhangzhaobin@mail.iggcas.ac.cn](zhangzhaobin@mail.iggcas.ac.cn); [或添加**微信**](https://gitee.com/geomech/hydrate/issues/ID5HZX).   

### 反馈

技术问题请[**新建Issue**](https://gitee.com/geomech/hydrate/issues/new)，*软件授权*及其他问题请[联系作者](https://gitee.com/geomech/hydrate/issues/ID5HZX).

### 功能

1. 多相多组分流动，支持: 水/蒸气/水冰，ch4/ch4水合物，co2/co2水合物，盐度/砂，油/重油/干酪根，或其它自定义组分; 支持同时计算任意多个相，每个相支持任意多组分.
2. 反应: 水的蒸发/结冰/融化; ch4水合物形成/分解; co2水合物形成/分解; 干酪根/重油裂解，或其它自定义的反应;
3. 热传导/对流;
4. 应力/应变/振动等静力学和动力学过程.

### 特点

1. 接口完备，可编程，方便应用到不同场景;
2. 支持任意多个相，每个相支持任意多组分，每个组分支持多个属性.

### 安装
1. 确保系统为Windows 10/11, x64;  如有在Linux上运行的需求，请联系作者; 
2. 安装[Python](https://www.python.org/) (64位, 3.8+, 推荐3.10及更新的版本); 推荐[WinPython](https://gitee.com/geomech/hydrate/attach_files) (绿色免安装); 
3. 安装`PyQt6, PyQt6-WebEngine, pyqt6-qscintilla, numpy, scipy, matplotlib, pyqtgraph, PyOpenGL, pypiwin32, pywin32, dulwich`等第三方的Python包; 
4. [下载](https://gitee.com/geomech/hydrate)zip并解压，或者使用[git](https://git-scm.com/)来[clone](https://gitee.com/help/articles/4111#article-header0)代码(务必存储到纯英文路径下);
5. 将`zmlx`所在的文件夹添加到Python的搜索路径中，确保`zmlx`可以被Python导入. 
6. 参考[`zmlx/demo`](https://gitee.com/geomech/hydrate/tree/master/zmlx/demo)建模; 运行[`zml_ui.pyw`](https://gitee.com/geomech/hydrate/blob/master/zml_ui.pyw)打开界面.

### 开发

欢迎并感谢您成为[IGG-Hydrate](https://gitee.com/geomech/hydrate)的开发者：

1. 请只修改自己创建的文件(以避免冲突);
2. 请务必熟悉[git](https://git-scm.com/)，在[Gitee帮助中心](https://gitee.com/help#article-header0)有不少git的入门资料；新手建议安装[TortoiseGit](https://tortoisegit.org/)，它会在文件管理器添加右键菜单，可以满足大部分操作;
3. 如果直接向[IGG-Hydrate](https://gitee.com/geomech/hydrate)推送代码，可能会报错（因为没有权限）。此时，可以在页面右上角，点击[申请加入仓库](https://gitee.com/geomech/hydrate)，成为开发者；或者，你也可以使用[Fork + Pull 模式](https://help.gitee.com/base/pullrequest/Fork+Pull)参与开发。
