---
description: 合并当前未推送的提交，并根据修改内容自动生成合并后的描述
---

执行以下操作：

1. 用 `git log origin/master..HEAD --oneline` 查看未推送的提交列表
2. 用 `git diff origin/master..HEAD --stat` 查看文件变更总结
3. 用 `git reset --soft origin/master` 将所有提交合并到暂存区
4. 根据变更内容自动生成清晰的提交描述（中文），格式如下：
   - 第一行：版本号 + 简短描述
   - 空行
   - == 分类标题 ==（如：核心重构 / bug修复 / demo / 文档 / 配置）
   - 每个分类下列出具体变更
5. 使用 `pyproject.toml` 中的当前版本号（不额外升级）
6. `git commit` 提交

注意：
- 描述要简洁、结构化
- 不要提及 "Co-Authored-By" 行
- 分类标题使用中文，内容使用简短列表
