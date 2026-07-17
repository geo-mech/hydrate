# zmlx.filesys — 文件系统操作（已弃用）

## 重要提示

**本包已弃用**，将在 2026-4-15 后移除。请迁移至 `zmlx.alg.fsys`。

```python
# 旧方式（已弃用）
from zmlx.filesys import list_files, join_paths

# 新方式（推荐）
from zmlx.alg import list_files, join_paths
# 或
from zmlx.alg.fsys import list_files, join_paths
```

---

## 概述

`zmlx.filesys` 提供文件系统相关的操作函数，包括文件列表、路径拼接、文件信息查询等。目前所有功能均为从 `zmlx.alg.fsys` 重新导出的转发器。

---

## 函数列表（即将迁移）

| 函数 | 描述 | 迁移目标 |
|------|------|---------|
| `list_files(path, keywords, exts)` | 递归文件列表 | `zmlx.alg.fsys` |
| `list_code_files(path, exts)` | 列出代码文件 | `zmlx.alg.fsys` |
| `count_lines(path)` | 统计代码行数 | `zmlx.alg.fsys` |
| `get_lines(path)` | 统计文本文件行数 | `zmlx.alg.fsys` |
| `first_only(path)` | 确保操作仅执行一次 | `zmlx.alg.fsys` |
| `get_last_file(folder)` | 按字母序最后文件 | `zmlx.alg.fsys` |
| `get_latest_file(folder)` | 按修改时间最新文件 | `zmlx.alg.fsys` |
| `get_size_mb(path)` | 文件/文件夹大小（MB） | `zmlx.alg.fsys` |
| `has_permission(folder)` | 检查文件夹读权限 | `zmlx.alg.fsys` |
| `in_directory(file, dir)` | 检查文件是否在目录下 | `zmlx.alg.fsys` |
| `join_paths(a, b)` | 安全路径拼接 | `zmlx.alg.fsys` |
| `make_fname(time, folder, ext)` | 按时间戳生成文件名 | `zmlx.alg.fsys` |
| `make_fpath(folder, step, ext)` | 按步数生成输出路径 | `zmlx.alg.fsys` |
| `prepare_dir(folder)` | 准备空输出目录 | `zmlx.alg.fsys` |
| `show_fileinfo(filepath)` | 显示文件元信息 | `zmlx.alg.fsys` |
| `print_tag(folder)` | 创建时间标签 | `zmlx.alg.fsys` |
| `time_string()` | 生成时间戳字符串 | `zmlx.alg.fsys` |
| `has_tag(folder)` | 检查标签文件 | `zmlx.alg.fsys` |
| `make_dirs(path)` | 创建目录 | `zmlx.exts` |
| `make_parent(path)` | 创建父目录 | `zmlx.exts` |
| `change_fmt(...)` | 批量格式转换 | `zmlx.tfc` |

---

## 不迁移的模块

| 模块 | 处理方式 |
|------|---------|
| `change_fmt.py` | 独立脚本，不从 `alg.fsys` 导入 |
| `opath.py` | 重定向到 `zmlx.io.path` 和 `zmlx.io.TaskFolder` |
