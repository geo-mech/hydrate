"""通过 git 安全更新代码（fast-forward only）。

优先使用 git CLI；不可用时自动安装 pygit2 作为后备。
"""
import os
import subprocess
import sys


# ============================================================
# Git CLI 后端
# ============================================================

def _git(args, timeout=30):
    """执行 git 命令，返回 (returncode, stdout, stderr)。"""
    try:
        r = subprocess.run(
            ['git'] + args,
            capture_output=True, text=True, timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return -1, '', 'Git 未安装'
    except subprocess.TimeoutExpired:
        return -2, '', 'Git 命令超时'
    except Exception as e:
        return -3, '', str(e)


def _cli_available():
    code, _, _ = _git(['--version'], timeout=5)
    return code == 0


# ============================================================
# pygit2 后端（Git CLI 不可用时的后备）
# ============================================================

def _ensure_pygit2():
    """确保 pygit2 可用，不可用时尝试 pip install。"""
    try:
        import pygit2  # noqa: F401
        return True, 'pygit2 已就绪'
    except ImportError:
        pass

    # 尝试安装
    try:
        r = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'pygit2', '--quiet'],
            capture_output=True, text=True, timeout=120,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
        )
        if r.returncode != 0:
            return False, f'pygit2 安装失败: {r.stderr[-200:]}'
        import pygit2  # noqa: F401
        return True, 'pygit2 安装成功'
    except Exception as e:
        return False, f'pygit2 安装异常: {e}'


def _pygit2_repo():
    """打开当前目录的 pygit2 仓库。"""
    import pygit2
    try:
        path = pygit2.discover_repository(os.getcwd())
        return pygit2.Repository(path), ''
    except Exception as e:
        return None, f'当前目录不是 git 仓库: {e}'


def _pygit2_clean(repo):
    """pygit2 版本：检查工作区是否干净。"""
    status = repo.status()
    for filepath, flags in status.items():
        if flags != pygit2.GIT_STATUS_CURRENT:
            return False, f'有未提交的修改: {filepath}'
    return True, '工作区干净'

    import pygit2  # for reference in status check above


def _pygit2_fetch(repo, remote='origin'):
    """pygit2 版本：fetch。"""
    try:
        r = repo.remotes[remote]
        r.fetch()
        return True, 'fetch 完成'
    except KeyError:
        return False, f'远程仓库 "{remote}" 不存在'
    except Exception as e:
        return False, f'fetch 失败: {e}'


def _pygit2_compare(repo, remote='origin', branch='master'):
    """pygit2 版本：比较本地/远程 HEAD。"""
    try:
        local = repo.head.target
        remote_ref = f'refs/remotes/{remote}/{branch}'
        remote_commit = repo.revparse_single(remote_ref)
        remote_oid = remote_commit.id

        ahead = 0
        behind = 0
        if local != remote_oid:
            # 用 rev-list 等效逻辑
            local_commit = repo.get(local)
            merge_base = repo.merge_base(local, remote_oid)
            if merge_base != local:
                behind = 1  # 远程有新提交
            if merge_base != remote_oid:
                ahead = 1  # 本地有新提交
        return behind, ahead, ''
    except KeyError:
        return 0, 0, f'远程分支 "{remote}/{branch}" 不存在（请先 fetch）'
    except Exception as e:
        return 0, 0, f'版本比较失败: {e}'


def _pygit2_merge_ff(repo, remote='origin', branch='master'):
    """pygit2 版本：仅快进合并。"""
    try:
        remote_ref = f'refs/remotes/{remote}/{branch}'
        remote_commit = repo.revparse_single(remote_ref)
        remote_oid = remote_commit.id
        local_oid = repo.head.target

        # 检查是否可快进
        merge_base = repo.merge_base(local_oid, remote_oid)
        if merge_base != local_oid:
            return False, '无法快进合并 (本地有未推送的提交或历史分叉)'

        if merge_base == remote_oid:
            return True, '已是最新版本'

        # 快进
        local_branch = repo.lookup_branch(branch)
        local_branch.set_target(remote_oid)
        repo.checkout_tree(repo.get(remote_oid))
        repo.head.set_target(remote_oid)
        return True, '更新完成'
    except Exception as e:
        return False, f'合并失败: {e}'


