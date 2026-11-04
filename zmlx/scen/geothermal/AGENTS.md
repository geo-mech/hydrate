# AGENTS.md — `zmlx/scen/geothermal/`

**本文件只约束 `zmlx/scen/geothermal/` 这一个包**，不改变仓库其它任何地方的规矩。
与上层文档冲突时，**以本文件为准**（`zmlx/scen/geothermal/` > `projects/zml/AGENTS.md` >
仓库根 `AGENTS.md`）。

## 1. 这个包是「开发中的算例集」，不走发布流程

地热算例还在持续演进：算例会不断新加、参数会反复调整、结构随时可能推倒重来。
如果每次改动都要占一个补丁版本号、写一条全局 CHANGELOG，版本历史会被这些中间状态
淹没（一天可能刷出好几个版本），而真正的发布说明反而读不出东西。

因此，**对 `zmlx/scen/geothermal/` 的后续修改**：

| 事项 | 做法 |
|---|---|
| **版本号**（`pyproject.toml` / `zmlx/__init__.py`） | ❌ **不动** |
| **全局 CHANGELOG**（`zmlx/data/CHANGELOG.md`） | ❌ **不写**、不修改 |
| **改动记录** | ✅ 写进本包内的 [`CHANGELOG.md`](CHANGELOG.md) |
| 代码、文档、测试 | 照常 |

⚠️ **只对「改动完全落在这个包里」时适用**。若一次提交同时改了包外的文件
（例如 `zmlx/scen/ReadMe.md`、`zmlx/fluids/`、`zmlx/tfc/`），则**整次提交按常规流程走**：
升版本号、写全局 CHANGELOG —— 因为那些文件是随包公开发布的，需要发布说明。

⚠️ 仓库根 `AGENTS.md` 的「2. 提交」一节列的是**默认流程**，本文件是它之上的**一层豁免**：
仍在成型、会反复改动的场景代码，不该去占版本号和发布说明。

### 合并（squash）也按本约定，不升版本号

用户说「合并」时，仓库根 `AGENTS.md` §3 的默认流程是：

> 读 `origin/master` 的版本号作基准，小版本号 **+1** 作为合并后的版本号，
> 再同步 `pyproject.toml`、`zmlx/__init__.py`、`zmlx/data/CHANGELOG.md` 三处。

**当要合并的提交全部只落在本包内时，跳过那一步。** 做法：

1. `git log origin/master..HEAD --oneline` 看清有哪些未推送提交；
2. `git reset --soft origin/master` 把它们压回暂存区；
3. **不升版本号**、**不写全局 CHANGELOG**；
4. `git commit`，描述按 `== 分类标题 ==` 结构写（插件入口 / 包结构与分层 / 文档 /
   本包约定 / 验证 / 说明），合并前有几次提交也要在「说明」里交代清楚。

> 2026-11-04 定：此次合并起初按默认流程升到了 1.9.23 并写了三条全局 CHANGELOG，
> 随后全部撤回，改为「纯 geothermal 压缩、不动版本号」。**以后照本章办，不要再问。**

⚠️ 若待合并的提交里**混有包外改动**，则仍按根 `AGENTS.md` §3 的默认流程处理
（升版本号 + 写全局 CHANGELOG），与上面「提交」一节的口径保持一致。

## 2. 本包的 CHANGELOG

包内 [`CHANGELOG.md`](CHANGELOG.md) 是**这个包自己的改动记录**，与全局 CHANGELOG 分工：

| 文件 | 记什么 |
|---|---|
| 本包 `CHANGELOG.md` | 本包**每一次**改动（含拆分文件、改参数、补文档这类中间步骤） |
| 全局 `zmlx/data/CHANGELOG.md` | **只在**改动溢出到包外、或本包功能正式对外发布时才写 |

写法：顶部新增条目，标题形如 `## 2026-11-04`（按日期，不必编版本号），
一句话说清改了什么，需要时再用要点展开。**不要把多条并进一条**。

## 3. 包的结构与约定

```
zmlx/scen/geothermal/
├── zml_plugin.py        插件入口（一级菜单「地热」，默认不加载）
├── widgets/             控件集（每个文件一个控件）
│   └── well_cross_section.py  参数界面 WellCrossSectionWidget（填参数后 create + solve）
├── _mesh.py             网格：mesh_xz(jx, jz)
├── _fludefs.py          流体：create_fludefs()
├── _show.py             绘图：show(model, jx, jz, *, circles=None)
├── _well_cross_section.py  井截面取热建模：create(...) / solve(...)
├── cases/               算例，每个文件一个（case_02.py 的 test_high_perm / test_low_perm）
├── CHANGELOG.md         本包的改动记录
└── AGENTS.md            本文件
```

- **分层**：`_mesh` / `_fludefs` / `_show` 只做自己那一件事，`_well_cross_section` 组装，`cases/` 串接。
  加新算例时**新建一个 `cases/case_XX.py`**，不要往已有算例里塞分支。
- **算例的函数名要说明该工况的特点**（`test_high_perm` / `test_low_perm`），不要用
  `test_02` 这种纯编号 —— 插件菜单直接用函数名做标签，用户从菜单就该看出区别。
- **导入**：一律显式导入用到的名字，**禁止** `from zmlx import *`。
- **插件入口**：菜单项、`gui.add_func` 的命令名**一旦发布不能改名**（标签页状态里存的是原文）。
  求解一律经 `gui.start` 走控制台线程，并先判 `gui.is_running()`（控制台单槽位，忙时会静默丢弃请求）。
- **流体温度范围**：`h2o.create` 内有硬断言 `269 < t_min < t_max < 350`，
  且 `t_min` / `t_max` 是**查表钳制边界**（超范围会被静默截断成边界值，不报错也不外推），
  不是「算例温度区间」。改范围前先读 `_fludefs.py` 的说明。

## 4. 文档标准（本包要发布）

本包随 `zmlx` 一起发布，用户会读源码和 ``help()``，所以文档按**发布级**要求：

| 位置 | 要求 |
|---|---|
| **每个模块** | 顶部必须有 docstring：这个模块负责什么、放在整体哪一步 |
| **每个函数**（含内部辅助、嵌套函数） | 必须有 docstring，一句话说清做什么 |
| **有参数的函数** | 用 `Args:` 逐条说明含义、单位、默认值 |
| **有返回值的函数** | 用 `Returns:` 说明类型与含义 |
| **会抛异常的** | 用 `Raises:` 列出异常类型与触发条件 |
| **非显然的常量** | 用 `#:` 注释说明取值依据 |
| **反直觉的地方** | 用 `⚠️` 显式标注（例如 `dist` 不是热扩散率、`t_min/t_max` 是钳制边界） |

⚠️ **文档必须与代码同步**：改了参数、默认值、范围、文件名，同一提交里就要改掉
对应的文档 —— 本包历史上多次出现「文档还写着自然对流 / 500 天 / `[-0.6,0.6]`，
而代码早已是井截面取热 / 10 年 / `[-50,50]`」的情形，发布前已全部修正。

⚠️ **不要用旧格式**：统一 `Args:` / `Returns:` / `Raises:`（英文段名、中文内容），
不要混用 `参数:` / `返回:`。

⚠️ 引用**已删除的函数或模块**是错误：删代码时要同步扫一遍文档里的
`:func:` / ``xxx.py`` / ``cases/...`` 引用。
