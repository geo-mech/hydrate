### 介绍

[IGG-Hydrate](https://gitee.com/geomech/hydrate): 储层*热/流/固/化耦合*(THMC)计算模块@[IGG](http://www.igg.cas.cn/)
 
### 版本

ZmlVersion=240121

### 用途

1. 天然气水合物储层成藏/开发;
2. 重油原位转化;

### 功能
1. 多相多组分流动，支持: 水/蒸气/水冰，ch4/ch4水合物，co2/co2水合物，盐度/砂，油/重油/干酪根;  
2. 反应: 水的蒸发/结冰/融化; ch4水合物形成/分解; co2水合物形成/分解; 干酪根/重油裂解;
3. 热传导/对流;

### 授权

使用前请[联系作者](http://sourcedb.igg.cas.cn/cn/zjrck/201703/t20170306_4755492.html).

### 联系

zhangzhaobin@mail.iggcas.ac.cn;

### 安装

1. Windows 10/11, x64, 安装[VC_redist.x64.exe](https://gitee.com/geomech/hydrate/attach_files);
2. 安装[Python](https://www.python.org/) 3.7+，并配置`numpy`, `scipy`, `PyQt5`, `matplotlib`;
3. 将`zml.py`所在文件夹添加到Python[搜索路径](https://zhuanlan.zhihu.com/p/530589364);

### 使用

1. 参考[zmlx/demo](https://gitee.com/geomech/hydrate/tree/master/zmlx/demo);
2. 运行`UI.pyw`启动界面;

### 开发

1. 使用[Fork + Pull 模式](https://help.gitee.com/base/pullrequest/Fork+Pull)参与开发;
2. 只修改自己创建的文件(如果在其它文件里发现bug，请[新建Issue](https://gitee.com/geomech/hydrate/issues/new)来反馈).
