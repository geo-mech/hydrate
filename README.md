### 介绍

[IGG-Hydrate](https://gitee.com/geomech/hydrate): 非常规储层*热/流/固/化耦合*(THMC)计算模块. 用于：1、天然气水合物储层成藏/开发; 2、陆相页岩原位转化开发；3、其它流动/传热/化学耦合问题。
 
### 版本

ZmlVersion=240402

### 作者

[张召彬](http://sourcedb.igg.cas.cn/cn/zjrck/201703/t20170306_4755492.html)<sup>1,2,3,*</sup>, [李守定](http://sourcedb.igg.cas.cn/cn/zjrck/201412/t20141218_4278784.html)<sup>1,2,3</sup>, [李晓](http://sourcedb.igg.cas.cn/cn/zjrck/200907/t20090713_2065538.html)<sup>1,2,3</sup>, [赫建明](http://sourcedb.igg.cas.cn/cn/zjrck/201203/t20120302_3448658.html)<sup>1,2,3</sup>, 李关访<sup>1,2,3</sup>, [郑博](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/202303/t20230322_6706946.html)<sup>1,2,3</sup>, 毛天桥<sup>1,2,3</sup>, 徐涛<sup>1,2,3</sup>, 李宇轩<sup>1,2,3</sup>, Maryelin<sup>1,2,3</sup>, 谢卓然<sup>1,2,3</sup>

---

<sup>1</sup>[中国科学院地质与地球物理研究所](https://igg.cas.cn/)(北京, 100029);

<sup>2</sup>中国科学院地球科学研究院(北京, 100029);

<sup>3</sup>中国科学院大学(北京, 100029).

<sup>*</sup>联系: [zhangzhaobin@mail.iggcas.ac.cn](zhangzhaobin@mail.iggcas.ac.cn)

### 授权

使用前请[联系作者](http://sourcedb.igg.cas.cn/cn/zjrck/201703/t20170306_4755492.html).

### 功能
1. 多相多组分流动，支持: 水/蒸气/水冰，ch4/ch4水合物，co2/co2水合物，盐度/砂，油/重油/干酪根;  
2. 反应: 水的蒸发/结冰/融化; ch4水合物形成/分解; co2水合物形成/分解; 干酪根/重油裂解;
3. 热传导/对流;

### 安装

1. Windows 10/11, x64, 安装[VC_redist.x64.exe](https://gitee.com/geomech/hydrate/attach_files);
2. 安装[Python](https://www.python.org/) 3.7+，并配置`numpy`, `scipy`, `PyQt5`, `matplotlib`; 建议安装 [WinPython](https://pan.baidu.com/s/1PnqdA28GdUKhA9A_7x20zQ) 集成环境 (链接：[https://pan.baidu.com/s/1PnqdA28GdUKhA9A_7x20zQ](https://pan.baidu.com/s/1PnqdA28GdUKhA9A_7x20zQ), 提取码：mba8);
3. 将`zml.py`所在文件夹添加到Python[搜索路径](https://zhuanlan.zhihu.com/p/530589364);

### 使用

1. 参考[zmlx/demo](https://gitee.com/geomech/hydrate/tree/master/zmlx/demo);
2. 运行`UI.pyw`启动界面 (会尝试将`zml`添加到[搜索路径](https://zhuanlan.zhihu.com/p/530589364));
3. 发现问题或者有其它建模需求，请[联系作者](http://sourcedb.igg.cas.cn/cn/zjrck/201703/t20170306_4755492.html);

### 开发
欢迎并感谢您成为开发者并推送代码：
1. 使用[Fork + Pull 模式](https://help.gitee.com/base/pullrequest/Fork+Pull)参与开发;
2. 只修改自己创建的文件(如果在其它文件里发现bug，请[新建Issue](https://gitee.com/geomech/hydrate/issues/new)来反馈).
