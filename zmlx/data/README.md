### 简介

[**IGG-Hydrate**](https://gitee.com/geomech/hydrate): 储层多场耦合计算模块。
用于：
1、天然气水合物[成藏](https://doi.org/10.3390/w16192822)/[开发](https://doi.org/10.1016/j.apenergy.2024.122963)/[碳封存](https://doi.org/10.1016/j.fuel.2025.137599);
2、页岩油[原位转化](https://doi.org/10.1016/j.petsci.2024.05.025)；
3、储层内的其他流动/传热/化学/变形(THMC)耦合问题.

### 作者

[张召彬](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201703/t20170306_4755492.html)<sup>
1,2,x</sup>, [李守定](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201412/t20141218_4278784.html)<sup>
1,2</sup>, 李晓<sup>1,2</sup>, 徐涛<sup>
1,2</sup>, 李宇轩<sup>1,2</sup>, Maryelin Josefina Briceño Montilla<sup>1,2</sup>, 谢卓然<sup>1,2</sup>, 李晓旗<sup>1,2</sup>, 张韬<sup>1,2</sup>

<sup>1</sup>[中国科学院地质与地球物理研究所](https://igg.cas.cn/)(北京, 100029);

<sup>2</sup>[中国科学院大学](https://www.ucas.ac.cn/)(北京, 101408).

<sup>x</sup>
联系人: [张召彬](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201703/t20170306_4755492.html),
邮箱: [zhangzhaobin@mail.iggcas.ac.cn](mailto:zhangzhaobin@mail.iggcas.ac.cn);
或添加[微信](https://gitee.com/geomech/hydrate/issues/ID5HZX).

### 关键词

天然气水合物 / Gas Hydrate · 多场耦合 / THMC · 储层数值模拟 / Reservoir Simulation · 多相多组分流 / Multiphase Multicomponent Flow · 碳封存 / Carbon Sequestration · 页岩油原位转化 / Shale Oil In-situ Conversion · 热-流-力-化耦合

### 功能/特点

首先，[IGG-Hydrate](https://gitee.com/geomech/hydrate)是一个支持编程，进而实现复杂耦合功能的开放的计算模块：

1. 支持同时设置任意
   多种流体相态和组分。无论是单相流、两相流，还是复杂的多相多组分流动，均采用相同的配置方法，从而方便适配各种复杂的流动体系。支持:
   水/蒸气/水冰，CH<sub>4</sub>/CH<sub>4</sub>水合物，CO<sub>2</sub>/CO<sub>2</sub>水合物，盐度/砂，油/重油/干酪根，或其他
   自定义相态/组分;
2. 采用广义化学反应框架。假设任一化学反应的速率，都是温度、压力及相关组分浓度的函数；只需要给定相关函数或者插值数据，即可对化学反应进行建模。支持：水的蒸发/结冰/融化;
   CH<sub>4</sub>水合物形成/分解; CO<sub>2</sub>水合物形成/分解; 干酪根/重油裂解，或其他自定义反应;
3. 热传导/对流。自动计算岩土骨架的传热，以及依托多相多组分体系，自动计算所有加入流动体系的相态和组分的对流换热效应；
4. 采用动力学体系，计算储层力学问题，兼容应力/应变/振动等静力学和动力学过程（目前，此部分功能还在优化中）;
5. 基于指针(依托比如numpy等)，处理各个功能模块之间的数据交换，从而实现以上过程的高效耦合。

其次，[IGG-Hydrate](https://gitee.com/geomech/hydrate)也是一个面向不同应用场景的计算软件：
在水合物、页岩油、碳封存等领域，多个不同的场景，都有案例可以直接运行，学习成本不高。更多的应用场景在开发中，也欢迎(
并感谢)[联系作者](https://gitee.com/geomech/hydrate/issues/ID5HZX)
或者[新建Issue](https://gitee.com/geomech/hydrate/issues/new)来提出软件应用场景需求。

### 反馈

技术问题(bug反馈/建模咨询等)请[新建Issue](https://gitee.com/geomech/hydrate/issues/new)<sup>①</sup>
，其他问题请[联系作者](https://gitee.com/geomech/hydrate/issues/ID5HZX).

> 注：<sup>①</sup> 在[新建Issue](https://gitee.com/geomech/hydrate/issues/new)
> 之前，建议浏览[已有的Issues](https://gitee.com/geomech/hydrate/issues).

### 安装

1. 确保操作系统为Windows 10/11, x64<sup>①</sup>; Linux
   系统参考 [issues/IJWXWF](https://gitee.com/geomech/hydrate/issues/IJWXWF);
2. 安装[Python](https://www.python.org/) (64位, 3.8+, 推荐3.12+)<sup>②</sup> 并安装
   `PyQt6, pyqt6-qscintilla, PyQt6-WebEngine, numpy, scipy, matplotlib`等Python包<sup>③</sup>;
3. 安装[git](https://git-scm.com/)并确保`git`命令可用;
4. 使用[git](https://git-scm.com/)来拉取代码 (首次安装：`git clone https://gitee.com/geomech/hydrate.git`; 后续更新:
   `git pull`);
5. 将`hydrate`文件夹添加到Python搜索路径<sup>④</sup>;
6. 运行`python -m zmlx ui`打开界面;
7. 参考[`zmlx/demos`](https://gitee.com/geomech/hydrate/tree/master/zmlx/demos)建模<sup>⑤</sup>.

> 注：<sup>①</sup>
> 软件内核采用Visual Studio 2019编译，建议安装
> Visual
> Studio运行库 [VC_redist.x64.exe](https://gitee.com/geomech/hydrate/attach_files);
> <sup>②</sup>
> 推荐[WinPython](https://gitee.com/geomech/hydrate/attach_files),
> [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/main)
> 等Python发行版; <sup>③</sup> 运行脚本`zmlx/scripts/install_dep.py`可自动安装所有依赖包(
> 基于[pip](https://pypi.org/project/pip/))；
> <sup>④</sup> 使得Python中`import zmlx`可用; <sup>⑤</sup>
> 建议在[demos](https://gitee.com/geomech/hydrate/tree/master/zmlx/demos)
> 的基础上，向前追溯函数的实现; 另外，[demos](https://gitee.com/geomech/hydrate/tree/master/zmlx/demos)中案例仅供测试，作者不保证其参数的合理性.

### 作为 Python 库使用

`zmlx` 除提供界面外，也可作为 Python 库导入到脚本中，实现建模、求解与后处理的自动化。安装完成后（见上文「安装」），即可：

```python
import zmlx                # 顶层 API：建模、流体、求解、绘图等常用函数
```

常用入口集中在 `zmlx` 顶层命名空间，例如：

```python
from zmlx import seepage, create_ch4, create_h2o   # 模型与流体定义
from zmlx.tfc import solve                          # 多场耦合求解
from zmlx import plot_xy, show_xy                   # 绘图
```

完整的建模流程可参考 [`zmlx/demos`](https://gitee.com/geomech/hydrate/tree/master/zmlx/demos)。

### 学习/快速入门

建议从 [`zmlx/demos`](https://gitee.com/geomech/hydrate/tree/master/zmlx/demos) 开始学习。Demo 目录包含 **100+ 个可运行示例**，覆盖了单相流、两相流、水合物开发、热传导、力学等各类问题。

> 参阅 [`zmlx/demos/ReadMe.md`](https://gitee.com/geomech/hydrate/tree/master/zmlx/demos/ReadMe.md) 获取完整的建模指南，包括：
> - 建模方法与空间分布函数
> - 边界条件设置（定压、恒温、井）
> - 时间步进策略
> - 多相流与流体定义
> - 可视化策略
> - 常见陷阱与最佳实践

运行方式：
```bash
python zmlx/demos/flow_2ph/wat_disp_oil.py              # GUI 模式
python zmlx/demos/flow_2ph/wat_disp_oil.py --no-gui     # 命令行模式
```

### 协作/开发

欢迎并感谢您成为[IGG-Hydrate](https://gitee.com/geomech/hydrate)的开发者：

1. 请只修改自己创建的文件(以避免冲突);
2. 请只推送代码，*不要推送比较大的数据* (Gitee仓库有500Mb的总量限制);
3. 请务必熟悉[git](https://git-scm.com/)<sup>①</sup>;
4. 如果直接向[IGG-Hydrate](https://gitee.com/geomech/hydrate)
   推送代码，可能会报错（因为没有权限）。**建议**使用[Fork + Pull 模式](https://help.gitee.com/base/pullrequest/Fork+Pull)<sup>
   ②</sup>参与开发;
5. 在push代码前，先确保本地代码与主仓库同步。

> 注：<sup>①</sup> 在[Gitee帮助中心](https://gitee.com/help#article-header0)
> 有不少git的入门资料；新手建议安装[TortoiseGit](https://tortoisegit.org/)，它会在文件管理器添加右键菜单，可以满足大部分操作;
> 另外，如果是Pycharm用户，可以参考 https://gitee.com/geomech/hydrate/issues/IJT65R;
<sup>②</sup>[Fork + Pull 模式](https://help.gitee.com/base/pullrequest/Fork+Pull)是Gitee建议的方式. 如果不想使用Fork + Pull 模式，也可以点击[申请加入仓库](https://gitee.com/geomech/hydrate)成为开发者. 

### 镜像

仓库主网址为: [gitee.com/geomech/hydrate](https://gitee.com/geomech/hydrate),
镜像仓库: [github.com/geo-mech/hydrate](https://github.com/geo-mech/hydrate).

> 注：反馈或推送给代码，务必在[主仓库](https://gitee.com/geomech/hydrate)
> 进行，作者不会关注[镜像仓库](https://github.com/geo-mech/hydrate)的变化.

### 登录与使用

本软件可免费用于学术研究，发表文章时请声明使用了本软件。商业使用须联系作者获得许可。

#### 需要登录：把「本机」关联到你的邮箱

安装完成后必须先用邮箱完成一次登录，把本机与你的邮箱关联起来，软件才能正常使用
（未登录时，计算过程会提示登录）：

1. 打开界面（`python -m zmlx ui`或者运行`zml_ui.pyw`）；
2. 打开[登录页面](https://gitee.com/geomech/hydrate#登录与使用 "在本机界面里直接打开登录窗口")，
   入口是**菜单：帮助 → 用户 → 登录**（或界面状态栏右下角「未登录」的按钮）；
3. 按页面提示依次填写姓名、单位、邮箱，点「发送验证码」；
4. 到邮箱里收取 6 位数字验证码，填进「验证码」框，点「登录」；
5. 页面会显示登录结果与服务器原始答复；成功后状态栏右侧变为「已登录：<姓名>」。

要把这台电脑交还给别人（或不再使用）时，在登录页面点「**在这台电脑上退出**」即可：
只影响这一台电脑，登录邮箱与其它电脑都不受影响，需要时用同一个邮箱重新登录就能恢复。

> 注：① 邮箱是标识本机的唯一凭据 —— 换机器时用同一个邮箱再走一遍上面的流程即可；
> ② 当前的登录体系依赖网络，如果需要离线使用，请联系作者。

### 隐私声明

本软件有两类网络访问。

一、自动反馈运行日志（可关闭）。启动时会把上次运行的日志自动发送给开发者，用于定位崩溃
与报错、改进软件质量；内容只是程序自身的日志，不含你的模型数据或计算结果。

不希望发送，就在[系统变量](zmlx://gui/show_env_edit)里把「不向开发者反馈」设为 `Yes`；也可以先在
[反馈记录](zmlx://gui/show_feedbacks_view)里看看自己究竟反馈了什么，再决定要不要关。

> 但强烈不建议关闭：这是开发者发现真实问题的主要途径 —— 你遇到的那个崩溃、那次卡顿，
> 很可能正是靠它才被定位并修好的。

二、联网查询（无法关闭）。本软件采用邮箱登录（见上文「登录与使用」），登录状态校验
需要访问服务器。这是软件正常运行所必需的，关掉将无法使用。

### 关于软件名

之所以采用[IGG-Hydrate](https://gitee.com/geomech/hydrate)
，其中IGG是作者单位([中国科学院地质与地球物理研究所](http://www.igg.cas.cn/))的简称;
此软件模块，是作者在地球所重点部署项目“水合物开发的基础理论与技术”(IGGCAS-201903)
水合物试采系统温压场演化与流动保障机制”(U2244223)的支持下完成的初步版本。

### 更新

自2026年下半年起，IGG-Hydrate会按照**两个月一次**的频率进行更新。在此期间，除非有明确bug，否则代码将保持不变。
