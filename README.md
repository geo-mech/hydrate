### 介绍

[IGG-Hydrate](https://gitee.com/geomech/hydrate): 天然气水合物开发模拟器。用于：1、天然气水合物[成藏](https://doi.org/10.3390/w16192822)/[开发](https://doi.org/10.1016/j.apenergy.2024.122963)/[碳封存](https://doi.org/10.1021/acs.energyfuels.4c04288); 2、页岩油[原位转化](https://doi.org/10.1016/j.petsci.2024.05.025)；3、其它流动/传热/化学/变形耦合问题.

### 作者

[张召彬](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201703/t20170306_4755492.html)<sup>1,2,*</sup>, [李守定](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201412/t20141218_4278784.html)<sup>1,2</sup>, [李晓](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/200907/t20090713_2065538.html)<sup>1,2</sup>, [赫建明](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201203/t20120302_3448658.html)<sup>1,2</sup>, 李关访<sup>1,2</sup>, [郑博](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/202303/t20230322_6706946.html)<sup>1,2</sup>, 毛天桥<sup>1,2</sup>, 徐涛<sup>1,2</sup>, 李宇轩<sup>1,2</sup>, Maryelin<sup>1,2</sup>, 谢卓然<sup>1,2</sup>

<sup>1</sup>[中国科学院地质与地球物理研究所](https://igg.cas.cn/)(北京, 100029);

<sup>2</sup>[中国科学院大学](https://www.ucas.ac.cn/)(北京, 101408).

<sup>*</sup>联系: [zhangzhaobin@mail.iggcas.ac.cn](zhangzhaobin@mail.iggcas.ac.cn).   (技术问题请[新建Issue](https://gitee.com/geomech/hydrate/issues/new))

### 授权

免费用于学术用途; 使用前请[联系作者](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201703/t20170306_4755492.html). 

### 功能
1. 多相多[组分](https://gitee.com/geomech/hydrate/tree/master/zmlx/fluid)流动，支持: 水/蒸气/水冰，ch4/ch4水合物，co2/co2水合物，盐度/砂，油/重油/干酪根，或其它自定义组分;  
2. [反应](https://gitee.com/geomech/hydrate/tree/master/zmlx/react): 水的蒸发/结冰/融化; ch4水合物形成/分解; co2水合物形成/分解; 干酪根/重油裂解，或其它自定义的反应;
3. 热传导/对流.

### 成果
基于[IGG-Hydrate](https://gitee.com/geomech/hydrate)已发表的文章，请点击[云盘链接](https://pan.cstcloud.cn/s/5cKaQrdFSHM). 

### 运行环境
1. 操作系统: Windows 10/11, 64位; 已安装[VC_redist.x64.exe](https://gitee.com/geomech/hydrate/attach_files);
2. 已正确安装[Python](https://www.python.org/) 3.8+, 64位，且python及[pip](https://www.runoob.com/w3cnote/python-pip-install-usage.html)命令可用; 
3. 已正确安装了[git](https://git-scm.com/). 

### 安装
在正确配置了运行环境之后，可以采用如下方法安装(**任选其一**):
1. **推荐安装方法**，联网并使用[pip](https://www.runoob.com/w3cnote/python-pip-install-usage.html)+[git](https://git-scm.com/)安装. cmd运行如下命令，自动安装[IGG-Hydrate](https://gitee.com/geomech/hydrate)及其依赖项:

    `pip install git+https://gitee.com/geomech/hydrate.git`

2. 若无[git](https://git-scm.com/)，可先手动下载[IGG-Hydrate](https://gitee.com/geomech/hydrate)为`hydrate.zip`。之后，再cmd运行如下命令，也可以安装本模块及依赖项:

    `pip install hydrate.zip` 

3. 若[pip](https://www.runoob.com/w3cnote/python-pip-install-usage.html)不可用，也可手动将下载的zip文件解压到[Python](https://www.python.org/)的搜索路径，并手动安装PyQt6, numpy, scipy, matplotlib等依赖项. 

### 运行

1. 运行 `python -m zml_ui` 可启动[IGG-Hydrate](https://gitee.com/geomech/hydrate)的主界面;
2. 具体的建模方法，可以参考[zmlx/demo](https://gitee.com/geomech/hydrate/tree/master/zmlx/demo). 

### Python集成开发环境

在使用的过程中，需要编辑[Python](https://www.python.org/)代码。建议使用[PyCharm](https://www.jetbrains.com/pycharm/)集成开发环境。

### 反馈

使用过程中遇到问题，请[新建Issue](https://gitee.com/geomech/hydrate/issues/new)来向作者提问或者反馈.

### 开发

1. 非常欢迎并感谢您成为[IGG-Hydrate](https://gitee.com/geomech/hydrate)的开发者。成为开发者之后，可以直接推送或者修改代码，[git](https://git-scm.com/)会记录您的每一个贡献；
2. 如果不想申请成为开发着，也可以使用[Fork + Pull 模式](https://help.gitee.com/base/pullrequest/Fork+Pull)参与开发；
3. 无论采用何种形式，请只修改自己创建的文件(如果在其它文件里发现bug，请[新建Issue](https://gitee.com/geomech/hydrate/issues/new)来反馈)，这样可以有效地避免文件的冲突；
4. 参与开发之前，请[点击此处](https://gitee.com/all-about-git)熟悉[git](https://git-scm.com/)。

### 致谢

1. [中国科学院地质地球所](https://igg.cas.cn/)重点部署项目(IGGCAS-201903);
2. 国家自然科学基金地质联合基金(U2244223).

### 文件说明

1. [zml.py](https://gitee.com/geomech/hydrate/blob/master/zml.py)和zml.dll：计算内核的接口文件以及动态库文件，是整个模块的基础；
2. [zml_ui.pyw](https://gitee.com/geomech/hydrate/blob/master/zml_ui.pyw)：用户界面的入口；
3. [zmlx](https://gitee.com/geomech/hydrate/tree/master/zmlx)：zml内核的扩展，提供进一步的功能；
4. [zmlx/demo](https://gitee.com/geomech/hydrate/tree/master/zmlx/demo)：建模的示例，应是用户使用此模块建模时阅读的起点。

