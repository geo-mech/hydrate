### 简介

[**IGG-Hydrate**](https://gitee.com/geomech/hydrate): 储层多场耦合计算模块(Python接口和C++内核)。
用于：
1、天然气水合物[成藏](https://doi.org/10.3390/w16192822)/[开发](https://doi.org/10.1016/j.apenergy.2024.122963)/[碳封存](https://doi.org/10.1016/j.fuel.2025.137599);
2、页岩油[原位转化](https://doi.org/10.1016/j.petsci.2024.05.025)；
3、储层内的其他流动/传热/化学/变形(THMC)耦合问题.

### 作者

[张召彬](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201703/t20170306_4755492.html)<sup>
1,2,x</sup>, [李守定](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201412/t20141218_4278784.html)<sup>
1,2</sup>, [李晓](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/200907/t20090713_2065538.html)<sup>1,2</sup>, 徐涛<sup>
1,2</sup>, 李宇轩<sup>1,2</sup>, Maryelin<sup>1,2</sup>, 谢卓然<sup>1,2</sup>, 李晓旗<sup>1,2</sup>

<sup>1</sup>[中国科学院地质与地球物理研究所](https://igg.cas.cn/)(北京, 100029);

<sup>2</sup>[中国科学院大学](https://www.ucas.ac.cn/)(北京, 101408).

<sup>x</sup>
联系人: [张召彬](https://igg.cas.cn/sourcedb_igg_cas/cn/zjrck/201703/t20170306_4755492.html),
邮箱: [zhangzhaobin@mail.iggcas.ac.cn](zhangzhaobin@mail.iggcas.ac.cn);
或添加[微信](https://gitee.com/geomech/hydrate/issues/ID5HZX).

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

注：<sup>①</sup> 在[新建Issue](https://gitee.com/geomech/hydrate/issues/new)
之前，建议浏览[已有的Issues](https://gitee.com/geomech/hydrate/issues).

### 安装

#### Windows 版本

1. 确保操作系统为Windows 10/11, x64<sup>①</sup>;
2. 安装[Python](https://www.python.org/) (64位, 3.8+, 推荐3.12+)<sup>②</sup> 并安装
   `PyQt6, pyqt6-qscintilla, PyQt6-WebEngine, numpy, scipy, matplotlib`等Python包<sup>③</sup>;
3. 下载[IGG-Hydrate](https://gitee.com/geomech/hydrate)
   的[zip包](https://gitee.com/geomech/hydrate/repository/archive/master.zip)并解压(或者使用[git](https://git-scm.com/)
   来[clone](https://gitee.com/help/articles/4111#article-header0)代码); 之后，将`zml.py`所在的文件夹(建议纯英文路径)
   添加到Python的搜索路径中;
4. 参考[`zmlx/demo`](https://gitee.com/geomech/hydrate/tree/master/zmlx/demo)建模<sup>④</sup>; 运行[
   `zml_ui.pyw`](https://gitee.com/geomech/hydrate/blob/master/zml_ui.pyw)打开界面.

注：<sup>①</sup>
软件计算内核采用Visual Studio编译，建议用户在运行[IGG-Hydrate](https://gitee.com/geomech/hydrate)之前，提前安装
Visual
Studio运行库 [VC_redist.x64.exe](https://gitee.com/geomech/hydrate/attach_files) (
尽管，貌似很多时候系统都内置了，但是安装这个运行库，并不会有任何的副作用);
<sup>②</sup> 推荐使用[WinPython](https://gitee.com/geomech/hydrate/attach_files) (
绿色免安装，同时也是软件作者使用的发行版，更能保证和[IGG-Hydrate](https://gitee.com/geomech/hydrate)的兼容);
注意：关于Python版本的需求主要来自界面/绘图等功能;
<sup>③</sup> 运行脚本`zmlx/script/install_dep.py`来可自动安装所有依赖包(基于[pip](https://pypi.org/project/pip/)
，不保证安装成功)；另外，`PyQt5`不再支持;
<sup>④</sup> 建议在[demo](https://gitee.com/geomech/hydrate/tree/master/zmlx/demo)
的基础上，向前追溯函数的实现; [demo](https://gitee.com/geomech/hydrate/tree/master/zmlx/demo)中案例仅供测试，作者不保证其参数的合理性.

#### Linux 版本

**系统要求**：推荐 Ubuntu 24.04 LTS (其他 Debian/Ubuntu 衍生版本可参考，未测试其他发行版)

**安装步骤**：

1. 打开终端，更新系统软件源：
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. 安装必要依赖：
   ```bash
   sudo apt install -y git libboost-all-dev python3-venv python3-pip
   ```
    - `git`: 用于克隆代码仓库
    - `libboost-all-dev`: Boost 库（编译依赖）
    - `python3-venv`: Python 虚拟环境工具
    - `python3-pip`: Python 包管理工具

3. 创建并激活 Python 虚拟环境（推荐，避免依赖冲突）：
   ```bash
   # 创建虚拟环境（可自定义环境名称）
   python3 -m venv igg_hydrate_env
   
   # 激活虚拟环境
   source igg_hydrate_env/bin/activate
   ```
   激活后终端提示符会显示 `(igg_hydrate_env)` 前缀，表示已进入虚拟环境。

4. 安装 IGG-Hydrate（自动安装所有 Python 依赖）：
   ```bash
   pip install git+https://gitee.com/geomech/hydrate.git
   ```
   > 注意：首次安装可能需要较长时间，需耐心等待。

5. 启动 IGG-Hydrate 界面：
   ```bash
   python -m zmlx ui
   ```

**使用说明**：

- 每次使用前需激活虚拟环境：`source igg_hydrate_env/bin/activate`
- 退出虚拟环境：`deactivate`
- Linux 下生成的二进制模型文件与 Windows 不兼容，如需跨平台使用，请保存为 `txt` 或 `xml` 格式。

**故障排查**：

- 在Linux上运行，核心是要满足动态库`zmlx/exts/zml.so`的依赖，请自行使用相关的工具来检查;
- 可以使用ctypes尝试导入`zmlx/exts/zml.so`来测试环境配置是否成功. 

### 协作/开发

欢迎并感谢您成为[IGG-Hydrate](https://gitee.com/geomech/hydrate)的开发者：

1. 请只修改自己创建的文件(以避免冲突);
2. 请只推送代码，*不要推送比较大的数据* (Gitee仓库有500Mb的总量限制);
3. 请务必熟悉[git](https://git-scm.com/)<sup>①</sup>;
4. 如果直接向[IGG-Hydrate](https://gitee.com/geomech/hydrate)
   推送代码，可能会报错（因为没有权限）。此时，可以在页面右上角，点击[申请加入仓库](https://gitee.com/geomech/hydrate)
   ，成为开发者；或者，你也可以使用[Fork + Pull 模式](https://help.gitee.com/base/pullrequest/Fork+Pull)<sup>②</sup>参与开发。

注：<sup>①</sup> 在[Gitee帮助中心](https://gitee.com/help#article-header0)
有不少git的入门资料；新手建议安装[TortoiseGit](https://tortoisegit.org/)，它会在文件管理器添加右键菜单，可以满足大部分操作;
另外，如果是Pycharm用户，可以参考 https://gitee.com/geomech/hydrate/issues/IJT65R;
<sup>②</sup>[Fork + Pull 模式](https://help.gitee.com/base/pullrequest/Fork+Pull)是Gitee建议的一种参与开发的方式.

### 镜像

仓库主网址为: [gitee.com/geomech/hydrate](https://gitee.com/geomech/hydrate), 镜像仓库<sup>
①</sup>: [github.com/geo-mech/hydrate](https://github.com/geo-mech/hydrate).

注：<sup>①</sup> 反馈或推送给代码，务必在[主仓库](https://gitee.com/geomech/hydrate)
进行，作者不会关注[镜像仓库](https://github.com/geo-mech/hydrate)的变化.

### 授权

大部分功能可自由免费使用.
但是，不同的模块可能有不同的授权要求，建议使用前先联系并[告知作者](https://gitee.com/geomech/hydrate/issues/ID5HZX)，谢谢。

特别注意：软件启动的时候，会检查网络时间，进而确保运行的是比较新的版本。对于过期的版本，仍然可以运行，但是计算的速度会受到限制。因此，
请确保使用最新版，并在运行此软件模块的时候，确保电脑联网，否则计算会很慢。之所以有此限制，主要是作者不希望维护多个版本。

### 关于软件名

之所以采用[IGG-Hydrate](https://gitee.com/geomech/hydrate)
，其中IGG是作者单位([中国科学院地质与地球物理研究所](http://www.igg.cas.cn/))的简称;
此软件模块，是作者在地球所重点部署项目“水合物开发的基础理论与技术”(IGGCAS-201903)
水合物试采系统温压场演化与流动保障机制”(U2244223)的支持下完成的初步版本。