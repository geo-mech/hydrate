### 模块简介

[IGG-Hydrate](https://gitee.com/geomech/hydrate):
天然气水合物成藏/开发计算模块。用于：1、天然气水合物[成藏](https://doi.org/10.3390/w16192822)/[开发](https://doi.org/10.1016/j.apenergy.2024.122963)/[碳封存](https://doi.org/10.1021/acs.energyfuels.4c04288);
2、页岩油[原位转化](https://doi.org/10.1016/j.petsci.2024.05.025)；3、其它流动/传热/化学/变形(THMC)耦合问题.

### 作者

[张召彬](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201703/t20170306_4755492.html)<sup>
1,2,*</sup>, [李守定](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201412/t20141218_4278784.html)<sup>
1,2</sup>, [李晓](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/200907/t20090713_2065538.html)<sup>
1,2</sup>, [赫建明](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201203/t20120302_3448658.html)<sup>1,2</sup>,
李关访<sup>1,2</sup>, [郑博](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/202303/t20230322_6706946.html)<sup>1,2</sup>,
毛天桥<sup>1,2</sup>, 徐涛<sup>1,2</sup>, 李宇轩<sup>1,2</sup>, Maryelin<sup>1,2</sup>, 谢卓然<sup>1,2</sup>

<sup>1</sup>[中国科学院地质与地球物理研究所](https://igg.cas.cn/)(北京, 100029);

<sup>2</sup>[中国科学院大学](https://www.ucas.ac.cn/)(北京, 101408).

<sup>*</sup>联系: [zhangzhaobin@mail.iggcas.ac.cn](zhangzhaobin@mail.iggcas.ac.cn).   (
技术问题请[新建Issue](https://gitee.com/geomech/hydrate/issues/new))

### 授权

免费用于学术用途; 使用前请[联系作者](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201703/t20170306_4755492.html).

### 主要功能

1. 多相多[组分](https://gitee.com/geomech/hydrate/tree/master/zmlx/fluid)流动，支持:
   水/蒸气/水冰，ch4/ch4水合物，co2/co2水合物，盐度/砂，油/重油/干酪根，或其它自定义组分;
2. [反应](https://gitee.com/geomech/hydrate/tree/master/zmlx/react): 水的蒸发/结冰/融化; ch4水合物形成/分解;
   co2水合物形成/分解; 干酪根/重油裂解，或其它自定义的反应;
3. 热传导/对流;
4. 应力/应变/振动等.

### 特点

接口完备，可编程性强，方便应用到不同场景.

### 发表的文章

基于[IGG-Hydrate](https://gitee.com/geomech/hydrate)
已发表的文章，请点击[云盘链接](https://pan.cstcloud.cn/s/5cKaQrdFSHM).

### 运行环境

1. Windows 10/11, x64 ([VC_redist.x64.exe](https://gitee.com/geomech/hydrate/attach_files)已安装);
2. [Python](https://www.python.org/) (64位, 3.8+).

### 安装

推荐使用[git](https://git-scm.com/)+[pip](https://pypi.org/project/pip/)来安装/更新：

`pip install git+https://gitee.com/geomech/hydrate.git`

#### 注：
若[git](https://git-scm.com/)或者[pip](https://pypi.org/project/pip/)不可用，可手动安装`PyQt6, numpy, scipy, matplotlib, pyqtgraph, PyOpenGL`等依赖项，
并将下载解压的[IGG-Hydrate](https://gitee.com/geomech/hydrate)添加到Python搜索路径. 

### 建模

1. 参考[`zmlx/demo`](https://gitee.com/geomech/hydrate/tree/master/zmlx/demo)建模;
2. 运行[`zml_ui.pyw`](https://gitee.com/geomech/hydrate/blob/master/zml_ui.pyw)打开界面.

### 问题反馈

安装/使用过程中遇到问题，请[新建Issue](https://gitee.com/geomech/hydrate/issues/new)来提问/反馈.

### 参与研发

1. 非常欢迎并感谢您成为[IGG-Hydrate](https://gitee.com/geomech/hydrate)的开发者, [git](https://git-scm.com/)会记录您的每一个贡献;
2. 请只修改自己创建的文件(以避免冲突);
3. 请务必熟悉[git](https://git-scm.com/).
