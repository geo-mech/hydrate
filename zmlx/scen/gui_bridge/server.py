"""界面桥 — **传输层**（stdlib HTTP 服务，不开第三方依赖）.

⚠️ 本模块**不 import Qt**：它只做「收 HTTP → 校验 → 调 ``gui.command`` → 回 JSON」。
Qt 相关的部分全在 :mod:`methods`，而那边的函数**只在 GUI 线程执行**。

三条硬约束（``ReadMe.md`` §4.1 / §6）：

1. 只注册**一个** gui 命令（``bridge_call``）—— 单一入口才好对学生白名单校验、审计和
   收敛参数校验；铺开 N 个命令等于在命令表里开 N 个面。
   ⚠️ **与「通道池」无关**：``GuiApi`` 的 20 通道池已于 v1.9.9 删除（改为每调用新建
   一个通道、无并发上限、不再丢弃），所以「省通道」不再是这里的理由。
2. 服务端用**一把串行锁**：同一时刻只放一个请求进去，吞吐不是指标，可预测才是。
3. 等锁超过 ``LOCK_TIMEOUT`` 就回 ``BUSY`` —— 让调用方能区分「对方忙」和「对方死了」。

Created by DeepSeek, 2026-10-30: 第一版
"""

import collections
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from zmlx.scen.gui_bridge import discovery, protocol


#: 命令名：**整个功能唯一的 gui 入口**（单一面便于白名单校验与审计，不污染命令表）
COMMAND_NAME = 'bridge_call'

#: 等串行锁的上限（秒）
LOCK_TIMEOUT = 5.0

#: 请求体上限：超过就拒绝，防止一次塞爆内存
MAX_BODY = 1 << 20  # 1 MiB


class BridgeServer:
    """一个进程内的桥服务（同一进程**只应该有一个**实例）.

    Attributes:
        port: 实际监听端口（``0`` 表示没启动）。
    """

    def __init__(self):
        self._httpd = None
        self._thread = None
        self._token = ''
        self._port = 0
        self._lock = threading.Lock()
        self._log = collections.deque(maxlen=200)
        self._requests = 0
        self._started = 0.0

    # -- 状态 ---------------------------------------------------------------

    @property
    def running(self):
        """服务是否在跑."""
        return self._httpd is not None

    @property
    def port(self):
        """监听端口（未启动为 0）."""
        return self._port

    @property
    def token(self):
        """本次启动的鉴权令牌（未启动为空串）."""
        return self._token

    @property
    def requests(self):
        """累计处理过的请求数."""
        return self._requests

    def log_items(self, tail=20):
        """最近的访问日志（给测试面板看）."""
        items = list(self._log)
        return items[-int(tail):] if tail else items

    # -- 生命周期 -----------------------------------------------------------

    def start(self):
        """启动服务并写出句柄文件.

        Returns:
            int: 实际端口。

        Raises:
            OSError: 端口绑不上（几乎不会发生，因为用 ``0`` 让系统分配）。
        """
        if self.running:
            return self._port

        from zmlx import __version__

        self._token = secrets.token_hex(16)
        httpd = ThreadingHTTPServer(('127.0.0.1', 0), _Handler)
        httpd.daemon_threads = True
        httpd.bridge = self
        self._port = int(httpd.server_address[1])
        self._httpd = httpd
        self._started = time.time()
        self._thread = threading.Thread(
            target=httpd.serve_forever, kwargs={'poll_interval': 0.2},
            name='zml-gui-bridge', daemon=True)
        self._thread.start()
        discovery.write_handle(self._port, self._token, version=str(__version__))
        self._note('start', '端口 {0}'.format(self._port), ok=True)
        return self._port

    def stop(self):
        """停止服务并删除句柄文件（失败不抛 —— 退出路径上不能有异常）."""
        httpd, self._httpd = self._httpd, None
        self._port = 0
        if httpd is not None:
            try:
                httpd.shutdown()
            except Exception:
                pass
            try:
                httpd.server_close()
            except Exception:
                pass
        discovery.remove_handle()
        self._note('stop', '服务已停止', ok=True)

    # -- 调用 ---------------------------------------------------------------

    def call(self, method, params=None):
        """执行一个方法（**任意线程**调用；内部投递到 GUI 线程）.

        Args:
            method: 方法名。
            params: 参数字典。

        Returns:
            dict: 方法的 ``result``。

        Raises:
            protocol.ProtocolError: 忙 / 无界面 / 内部错误。
        """
        if not self._lock.acquire(timeout=LOCK_TIMEOUT):
            raise protocol.ProtocolError(
                protocol.BUSY,
                '上一个请求还没返回（GUI 线程可能正被长任务占用）',
                hint='稍后重试；若持续如此，说明界面被某个计算卡住了')

        started = time.time()
        failed = False
        try:
            from zmlx.ui import gui

            if not gui.exists():
                raise protocol.ProtocolError(
                    protocol.FAILED, '界面已关闭，通道不可用')

            try:
                result = gui.command(COMMAND_NAME, method, params or {})
            except protocol.ProtocolError:
                raise
            except Exception as err:  # noqa: BLE001 - 内部错误也要变成合法响应
                raise protocol.ProtocolError(
                    protocol.INTERNAL_ERROR,
                    '{0}: {1}'.format(type(err).__name__, err))

            if result is None:
                # ⚠️ 这里**不是**「通道满」：``GuiApi`` 的通道池已于 v1.9.9 删除，
                #    ``gui.command`` 不会再因为并发而上限丢弃（除非命令自己返回 None）。
                #    ``methods.dispatch`` 恒返回 dict 或抛异常，所以走到这里说明
                #    ``bridge_call`` 被别的插件覆盖了，或者是 headless（上面已挡）。
                raise protocol.ProtocolError(
                    protocol.INTERNAL_ERROR,
                    '命令 {0!r} 返回了 None（正常应返回 dict）'.format(COMMAND_NAME),
                    hint='多半是 bridge_call 被别的插件覆盖了；重启界面即可恢复')
            return result
        except Exception:
            failed = True
            raise
        finally:
            cost = (time.time() - started) * 1000.0
            self._requests += 1
            self._note(method, '{0:.1f} ms'.format(cost), ok=not failed)
            self._lock.release()

    def _note(self, method, detail, ok=True):
        """记一条访问日志（测试面板要能看到"谁在什么时候调了什么"）."""
        self._log.append({
            'time': time.strftime('%H:%M:%S'),
            'method': str(method),
            'detail': str(detail),
            'ok': bool(ok),
        })


