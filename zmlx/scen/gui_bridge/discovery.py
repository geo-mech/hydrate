"""界面桥 — **发现层**（句柄文件的写入 / 扫描 / 残留清理）.

外部进程怎么知道"那个界面在哪"? 靠一份写在临时目录里的小 json::

    <临时目录>/zml_gui_bridge/<pid>.json
    {"pid": 12345, "port": 51234, "token": "9f3a...", "app": "IGG-Hydrate",
     "version": "1.9.42", "cwd": "...", "started": 1793412345}

⚠️ **token 就写在里面**。这不是疏忽：威胁模型是「同一用户的进程之间互相可信」，
token 挡的是**别的用户**和**网页里的 JS**，挡不住你自己用户下的脚本（``ReadMe.md`` §9）。
所以这里的实现不要试图加密，加密也挡不住同用户读取。

⚠️ **残留清理必须做**：进程被强杀时 json 留了下来，下次启动若不清理，界面上会出现
一个永远连不上的"幽灵实例"。判据是 pid 是否存活 + 端口是否还能 ``/health``。

Created by DeepSeek, 2026-10-30: 第一版
"""

import json
import os
import sys
import tempfile
import time


def handle_dir():
    """句柄目录（不存在时按需创建）.

    Returns:
        str: 目录的绝对路径。
    """
    path = os.path.join(tempfile.gettempdir(), 'zml_gui_bridge')
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        pass
    return path


def handle_path(pid=None):
    """某个进程的句柄文件路径."""
    return os.path.join(handle_dir(), '{0}.json'.format(os.getpid() if pid is None else pid))


def _pid_alive(pid):
    """这个 pid 现在还有进程吗.

    ⚠️ Windows 上**不能**用 ``os.kill(pid, 0)`` —— 它会真的发信号（甚至终止进程）。
    用 ``OpenProcess`` 探测即可。
    """
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if sys.platform == 'win32':
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if not handle:
                return False
            kernel32.CloseHandle(handle)
            return True
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def write_handle(port, token, app='IGG-Hydrate', version=''):
    """写出本进程的句柄文件.

    Args:
        port: 实际监听的端口（``0`` 由系统分配后取到的那个）。
        token: 本次启动生成的鉴权令牌。
        app: 应用名（给发现方看的）。
        version: 版本号（给发现方看的）。

    Returns:
        str: 写出的文件路径。
    """
    data = {
        'pid': os.getpid(),
        'port': int(port),
        'token': str(token),
        'app': str(app),
        'version': str(version),
        'cwd': os.getcwd(),
        'started': int(time.time()),
    }
    path = handle_path()
    with open(path, 'w', encoding='utf-8') as fp:
        json.dump(data, fp, ensure_ascii=False)
    return path


def remove_handle():
    """删掉本进程的句柄文件（退出/停止服务时调用，失败不抛）."""
    try:
        os.remove(handle_path())
    except OSError:
        pass


def list_handles(clean=True, exclude_self=True):
    """列出**其它**运行中的实例.

    Args:
        clean: 是否顺手删掉 pid 已死的句柄文件。
        exclude_self: 是否排除本进程（测"两个界面互连"时，自己不该出现在目标列表里）。

    Returns:
        list[dict]: 每项是句柄内容，另带 ``path`` 字段。
    """
    folder = handle_dir()
    self_pid = os.getpid()
    results = []
    try:
        names = os.listdir(folder)
    except OSError:
        return results

    for name in names:
        if not name.endswith('.json'):
            continue
        path = os.path.join(folder, name)
        try:
            with open(path, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
        except (OSError, ValueError):
            if clean:
                _quiet_remove(path)
            continue
        if not isinstance(data, dict) or not data.get('port'):
            if clean:
                _quiet_remove(path)
            continue
        pid = data.get('pid')
        if not _pid_alive(pid):
            if clean:
                _quiet_remove(path)
            continue
        if exclude_self and pid == self_pid:
            continue
        data['path'] = path
        results.append(data)

    results.sort(key=lambda item: item.get('started') or 0)
    return results


def _quiet_remove(path):
    try:
        os.remove(path)
    except OSError:
        pass
