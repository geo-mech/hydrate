# zmlx.alg — 通用算法与工具集

## 概述

`zmlx.alg` 是 zmlx 的通用算法和工具模块集合。包含基础数学函数、文件系统操作、插值算法、并行计算（多进程/多线程）、系统管理、图像处理、几何网格查询等。大部分算法与 zml 核心无关，可独立使用。

> **注意**：本包内容正在逐步整理中。部分函数已迁移到 `zmlx.exts`、`zmlx.io`、`zmlx.geometry` 等更合适的包中，原位置保留已弃用的转发器。

---

## 快速开始

```python
from zmlx.alg import *

# 基础数学
clamp(value, 0, 1)          # 钳制到 [0, 1]
linspace(0, 10, 5)          # 等间距数组（纯 Python）
mean(1, 2, 3, 4)            # 算术平均
year_to_seconds(365)        # 年→秒
time2str(86400)              # 秒→可读字符串 ("1 d")
mass2str(1000)               # 千克→可读字符串 ("1 t")
fsize2str(1024**3)           # 字节→可读字符串 ("1 Gb")

# 文件系统
list_files('.', extensions=['.py'])  # 列出 Python 文件
get_last_file('/path/to/folder')     # 按字母序最后文件
get_latest_file('/path/to/folder')   # 按修改时间最新文件
prepare_dir('output')                # 清空并准备输出目录
print_tag('output')                  # 创建时间标签

# 插值
interp1(x, y, xq)                    # 1D 插值（MATLAB 风格）

# 并行
apply_async(tasks, processes=4)      # 多进程并行
```

---

## 按功能分类

### 基础数学运算（`base.py`）

| 函数 | 描述 |
|------|------|
| `clamp(value, left, right)` | 数值钳制 |
| `linspace(start, stop, num)` | 等间距点序列（纯 Python 实现） |
| `mean(*args)` | 算术平均 |
| `divide_list(lst, n)` | 将列表均分为 n 个子列表 |
| `is_sorted(vx, compare)` | 检查列表是否有序 |
| `make_index(index)` | 索引归一化 |
| `rand_dir3(norm, max_try, default)` | 生成随机 3D 单位方向向量 |
| `less(x, y)` | 小于比较辅助函数 |
| `join_cols(*args)` / `join_rows(*args)` | 数组水平/垂直拼接 |

### 时间/质量/尺寸格式化

| 函数 | 描述 | 示例 |
|------|------|------|
| `year_to_seconds(years)` | 年→秒 | `year_to_seconds(1)` → 31536000 |
| `time2str(s)` | 秒→可读字符串 | `"1 d"`、`"3.2 h"`、`"500 ms"` |
| `mass2str(kg)` | 千克→可读字符串 | `"1 t"`、`"500 kg"`、`"30 g"` |
| `fsize2str(size)` | 字节→可读字符串 | `"1 Gb"`、`"500 Mb"` |

### 文件系统操作（`fsys.py`）

| 函数 | 描述 |
|------|------|
| `list_files(path, keywords, exts)` | 递归文件列表（关键字+扩展名过滤） |
| `list_code_files(path, exts)` | 列出代码文件（.h, .cpp, .py 等） |
| `count_lines(path, exts)` | 统计代码行数 |
| `get_lines(path)` | 统计文本文件行数 |
| `first_only(path)` | 确保操作只执行一次（标记文件机制） |
| `get_last_file(folder)` | 按字母序最后文件 |
| `get_latest_file(folder)` | 按修改时间最新文件 |
| `get_size_mb(path)` | 文件/文件夹大小 |
| `in_directory(file, dir)` | 检查文件是否在目录下 |
| `make_fname(time, folder, ext, unit)` | 按时间戳生成文件名 |
| `make_fpath(folder, step, ext, name)` | 按步数生成输出路径 |
| `prepare_dir(folder, direct_del)` | 准备空输出目录 |
| `show_fileinfo(filepath)` | 显示文件元信息 |
| `print_tag(folder)` | 创建时间标签标记数据位置 |
| `time_string()` | 生成时间戳字符串 `YYYYmmddTHHMMSS` |
| `has_tag(folder)` | 检查目录中是否有标签文件 |

### 插值（`interp.py`）

