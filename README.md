### 介绍

[IGG-Hydrate](https://gitee.com/geomech/hydrate): 天然气水合物成藏/开发计算模块。用于：1、天然气水合物[成藏](https://doi.org/10.3390/w16192822)/[开发](https://doi.org/10.1016/j.apenergy.2024.122963)/[碳封存](https://doi.org/10.1021/acs.energyfuels.4c04288); 2、页岩油[原位转化](https://doi.org/10.1016/j.petsci.2024.05.025)；3、其它流动/传热/化学/变形(THMC)耦合问题.

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
3. 热传导/对流;
4. 应力/应变/振动等. 

### 特点

接口完备，可编程性强，方便扩展到(也已成功用到)不同的场景. 

### 成果
基于[IGG-Hydrate](https://gitee.com/geomech/hydrate)已发表的文章，请点击[云盘链接](https://pan.cstcloud.cn/s/5cKaQrdFSHM). 

### 系统
Windows 10/11, 64位. 

### 安装
以下方法，_任选其一_:
1. 下载作者打包的[便携版Python环境](https://pan.cstcloud.cn/s/sQu05gziTx0); 
2. 安装[Python](https://www.python.org/) (64位, 3.8+)和[git](https://git-scm.com/), 运行命令: `pip install git+https://gitee.com/geomech/hydrate.git`.

### 使用

参考[zmlx/demo](https://gitee.com/geomech/hydrate/tree/master/zmlx/demo). 

### 反馈

安装/使用过程中遇到问题，请[新建Issue](https://gitee.com/geomech/hydrate/issues/new)来提问/反馈.

### 开发

1. 非常欢迎并感谢您成为[IGG-Hydrate](https://gitee.com/geomech/hydrate)的开发者, [git](https://git-scm.com/)会记录您的每一个贡献;
2. 请只修改自己创建的文件(可避免冲突);
3. 请务必熟悉[git](https://git-scm.com/);
