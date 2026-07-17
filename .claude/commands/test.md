---
description: 批量运行 demo 测试
---

运行 `python zmlx/demo/test_all_demos.py`，分析 test_report.log 并汇报通过/超时/失败/错误。

**参数**：`--jobs N` 线程数，`--timeout N` 超时秒数。
**默认**：`--jobs CPU核心数 --timeout 60`

**超时调整**：
- "快速测试" → `--timeout 30`
- "深度测试"/"详细测试"/"仔细测试" → `--timeout 500`
- 用户指定时长 → 对应秒数