| 函数 | 描述 |
|------|------|
| `create_interp1d(x, y, kind)` | 创建 1D 插值器（scipy interp1d 包装） |
| `interp1(x, y, xq)` | MATLAB 风格 1D 插值 |

### 并行计算

| 函数 | 来源 | 描述 |
|------|------|------|
| `apply_async(tasks, processes)` | `multi_proc.py` | 多进程并行执行任务 |
| `create_async(func, args, kwds)` | `multi_proc.py` | 创建异步任务字典 |
| `apply_threads(tasks)` | `multi_thread.py` | 多线程并行执行任务 |

### 系统操作（`sys.py`）

| 函数 | 描述 |
|------|------|
| `pip_install(package_name)` | 安装 Python 包 |
| `install_dep()` | 安装 zmlx 依赖 |
| `import_module(name, package)` | 导入模块（含自动安装回退） |
| `startfile(path)` | 跨平台文件打开（替代 os.startfile） |
| `create_shortcut(target, path)` | 创建 Windows 快捷方式 |
| `srand(seed)` | 设置随机种子（Python + zml 内核） |
| `get_city()` | 获取城市信息（基于 IP） |
| `timing_show(key, func)` | 执行函数并打印耗时 |
| `sbatch(args)` | 提交 SLURM 批处理作业（北京超算） |
| `has_module(name)` | 检查模块是否存在 |

### 图像处理（`image.py`）

| 函数 | 描述 |
|------|------|
| `make_video(video_name, image_folder, fps)` | 合成图像为 MP4 视频（OpenCV） |
| `convert_png_to_jpg(folder)` | 批量 PNG→JPG 转换 |
| `crop_image(output, input, left, upper, right, lower)` | 裁剪图片 |
| `get_data(img, cmap, ...)` | 从颜色映射图像提取数据 |
| `load_field(option, folder)` | 从图像+颜色映射配置加载场 |

### 渗流网格查询

| 函数 | 来源 | 描述 |
|------|------|------|
| `get_cells_around_seg(seg, dist, model)` | `around_seg.py` | 获取线段周围的 Cell |
| `get_faces_around_seg(seg, dist, model)` | `around_seg.py` | 获取线段周围的 Face |
| `get_faces_across(model, p0, p1)` | `faces_across.py` | 获取穿过两点的所有 Face |

### 裂缝力学（`frac.py`）

| 函数 | 描述 |
|------|------|
| `get_frac_width(pos, half_length, ...)` | 解析裂缝宽度（Crouch & Starfield BEM 解） |
| `get_frac_cond(aperture, length, height, vis)` | 裂缝导流能力（立方定律） |

### 渗透率（`perm_cascade.py`）

| 函数 | 描述 |
|------|------|
| `get_average2(l1, k1, l2, k2)` | 两段串联调和平均 |
| `get_average(*perm)` | 多段等长串联渗透率调和平均 |

---

## 模块列表

| 模块 | 描述 |
|------|------|
| `base.py` | 基础数学运算和时间/质量格式化 |
| `fsys.py` | 文件系统操作 |
| `sys.py` | 系统管理（pip、快捷方式、随机种子） |
| `interp.py` | 1D 插值 |
| `multi_proc.py` | 多进程并行 |
| `multi_thread.py` | 多线程并行 |
| `image.py` | 图像处理（视频合成、裁剪、数据提取） |
| `vec.py` | Vector ↔ NumPy 互转 |
| `around_seg.py` | 线段周围网格查询 |
| `faces_across.py` | 面穿越查询 |
| `frac.py` | 裂缝力学宽度/导流能力 |
| `perm_cascade.py` | 串联渗透率平均 |
| `numpy_algs.py` | NumPy ↔ 文本转换 |
| `search_paths.py` | 搜索路径管理 |
| `git.py` | Git 操作（clone, update） |
| `marked_text.py` | 标记文本提取/替换 |
| `os.py` | OS 级操作（文件删除、路径、桌面） |

---

## 与其他模块的关系

- 本包设计上尽量不依赖其他 zmlx 模块（`base.py`、`fsys.py` 为纯 Python）
- `sys.py` 中的 `pip_install` 等函数用于管理 zmlx 的第三方依赖
- 文件系统操作（`fsys.py`）是 `zmlx.filesys`（已弃用）的迁移目标
- `around_seg.py` 和 `faces_across.py` 是渗流网格特有算法
