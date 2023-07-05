#### 介绍

储层多场耦合计算模块 ([_IggHydrate_](https://gitee.com/geomech/hydrate))

@[中科院地质地球所](http://www.igg.cas.cn/).

#### 作者

[张召彬](http://sourcedb.igg.cas.cn/cn/zjrck/201703/t20170306_4755492.html)，[李守定](http://sourcedb.igg.cas.cn/cn/zjrck/201412/t20141218_4278784.html)，[赫建明](http://sourcedb.igg.cas.cn/cn/zjrck/201203/t20120302_3448658.html)，[李晓](http://sourcedb.igg.cas.cn/cn/zjrck/200907/t20090713_2065538.html)，徐涛，李宇轩，Maryelin

#### 版本

ZmlVersion=230705

#### 网址

https://gitee.com/geomech/hydrate 

#### 功能

1) 多相多组分流动.
2) 热传导.
3) 扩散.
4) 化学反应.
5) 应力.
6) 裂缝扩展.

#### 特点

1) 支持结构/非结构网格;
2) 支持任意多相流动，且任意相都支持多组分;
3) 流体/组分支持自定义属性(如温度、颗粒浓度等)，且属性会随着流动输运;
4) 支持利用数据来自定义流体(无需公式);
5) 支持组分之间的化学反应;
6) 提供底层API，可以对单元，流体，组分进行精细化读/写操作;
7) 作为[Python](https://www.python.org/)模块可被第三方软件调用; 

#### 联系

如遇bug、疑问或建议，以及建模需求，请在[Issues页面](https://gitee.com/geomech/hydrate/issues)，[新建Issue](https://gitee.com/geomech/hydrate/issues/new)，或[联系作者](http://sourcedb.igg.cas.cn/cn/zjrck/201703/t20170306_4755492.html). 

#### 运行环境

1) 安装[Python](https://www.python.org/) 3.7及以上版本. 建议安装[WinPython](https://winpython.github.io/).   
2) 安装[VC_redist.x64.exe](https://gitee.com/geomech/hydrate/attach_files).
3) 为方便下载、更新及提交代码，建议[注册Gitee账号](https://gitee.com/signup)并安装配置[Git](https://git-scm.com/). 

#### 安装

1) 从[https://gitee.com/geomech/hydrate](https://gitee.com/geomech/hydrate)下载或拉取代码 <注意不要存入中文路径>.
2) 把下载后的文件夹添加到Python搜索路径. 

#### 更新

1) [下载](https://gitee.com/geomech/hydrate)或[拉取](https://gitee.com/geomech/hydrate.git)代码并覆盖原文件即完成更新. 
2) 请每个月至少更新一次. 

#### 使用
1) 所有功能均封装在模块`zml`和`zmlx`里，可在 [Python](https://www.python.org/) 3.7+环境中`import`. 
2) 运行`UI.pyw`可启动软件界面.
3) 参考[zmlx/demo](https://gitee.com/geomech/hydrate/tree/master/zmlx/demo)中的例子来建模，如有需求请[咨询作者](http://sourcedb.igg.cas.cn/cn/zjrck/201703/t20170306_4755492.html). 

#### 授权

[联系作者](http://sourcedb.igg.cas.cn/cn/zjrck/201703/t20170306_4755492.html)以使用，并承诺：
1) 使用[最新版](https://gitee.com/geomech/hydrate). 
2) 及时[报告bug](https://gitee.com/geomech/hydrate/issues/new).

#### 开发者

欢迎/感谢成为*开发者*，请注意:

1) <font color="#FF0000">只</font>修改文件夹 [zmlx](https://gitee.com/geomech/hydrate/tree/master/zmlx) 里面的内容；
2) <font color="#FF0000">只</font>修改<font color="#FF0000">自己</font>创建的文件; 非自己创建的文件的bug，请[新建Issue](https://gitee.com/geomech/hydrate/issues/new)来反馈;



