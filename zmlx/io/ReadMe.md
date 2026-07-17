# zmlx.io — 输入输出模块

## 概述

`zmlx.io` 提供文件读写、路径管理、数据序列化等输入输出功能。支持文本文件、JSON、Python 格式、XYZ 坐标数据等多种格式。

---

## 快速开始

```python
from zmlx import *

# 文本文件
data = load_txt('data.txt')           # 读取文本为 list
col = load_col('data.txt', index=0)   # 读取指定列
append_file('log.txt', '新数据\n')    # 追加文本

# JSON
from zmlx.io.json_ex import write, read
write('config.json', {'key': 'value'})
data = read('config.json')            # 失败时返回 None

# Python 格式
from zmlx.io.python import write_py, read_py
write_py('output.py', {'a': 1, 'b': 2})
data = read_py('output.py')
```

---

## 主要模块

### `base.py` — 核心 IO 函数

| 函数 | 描述 |
|------|------|
| `load_txt(*args, **kwargs)` | 读取文本文件为 Python list（numpy.loadtxt 包装后 .tolist()） |
| `load_col(fname, index, dtype, text)` | 从文件提取指定列数据 |
| `append_file(filename, text, encoding)` | 在文件末尾追加文本 |
| `get_text_back(filename, max_length)` | 从文件末尾读取文本（tail 风格） |
| `TaskFolder`（类） | 任务文件夹管理器，自动创建带时间戳的目录 |

### `path.py` — 路径管理

| 函数 | 描述 |
|------|------|
| `get_path(*args, tag, key)` | 返回输出文件路径（从环境变量读取工作目录） |
| `set_path(folder, tag, key)` | 设置输出目录（写入环境变量） |

### `json_ex.py` — JSON 读写

| 函数 | 描述 |
|------|------|
| `write(path, obj, indent=2)` | 序列化 JSON 文件 |
| `read(path, encoding, default)` | 反序列化 JSON 文件（失败返回默认值） |

### `python.py` — Python 格式

| 函数 | 描述 |
|------|------|
| `write_py(path, data)` | 以 Python repr 格式写入 .py 文件 |
| `read_py(path, key)` | 读取并执行 .py 文件，返回指定命名空间变量 |

### `text.py` — 文本文件

| 函数 | 描述 |
|------|------|
| `read_text(path)` | 读取文本文件（委托给 zmlx.exts） |
| `write_text(path, text)` | 写入文本文件（委托给 zmlx.exts） |

### `xyz.py` — 坐标数据加载

| 函数 | 描述 |
|------|------|
| `load_xyz(ipath, ix, iy, iz)` | 从文本文件加载 XYZ 坐标（numpy.loadtxt），支持按列索引提取 |

---

## 模块列表

| 模块 | 描述 |
|------|------|
| `base.py` | 核心 IO 函数（load_txt, load_col, append_file, TaskFolder） |
| `path.py` | 工作目录和输出路径管理 |
| `json_ex.py` | JSON 文件读写（继承标准库 json） |
| `python.py` | Python 格式文件读写 |
| `text.py` | 纯文本文件读写 |
| `xyz.py` | XYZ 坐标数据加载 |
| `env/plt_export_dpi.py` | matplotlib 导出 DPI 环境变量配置 |

---

## 与其他模块的关系

- `zmlx.exts`：依赖 `make_dirs`、`make_parent`、`read_text`、`write_text`
- `zmlx.alg.fsys`：IO 基础函数迁移目标
- `zmlx.mesh.io`：三角网格文件加载（`load_trimesh`）
- 注：`zmlx.io` 中的部分函数（如 `load_trimesh`）已迁移到 `zmlx.mesh.io`