class _Handler(BaseHTTPRequestHandler):
    """唯一的 HTTP 入口：``GET /health`` 与 ``POST /rpc``."""

    server_version = 'ZmlGuiBridge/1.0'
    protocol_version = 'HTTP/1.1'

    # 静音：默认实现会把每条请求打到 stderr，在 GUI 程序里就是控制台刷屏
    def log_message(self, fmt, *args):
        pass

    # -- 路由 ---------------------------------------------------------------

    def do_GET(self):
        path = self.path.split('?')[0].rstrip('/') or '/'
        if path in ('/health', '/'):
            # ⚠️ /health **不校验 token**：发现方在拿到句柄之前就要能探活
            self._send(200, {'ok': True, 'app': 'IGG-Hydrate',
                             'pid': _pid(), 'port': self.server.bridge.port})
            return
        self._send(404, {'ok': False, 'message': '只支持 GET /health 与 POST /rpc'})

    def do_POST(self):
        bridge = self.server.bridge
        path = self.path.split('?')[0].rstrip('/') or '/'
        if path != '/rpc':
            self._send(404, {'ok': False, 'message': '未知路径 {0!r}'.format(path)})
            return

        token = self.headers.get('X-ZML-Bridge-Token') or ''
        if not _same(token, bridge.token):
            self._send(401, protocol.failure(
                None, protocol.ProtocolError(
                    protocol.UNAUTHORIZED, 'token 不对',
                    hint='从 <临时目录>/zml_gui_bridge/<pid>.json 里取 token')))
            bridge._note('(拒绝)', 'token 错误', ok=False)
            return

        try:
            length = int(self.headers.get('Content-Length') or 0)
        except ValueError:
            length = 0
        if length <= 0:
            self._send(400, protocol.failure(
                None, protocol.ProtocolError(protocol.INVALID_REQUEST, '请求体为空')))
            return
        if length > MAX_BODY:
            self._send(413, protocol.failure(
                None, protocol.ProtocolError(protocol.INVALID_REQUEST,
                                             '请求体过大（上限 1 MiB）')))
            return

        raw = self.rfile.read(length)
        request_id = None
        try:
            payload = protocol.loads(raw.decode('utf-8', 'replace'))
            request_id, method, params = protocol.normalize_request(payload)
            result = bridge.call(method, params)
        except protocol.ProtocolError as err:
            self._send(_status_of(err), protocol.failure(request_id, err))
            return
        except Exception as err:  # noqa: BLE001 - 兜底，绝不让服务线程抛出去
            self._send(500, protocol.failure(
                request_id, protocol.ProtocolError(
                    protocol.INTERNAL_ERROR, '{0}: {1}'.format(type(err).__name__, err))))
            return

        self._send(200, protocol.success(request_id, result))

    # -- 输出 ---------------------------------------------------------------

    def _send(self, status, obj):
        body = protocol.dumps(obj).encode('utf-8')
        # ⚠️ **非 200 一律关连接**：这些分支（401 / 413 / 400 / 404 / 500）都没有消费
        #    请求体 —— ``do_POST`` 在 token 校验、长度校验、JSON 解析失败时就直接回包了。
        #    而 HTTP/1.1 默认 keep-alive，残留的请求体会被当成**下一个请求**的请求行，
        #    于是同一连接上后续请求全部得到 ``400 Bad Request``（2026-10-30 实测复现：
        #    先发错 token 再发正确请求 → 第二次拿到基类的 HTML 400 页）。
        #    要么读完 body、要么关连接；这里选关 —— 出错后重连，比让客户端拿到错乱响应
        #    清楚得多。正常 200 仍然复用连接（``BridgeClient`` 走 urllib，每次新建连接，
        #    但它不是唯一可能的客户端：``requests.Session`` / 手写 ``http.client`` 会复用）。
        if status != 200:
            self.close_connection = True
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            if status != 200:
                self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass  # 客户端提前断开：不是错误


def _status_of(err):
    """把协议错误码映射成 HTTP 状态码（客户端主要看 body，这里只是别全都 200）."""
    return {
        protocol.PARSE_ERROR: 400,
        protocol.INVALID_REQUEST: 400,
        protocol.INVALID_PARAMS: 400,
        protocol.METHOD_NOT_FOUND: 404,
        protocol.UNAUTHORIZED: 401,
        protocol.BUSY: 503,
    }.get(err.code, 500)


def _same(a, b):
    """常数时间比较（避免 token 被按字节猜）."""
    if not a or not b:
        return False
    try:
        return secrets.compare_digest(str(a), str(b))
    except Exception:
        return False


def _pid():
    import os

    return os.getpid()
