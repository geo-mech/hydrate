try:
    import pygit2
except ImportError:
    pygit2 = None


def clone(repo_url, local_path):
    """
    克隆仓库到本地路径
    """
    try:
        repo = pygit2.clone_repository(repo_url, local_path)
        print(f"成功克隆仓库到 {local_path}")
        return repo
    except pygit2.GitError as e:
        print(f"克隆仓库失败：{str(e)}")


def update(local_path):
    """
    拉取远程仓库更新
    """
    repo = pygit2.Repository(local_path)

    # 获取远程仓库
    remote = repo.remotes["origin"]
    remote.fetch()  # 拉取远程更新

    # 获取本地分支和远程跟踪分支的 HEAD
    local_branch_name = "master"
    remote_branch_name = f"origin/{local_branch_name}"

    # 本地分支的 HEAD
    local_branch = repo.lookup_branch(local_branch_name)
    local_commit = repo.get(local_branch.target)

    # 远程跟踪分支的 HEAD
    remote_branch = repo.lookup_branch(remote_branch_name,
                                       pygit2.GIT_BRANCH_REMOTE)
    remote_commit = repo.get(remote_branch.target)

    # 检查是否有更新
    if local_commit.id == remote_commit.id:
        print("无更新，无需操作")
    else:
        # 分析合并类型
        analysis, *_ = repo.merge_analysis(remote_commit.id)

        # 处理快进合并
        if analysis & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
            # 移动分支指针到远程提交
            local_branch.set_target(remote_commit.id)
            # 更新工作区文件
            repo.checkout_tree(repo.get(remote_commit.id))
            # 更新 HEAD 引用
            repo.head.set_target(remote_commit.id)
            print("已快进合并到最新版本")

        # 处理普通合并（需生成合并提交）
        elif analysis & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
            try:
                # 执行合并操作
                repo.merge(remote_commit.id)

                # 检查冲突
                if repo.index.conflicts:
                    print("发现冲突，需手动解决")
                    # 冲突处理逻辑（需手动实现）
                else:
                    # 写入合并后的树对象
                    tree = repo.index.write_tree()
                    # 创建合并提交（两个父提交：本地和远程）
                    parents = [local_commit.id, remote_commit.id]
                    repo.create_commit(
                        local_branch.name,
                        repo.default_signature,
                        repo.default_signature,
                        "Merge remote updates",
                        tree,
                        parents
                    )
                    # 清理合并状态
                    repo.state_cleanup()
                    print("已合并更新并生成提交")
            except Exception as e:
                print(f"合并失败：{str(e)}")
        else:
            print("合并类型不支持")
