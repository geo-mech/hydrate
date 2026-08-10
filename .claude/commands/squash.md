---
description: 合并当前未推送的提交，并根据修改内容自动生成合并后的描述
---

执行以下操作：

1. 用 `git log origin/master..HEAD --oneline` 查看未推送的提交列表
2. 用 `git diff origin/master..HEAD --stat` 查看文件变更总结
3. 读取 `origin/master` 上的 `pyproject.toml` 中的版本号（基准版本）
4. 将基准版本的小版本号 **+1** 作为合并后的版本号（例如基准 1.7.1 → 合并后 1.7.2）
5. 用 `git reset --soft origin/master` 将所有提交合并到暂存区
6. 更新 `pyproject.toml` 和 `CHANGELOG.md` 中的版本号为计算出的版本号
7. 根据变更内容自动生成清晰的提交描述（中文），格式如下：
   - 第一行：版本号 + 简短描述
   - 空行
   - == 分类标题 ==（如：核心重构 / bug修复 / demo / 文档 / 配置）
   - 每个分类下列出具体变更
8. `git commit` 提交

注意：
- 描述要简洁、结构化
- 不要提及 "Co-Authored-By" 行
- 分类标题使用中文，内容使用简短列表
- 合并后版本号应为基准版本 + 1 个小版本（不是累加所有中间版本的增量）
