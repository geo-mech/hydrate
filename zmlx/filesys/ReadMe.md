# zmlx.filesys — 文件系统操作（已弃用）

## 重要提示

**本包已弃用**（原定 2026-4-15 移除，**已过期**，实际仍在）。请迁移至 `zmlx.algs.fsys`。

```python
# 旧方式（已弃用）
from zmlx.filesys import list_files, join_paths

# 新方式（推荐）
from zmlx.algs import list_files, join_paths
# 或
from zmlx.algs.fsys import list_files, join_paths
```

---

## 概述

`zmlx.filesys` 提供文件系统相关的操作函数，包括文件列表、路径拼接、文件信息查询等。目前所有功能均为从 `zmlx.algs.fsys` 重新导出的转发器。

---

## 函数列表

以下函数的说明见 `zmlx/algs/ReadMe.md`（`get_size_mb` 返回 MB）：

`list_files(path, keywords, exts)`、`list_code_files(path, exts)`、`count_lines(path)`、`get_lines(path)`、`first_only(path)`、`get_last_file(folder)`、`get_latest_file(folder)`、`get_size_mb(path)`、`in_directory(file, dir)`、`make_fname(time, folder, ext)`、`make_fpath(folder, step, ext)`、`prepare_dir(folder)`、`show_fileinfo(filepath)`、`print_tag(folder)`、`time_string()`、`has_tag(folder)`

以下函数不在 `zmlx/algs/ReadMe.md` 的列表中：

| 函数 | 描述 | 迁移目标 |
|------|------|---------|
| `has_permission(folder)` | 检查文件夹读权限 | `zmlx.algs.fsys` |
| `join_paths(a, b)` | 安全路径拼接 | `zmlx.algs.fsys` |
| `make_dirs(path)` | 创建目录 | `zmlx.exts` |
| `make_parent(path)` | 创建父目录 | `zmlx.exts` |
| `change_fmt(...)` | 批量格式转换 | `zmlx.tfc` |

---

## 不迁移的模块

| 模块 | 处理方式 |
|------|---------|
| `change_fmt.py` | 独立脚本，不从 `alg.fsys` 导入 |
| `opath.py` | 重定向到 `zmlx.io.path` 和 `zmlx.io.TaskFolder` |
