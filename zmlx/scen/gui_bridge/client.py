"""界面桥 — **客户端**（stdlib ``urllib``，供测试控件与外部脚本使用）.

设计上它要能在**任何** Python 进程里跑（不需要 Qt、不需要 ``zmlx`` 的 GUI 部分），
所以只依赖标准库 —— 外部脚本可以直接 ``python -c "from ... import BridgeClient"``
或者干脆照抄 ``call()`` 那 20 行用 ``curl``。

用法::

    from zmlx.scen.gui_bridge.client import BridgeClient, discover
    target = discover()[0]                       # 扫临时目录里其它实例
    client = BridgeClient(target['port'], target['token'])
    print(client.call('ping'))
    client.show('show_env_edit')                 # 让**那个进程**切到环境变量页

Created by DeepSeek, 2026-10-30: 第一版
"""

import base64
import json
import urllib.error
import urllib.request

from zmlx.scen.gui_bridge import discovery


class BridgeError(Exception):
    """一次调用失败（网络 / 鉴权 / 对端返回的 ``error`` 对象）."""

    def __init__(self, message, code=None, hint=None):
        super(BridgeError, self).__init__(message)
        self.message = str(message)
        self.code = code
        self.hint = hint


class BridgeClient:
    """连到**另一个**进程的桥服务.

    Attributes:
        port: 目标端口。
        host: 默认 ``127.0.0.1``（本设计不做远程）。
    """

    def __init__(self, port, token='', host='127.0.0.1', timeout=5.0):
        self.host = str(host)
        self.port = int(port)
        self.token = str(token)
        self.timeout = float(timeout)
        self._seq = 0

    @classmethod
    def from_handle(cls, handle, **kwargs):
        """从句柄 dict（:func:`discovery.list_handles` 的一项）建客户端."""
        return cls(handle['port'], handle.get('token', ''), **kwargs)

    @property
    def url(self):
        """``host:port``，给界面显示用."""
        return '{0}:{1}'.format(self.host, self.port)

    # -- 底层 ---------------------------------------------------------------

    def health(self):
        """探活（**不需要 token**）."""
        return self._request('GET', '/health', None, with_token=False)

    def call(self, method, params=None):
        """调一个方法，返回 ``result``.

        Args:
            method: 方法名。
            params: 参数字典。

        Returns:
            dict: 对端的 ``result``。

        Raises:
            BridgeError: 网络不通 / token 不对 / 对端返回 error。
        """
        self._seq += 1
        payload = {'jsonrpc': '2.0', 'id': self._seq,
                   'method': method, 'params': params or {}}
        response = self._request('POST', '/rpc', payload)
        if not isinstance(response, dict):
            raise BridgeError('对端返回的不是 JSON 对象', code=None)
        error = response.get('error')
        if error:
            raise BridgeError(
                error.get('message') or '未知错误',
                code=error.get('code'),
                hint=(error.get('data') or {}).get('hint'))
        return response.get('result')

    def _request(self, verb, path, payload, with_token=True):
        url = 'http://{0}:{1}{2}'.format(self.host, self.port, path)
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        if with_token and self.token:
            headers['X-ZML-Bridge-Token'] = self.token
        request = urllib.request.Request(url, data=data, headers=headers, method=verb)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read()
        except urllib.error.HTTPError as err:
            body = err.read()
            try:
                parsed = json.loads(body.decode('utf-8', 'replace'))
            except ValueError:
                raise BridgeError('HTTP {0}: {1}'.format(err.code, body[:200]))
            error = parsed.get('error') or {}
            raise BridgeError(error.get('message') or 'HTTP {0}'.format(err.code),
                              code=error.get('code'),
                              hint=(error.get('data') or {}).get('hint'))
        except urllib.error.URLError as err:
            raise BridgeError('连不上 {0}（{1}）'.format(self.url, err.reason))
        except OSError as err:
            raise BridgeError('连不上 {0}（{1}）'.format(self.url, err))
        try:
            return json.loads(body.decode('utf-8', 'replace'))
        except ValueError:
            raise BridgeError('对端返回的不是合法 JSON')

    # -- 便捷方法 -----------------------------------------------------------

    def ping(self):
        """连通性检查."""
        return self.call('ping')

    def info(self):
        """窗口状态快照."""
        return self.call('info')

    def commands(self):
        """对端允许调用的命令名列表."""
        return self.call('commands').get('names') or []

    def tabs(self):
        """对端的标签页列表."""
        return self.call('tabs')

    def show(self, name):
        """让对端打开 / 切到某个页面（``name`` 是 gui 命令名）."""
        return self.call('show', {'name': name})

    def screenshot(self, target='window', max_width=1440):
        """截图.

        Returns:
            tuple: ``(png_bytes, width, height)``。
        """
        result = self.call('screenshot', {'target': target, 'max_width': max_width})
        data = base64.b64decode(result.get('png_b64') or '')
        return data, int(result.get('width') or 0), int(result.get('height') or 0)


def discover(exclude_self=True):
    """扫临时目录，列出其它正在运行的实例.

    Returns:
        list[dict]: 每项含 ``pid`` / ``port`` / ``token`` / ``version`` / ``cwd``。
    """
    return discovery.list_handles(clean=True, exclude_self=exclude_self)
