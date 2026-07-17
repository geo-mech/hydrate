"""
批量测试所有 demo：以无头模式多进程并行运行每个 demo（超时 30 秒），显示测试报告。

用法：
    python test_all_demos.py              # 测试所有 demo（并行，默认 CPU 核心数）
    python test_all_demos.py --jobs 8     # 使用 8 个线程并行
    python test_all_demos.py --timeout 30 # 每个 demo 超时 30 秒
    python test_all_demos.py --verbose    # 显示每个 demo 的运行输出
"""

import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 确保项目根目录在 Python 搜索路径中
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


def get_project_root():
    """项目根目录（pyproject.toml 所在）"""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def find_demos():
    """查找所有 demo 文件，排除自身"""
    from zmlx.demo import list_demo_files

    return [
        f for f, _ in list_demo_files() if os.path.basename(f) != "test_all_demos.py"
    ]


def run_one(path, rel, timeout, index, test_dir):
    """运行单个 demo，返回 (index, rel, code, elapsed, stdout, stderr)"""
    from zmlx.io import opath

    project_root = get_project_root()

    # 为每个 demo 设置独立的图片输出目录（通过环境变量传给子进程）
    demo_name = os.path.splitext(rel)[0].replace("\\", "/")
    plt_path = opath(test_dir, demo_name)

    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, path, "--no-gui"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env={
                **os.environ,
                "PYTHONPATH": project_root,
                "ZMLX_PLT_SAVE_PATH": plt_path,
            },
        )
        elapsed = time.time() - start
        return index, rel, result.returncode, elapsed, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return index, rel, -1, elapsed, "", ""
    except Exception as e:
        elapsed = time.time() - start
        return index, rel, -2, elapsed, "", str(e)


def main():
    import datetime

    verbose = "--verbose" in sys.argv
    timeout = 60
    jobs = os.cpu_count() or 4
    for i, arg in enumerate(sys.argv):
        if arg == "--jobs" and i + 1 < len(sys.argv):
            jobs = int(sys.argv[i + 1])
        if arg == "--timeout" and i + 1 < len(sys.argv):
            timeout = int(sys.argv[i + 1])

    # 每次测试使用独立的输出目录
    time_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    test_dir = f"test_output_{time_str}"

    demos = find_demos()
    total = len(demos)
    from zmlx.io import opath

    # 创建输出目录并打开
    output_root = opath(test_dir)
    os.makedirs(output_root, exist_ok=True)
    os.startfile(output_root)

    print(f"找到 {total} 个 demo，{jobs} 线程并行，每个超时 {timeout} 秒")
    print(f"输出目录: {output_root}")
    print("=" * 60)

    log_lines = [
        f"批量测试 demo，共 {total} 个，{jobs} 线程并行，超时 {timeout} 秒",
        "=" * 60,
    ]

    # 准备任务：[(path, rel, index)]
    tasks = []
    for i, path in enumerate(demos):
        rel = os.path.relpath(path, os.path.dirname(os.path.abspath(__file__)))
        tasks.append((path, rel, i))

    # 收集结果：按 index 存储
    results = {}

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {
            pool.submit(run_one, path, rel, timeout, i, test_dir): i
            for path, rel, i in tasks
        }
        for future in as_completed(futures):
            index, rel, code, elapsed, stdout, stderr = future.result()
            results[index] = (rel, code, elapsed, stdout, stderr)

            # 实时输出
            done = len(results)
            if code == 0:
                print(f"[{done}/{total}] {rel} OK ({elapsed:.1f}s)")
            elif code == -1:
                print(f"[{done}/{total}] {rel} TIMEOUT ({elapsed:.1f}s)")
            else:
                print(f"[{done}/{total}] {rel} FAIL ({elapsed:.1f}s)")

            if verbose and stdout:
                for line in stdout.strip().split("\n")[-2:]:
                    print(f"    | {line}")

    # 按原始顺序整理结果并生成日志
    passed, failed, timeout_list, error_list = [], [], [], []
    for i in range(total):
        rel, code, elapsed, stdout, stderr = results[i]
        log_lines.append(f"\n[{i + 1}/{total}] {rel} ({elapsed:.1f}s)")
        if stdout:
            log_lines.append(f"  stdout: {stdout.strip()[:2000]}")
        if stderr:
            log_lines.append(f"  stderr: {stderr.strip()[:2000]}")

        if code == 0:
            log_lines.append(f"  result: OK")
            passed.append((rel, elapsed))
        elif code == -1:
            log_lines.append(f"  result: TIMEOUT")
            timeout_list.append((rel, elapsed))
        elif code == -2:
            log_lines.append(f"  result: ERROR - {stderr.strip()[:200]}")
            error_list.append((rel, stderr))
        else:
            log_lines.append(f"  result: FAIL (exit={code})")
            failed.append((rel, code, stderr.strip()))

    # 报告
    print()
    print("=" * 60)
    print(f"测试报告: 共 {total} 个 demo")
    print(f"  通过:   {len(passed)}")
    print(f"  超时:   {len(timeout_list)}")
    print(f"  失败:   {len(failed)}")
    print(f"  错误:   {len(error_list)}")

    if timeout_list:
        print()
        print("--- 超时的 demo（计算量大，非错误）---")
        for rel, elapsed in timeout_list:
            print(f"  {rel} ({elapsed:.1f}s)")

    if failed:
        print()
        print("--- 失败的 demo ---")
        for rel, code, stderr in failed:
            msg = stderr[:200] if stderr else f"exit code={code}"
            print(f"  {rel}: {msg}")

    if error_list:
        print()
        print("--- 运行出错的 demo ---")
        for rel, err in error_list:
            print(f"  {rel}: {err[:200]}")

    # 写入日志文件
    log_path = opath(test_dir, "test_report.log")
    log_lines.append(
        f"\n通过:{len(passed)} 超时:{len(timeout_list)} 失败:{len(failed)} 错误:{len(error_list)}"
    )
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    print(f"\n日志已保存到: {log_path}")


if __name__ == "__main__":
    main()