# ============================================================
# 统一入口
# ============================================================

def update_by_git(remote='origin', branch='master', cwd=None):
    """通过 git 安全更新代码（优先 CLI，后备 pygit2）。

    安全检查链（一项不通过即阻止更新）：
    1. Git CLI 或 pygit2 可用
    2. 当前目录是 git 仓库
    3. 工作区干净（无未提交修改）
    4. 远程仓库可达
    5. 仅快进合并（--ff-only，保证线性历史）

    Args:
        remote: 远程仓库名，默认 'origin'
        branch: 分支名，默认 'master'
        cwd: 工作目录（git 仓库根目录），默认 os.getcwd()

    Returns:
        (ok: bool, msg: str)
    """
    prev_cwd = os.getcwd()
    try:
        if cwd is not None:
            os.chdir(cwd)
        return _update(remote, branch)
    finally:
        os.chdir(prev_cwd)


def _update(remote, branch):
    """实际更新逻辑（在正确的 cwd 下执行）。"""
    use_cli = _cli_available()

    if use_cli:
        # === Git CLI 路径 ===
        code, _, err = _git(['rev-parse', '--git-dir'], timeout=5)
        if code != 0:
            return False, '当前目录不是 git 仓库'

        code, _, err = _git(['diff', '--quiet'], timeout=10)
        if code != 0:
            return False, '工作区有未暂存的修改，请先 git add 或 git stash'

        code, _, err = _git(['diff', '--cached', '--quiet'], timeout=10)
        if code != 0:
            return False, '暂存区有未提交的修改，请先 git commit'

        code, _, err = _git(['ls-remote', remote], timeout=15)
        if code != 0:
            return False, f'无法连接远程仓库 "{remote}": {err}'

        code, _, err = _git(['fetch', remote], timeout=60)
        if code != 0:
            return False, f'fetch 失败: {err}'

        code, out, err = _git(
            ['rev-list', '--left-right', '--count', f'HEAD...{remote}/{branch}'],
            timeout=10)
        if code != 0:
            return False, f'无法比较版本: {err}'
        parts = out.split()
        if len(parts) != 2:
            return False, f'无法解析版本差异: {out}'
        ahead = int(parts[0])
        behind = int(parts[1])

        if behind == 0:
            local_info = f' (本地领先 {ahead} 个提交)' if ahead > 0 else ''
            return True, f'已是最新版本{local_info}'

        code, out, err = _git(['merge', '--ff-only', f'{remote}/{branch}'], timeout=30)
        if code == 0:
            return True, f'更新完成 ({behind} 个提交)'
        return False, f'无法快进合并 (本地有未推送的提交或历史分叉):\n{err}'

    else:
        # === pygit2 路径 ===
        ok, msg = _ensure_pygit2()
        if not ok:
            return False, f'Git 不可用，且 {msg}。请手动安装 Git 或 pygit2'

        repo, msg = _pygit2_repo()
        if repo is None:
            return False, msg

        ok, msg = _pygit2_clean(repo)
        if not ok:
            return False, msg

        ok, msg = _pygit2_fetch(repo, remote)
        if not ok:
            return False, msg

        behind, ahead, msg = _pygit2_compare(repo, remote, branch)
        if msg:
            return False, msg
        if behind == 0:
            local_info = f' (本地领先 {ahead} 个提交)' if ahead > 0 else ''
            return True, f'已是最新版本{local_info}'

        ok, msg = _pygit2_merge_ff(repo, remote, branch)
        if ok:
            return True, msg
        return False, msg


if __name__ == '__main__':
    print('=== 测试 git 更新 ===\n')

    use_cli = _cli_available()
    print(f'后端: {"Git CLI" if use_cli else "pygit2"}')

    if not use_cli:
        ok, msg = _ensure_pygit2()
        print(f'pygit2: {"OK" if ok else "FAIL"} — {msg}')
        if not ok:
            sys.exit(1)

    # 运行完整检查（不实际更新）
    ok, msg = update_by_git()
    print(f'\nupdate_by_git(): {"OK" if ok else "FAIL"}')
    print(msg)
    print('\n=== 测试完成 ===')
