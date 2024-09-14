### 介绍

[IGG-Hydrate](https://gitee.com/geomech/hydrate): 天然气水合物开发模拟器。用于：1、天然气水合物成藏/开发; 2、页岩油原位转化；3、其它流动/传热/化学耦合问题。

### 作者

[张召彬](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201703/t20170306_4755492.html)<sup>1,2,3,*</sup>, [李守定](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201412/t20141218_4278784.html)<sup>1,2,3</sup>, [李晓](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/200907/t20090713_2065538.html)<sup>1,2,3</sup>, [赫建明](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201203/t20120302_3448658.html)<sup>1,2,3</sup>, 李关访<sup>1,2,3</sup>, [郑博](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/202303/t20230322_6706946.html)<sup>1,2,3</sup>, 毛天桥<sup>1,2,3</sup>, 徐涛<sup>1,2,3</sup>, 李宇轩<sup>1,2,3</sup>, Maryelin<sup>1,2,3</sup>, 谢卓然<sup>1,2,3</sup>


<sup>1</sup>[中国科学院地质与地球物理研究所](https://igg.cas.cn/)(北京, 100029);

<sup>2</sup>中国科学院地球科学研究院(北京, 100029);

<sup>3</sup>[中国科学院大学](https://www.ucas.ac.cn/)(北京, 101408).

<sup>*</sup>联系: [zhangzhaobin@mail.iggcas.ac.cn](zhangzhaobin@mail.iggcas.ac.cn)

### 授权

免费用于学术用途；使用前请[联系作者](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201703/t20170306_4755492.html).

### 功能
1. 多相多[组分](https://gitee.com/geomech/hydrate/tree/master/zmlx/fluid)流动，支持: 水/蒸气/水冰，ch4/ch4水合物，co2/co2水合物，盐度/砂，油/重油/干酪根;  
2. [反应](https://gitee.com/geomech/hydrate/tree/master/zmlx/react): 水的蒸发/结冰/融化; ch4水合物形成/分解; co2水合物形成/分解; 干酪根/重油裂解;
3. 热传导/对流;

### 安装

1. Windows 10/11, x64, 安装[VC_redist.x64.exe](https://gitee.com/geomech/hydrate/attach_files);
2. 安装[Python](https://www.python.org/) 3.7+ (x64); 
3. 将[zml.py](https://gitee.com/geomech/hydrate/blob/master/zml.py)所在文件夹添加到Python[搜索路径](https://zhuanlan.zhihu.com/p/530589364);
4. 命令行运行`python.exe -m zml env`来安装 [IGG-Hydrate](https://gitee.com/geomech/hydrate) 依赖的Python模块(包括：`numpy, scipy, PyQt5, matplotlib, pyqtgraph, PyOpenGL, PyQtWebEngine`等). 

### 使用

1. 参考[zmlx/demo](https://gitee.com/geomech/hydrate/tree/master/zmlx/demo);
2. 运行[UI.pyw](https://gitee.com/geomech/hydrate/blob/master/UI.pyw)启动界面.

### 反馈

使用过程中遇到问题，请[新建Issue](https://gitee.com/geomech/hydrate/issues/new)来向作者提问或者反馈。

### 开发
欢迎并感谢您成为开发者并推送代码：
1. 使用[Fork + Pull 模式](https://help.gitee.com/base/pullrequest/Fork+Pull)参与开发;
2. 只修改自己创建的文件(如果在其它文件里发现bug，请[新建Issue](https://gitee.com/geomech/hydrate/issues/new)来反馈).

### 致谢

1. 中国科学院地质地球所重点部署项目(IGGCAS-201903);
2. 国家自然科学基金地质联合基金(U2244223);


